from __future__ import annotations

import dataclasses
import os
import re
import tempfile
from pathlib import Path
from typing import Iterable

from .config import ConfigBlock, ConfigStyle, parse_config, render_config
from .errors import ExecutionFailed, MdDemoError
from .runners import BlockResult, DisplayMode, make_runner

RESULT_START_PREFIX = "<!-- md-demo: result start"
RESULT_START = "<!-- md-demo: result start. Do not edit; this block is overwritten. -->"
RESULT_END_PREFIX = "<!-- md-demo: result end"
RESULT_END = "<!-- md-demo: result end -->"
RUNTIME_ALIASES = {
    "python": "python",
    "python3": "python",
    "bash": "bash",
    "shell": "bash",
}
LANGUAGE_ALIASES = {
    "python": {"python", "python3"},
    "bash": {"bash", "shell"},
}


@dataclasses.dataclass(frozen=True)
class CodeBlock:
    start: int
    end: int
    language: str
    attrs: tuple[str, ...]
    code: str
    line: int


@dataclasses.dataclass(frozen=True)
class ResultBlock:
    start: int
    end: int
    line: int


@dataclasses.dataclass(frozen=True)
class ParsedDocument:
    lines: list[str]
    newline: str
    runtime: str
    display: DisplayMode
    preface_text: str
    body_start: int
    config_block: ConfigBlock
    code_blocks: list[CodeBlock]
    result_blocks: list[ResultBlock]


@dataclasses.dataclass(frozen=True)
class ProcessResult:
    text: str
    warnings: list[str]


FENCE_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<fence>`{3,}|~{3,})(?P<info>.*?)[ \t]*\r?\n?$")


def process_file(
    path: Path,
    *,
    clear: bool = False,
    config_style: ConfigStyle = "preserve",
) -> ProcessResult:
    raw = path.read_text()
    return process_text(raw, path=path, clear=clear, config_style=config_style)


def write_output(path: Path, text: str, output: str | None) -> None:
    if output == "-":
        print(text, end="")
        return
    if output:
        Path(output).write_text(text)
        return
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(text)
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def process_text(
    raw: str,
    *,
    path: Path,
    clear: bool = False,
    config_style: ConfigStyle = "preserve",
) -> ProcessResult:
    parsed = parse_document(raw)
    warnings = warn_for_mismatched_exe(parsed)
    attached = find_attached_results(parsed)
    result_indices = set(range(len(parsed.result_blocks)))
    stray = sorted(result_indices - set(attached.values()))
    if stray:
        block = parsed.result_blocks[stray[0]]
        raise MdDemoError(
            f"stray md-demo result block at line {block.line}; result blocks must appear immediately after the executable block that produced them"
        )

    runner = None if clear else make_runner(parsed.runtime, path.parent, parsed.display)
    try:
        return _rewrite(
            parsed,
            attached=attached,
            runner=runner,
            clear=clear,
            warnings=warnings,
            config_style=config_style,
        )
    finally:
        if runner is not None:
            runner.close()


def parse_document(raw: str) -> ParsedDocument:
    newline = detect_newline(raw)
    lines = raw.splitlines(keepends=True)
    config_block = parse_config(lines)
    config = config_block.config
    runtime_value = config.get("runtime")
    if not isinstance(runtime_value, str):
        raise MdDemoError("missing md-demo.runtime")
    runtime = RUNTIME_ALIASES.get(runtime_value)
    if runtime is None:
        raise MdDemoError(f"unsupported md-demo.runtime: {runtime_value}")
    display_value = config.get("display", "last-expression")
    if display_value in {"last-expression", "none"}:
        display = display_value
    else:
        raise MdDemoError("md-demo.display must be 'last-expression' or 'none' when provided")
    preface_value = config.get("preface-text", "")
    if preface_value is None:
        preface_text = ""
    elif isinstance(preface_value, str):
        preface_text = preface_value
    else:
        raise MdDemoError("md-demo.preface-text must be a string when provided")

    code_blocks, result_blocks = scan_blocks(lines, config_block.body_start)
    return ParsedDocument(
        lines,
        newline,
        runtime,
        display,
        preface_text,
        config_block.body_start,
        config_block,
        code_blocks,
        result_blocks,
    )


def detect_newline(raw: str) -> str:
    crlf = raw.find("\r\n")
    lf = raw.find("\n")
    if crlf != -1 and crlf == lf - 1:
        return "\r\n"
    return "\n"


def scan_blocks(lines: list[str], start: int) -> tuple[list[CodeBlock], list[ResultBlock]]:
    code_blocks: list[CodeBlock] = []
    result_blocks: list[ResultBlock] = []
    index = start
    while index < len(lines):
        stripped = lines[index].strip()
        if stripped.startswith(RESULT_START_PREFIX):
            result_start = index
            index += 1
            while index < len(lines) and not lines[index].strip().startswith(RESULT_END_PREFIX):
                index += 1
            if index >= len(lines):
                raise MdDemoError(f"unterminated md-demo result block at line {result_start + 1}")
            result_blocks.append(ResultBlock(result_start, index + 1, result_start + 1))
            index += 1
            continue

        match = FENCE_RE.match(lines[index])
        if not match:
            index += 1
            continue
        fence = match.group("fence")
        fence_char = fence[0]
        fence_len = len(fence)
        info = match.group("info").strip()
        language, attrs = parse_info(info)
        code_start = index + 1
        close = code_start
        while close < len(lines):
            close_match = FENCE_RE.match(lines[close])
            if close_match:
                closing = close_match.group("fence")
                if closing[0] == fence_char and len(closing) >= fence_len:
                    break
            close += 1
        if close >= len(lines):
            raise MdDemoError(f"unterminated fenced code block at line {index + 1}")
        if language:
            code_blocks.append(
                CodeBlock(
                    index, close + 1, language, attrs, "".join(lines[code_start:close]), index + 1
                )
            )
        index = close + 1
    return code_blocks, result_blocks


def parse_info(info: str) -> tuple[str, tuple[str, ...]]:
    if not info:
        return "", ()
    parts = info.split()
    language = parts[0]
    attrs = tuple(part.strip("{}[]") for part in parts[1:])
    return language, attrs


def is_executable(block: CodeBlock, runtime: str) -> bool:
    return "exe" in block.attrs and block.language in LANGUAGE_ALIASES[runtime]


def has_exe_marker(block: CodeBlock) -> bool:
    return "exe" in block.attrs


def warn_for_mismatched_exe(parsed: ParsedDocument) -> list[str]:
    warnings: list[str] = []
    allowed = LANGUAGE_ALIASES[parsed.runtime]
    for block in parsed.code_blocks:
        if has_exe_marker(block) and block.language not in allowed:
            warnings.append(
                f"warning: {block.language} exe block at line {block.line} does not match document runtime"
            )
    return warnings


def find_attached_results(parsed: ParsedDocument) -> dict[int, int]:
    starts = {block.start: index for index, block in enumerate(parsed.result_blocks)}
    attached: dict[int, int] = {}
    for code_index, block in enumerate(parsed.code_blocks):
        if not is_executable(block, parsed.runtime):
            continue
        cursor = block.end
        while cursor < len(parsed.lines) and parsed.lines[cursor].strip() == "":
            cursor += 1
        result_index = starts.get(cursor)
        if result_index is not None:
            attached[code_index] = result_index
    return attached


def _rewrite(
    parsed: ParsedDocument,
    *,
    attached: dict[int, int],
    runner,
    clear: bool,
    warnings: list[str],
    config_style: ConfigStyle,
) -> ProcessResult:
    executable_by_start = {
        block.start: index
        for index, block in enumerate(parsed.code_blocks)
        if is_executable(block, parsed.runtime)
    }
    attached_result_starts = {
        parsed.result_blocks[result_index].start for result_index in attached.values()
    }
    out: list[str] = []
    index = 0
    failed = False
    while index < len(parsed.lines):
        if index == 0 and config_style != "preserve":
            out.extend(render_config(parsed.config_block, parsed.newline, config_style))
            index = parsed.body_start
            continue
        if index in attached_result_starts:
            block = _result_by_start(parsed.result_blocks, index)
            index = block.end
            continue
        code_index = executable_by_start.get(index)
        if code_index is None:
            out.append(parsed.lines[index])
            index += 1
            continue

        block = parsed.code_blocks[code_index]
        out.extend(parsed.lines[block.start : block.end])
        index = block.end
        while index < len(parsed.lines) and parsed.lines[index].strip() == "":
            out.append(parsed.lines[index])
            index += 1
        if index in attached_result_starts:
            result_block = _result_by_start(parsed.result_blocks, index)
            index = result_block.end
        if clear or failed:
            continue
        result = runner.run_block(block.code)
        out.extend(format_result(result, parsed.newline, parsed.preface_text))
        if not result.ok:
            failed = True
            continue
    text = "".join(out)
    if failed:
        raise ExecutionFailed("execution failed", text)
    return ProcessResult(text, warnings)


def _result_by_start(result_blocks: Iterable[ResultBlock], start: int) -> ResultBlock:
    for block in result_blocks:
        if block.start == start:
            return block
    raise AssertionError(f"missing result block starting at {start}")


def format_result(result: BlockResult, newline: str, preface_text: str = "") -> list[str]:
    output = result.output
    if not output:
        return []
    fence = result_fence(output)
    lines = [RESULT_START + newline]
    if preface_text:
        lines.extend([preface_text + newline, newline])
    lines.append(f"{fence}text{newline}")
    normalized = output.replace("\r\n", "\n").replace("\r", "\n")
    for line in normalized.splitlines(keepends=True):
        lines.append(line.replace("\n", newline))
    if not normalized.endswith("\n"):
        lines.append(newline)
    lines.extend([f"{fence}{newline}", RESULT_END + newline])
    return lines


def result_fence(output: str) -> str:
    max_run = 2
    for match in re.finditer(r"`+", output):
        max_run = max(max_run, len(match.group(0)))
    return "`" * max(3, max_run + 1)

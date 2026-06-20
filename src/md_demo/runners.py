from __future__ import annotations

import ast
import contextlib
import dataclasses
import io
import os
import pprint
import re
import subprocess
import sys
import tokenize
import traceback
import uuid
from pathlib import Path
from typing import Literal

ANSI_RE = re.compile(
    r"(?:\x1B\[[0-?]*[ -/]*[@-~]|\x1B\][^\x07]*(?:\x07|\x1B\\)|[\x00-\x08\x0B\x0C\x0E-\x1F\x7F])"
)
DisplayMode = Literal["last-expression", "none"]


@dataclasses.dataclass
class BlockResult:
    output: str
    ok: bool


def clean_output(text: str) -> str:
    return ANSI_RE.sub("", text)


class Runner:
    def run_block(self, code: str) -> BlockResult:
        raise NotImplementedError

    def close(self) -> None:
        pass


class PythonRunner(Runner):
    def __init__(self, cwd: Path, display: DisplayMode):
        self.cwd = cwd
        self.import_path = str(cwd.resolve())
        self.display = display
        self.globals: dict[str, object] = {"__name__": "__md_demo__"}

    def run_block(self, code: str) -> BlockResult:
        stdout = io.StringIO()
        stderr = io.StringIO()
        old_cwd = Path.cwd()
        ok = True
        try:
            os.chdir(self.cwd)
            sys.path.insert(0, self.import_path)
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                self._execute(code)
            self.cwd = Path.cwd()
        except BaseException:
            ok = False
            traceback.print_exc(file=stderr)
            self.cwd = Path.cwd()
        finally:
            if sys.path and sys.path[0] == self.import_path:
                del sys.path[0]
            else:
                with contextlib.suppress(ValueError):
                    sys.path.remove(self.import_path)
            os.chdir(old_cwd)
        return BlockResult(clean_output(stdout.getvalue() + stderr.getvalue()), ok)

    def _execute(self, code: str) -> None:
        if self.display != "last-expression" or final_statement_has_semicolon(code):
            exec(code, self.globals, self.globals)
            return

        tree = ast.parse(code)
        if not tree.body or not isinstance(tree.body[-1], ast.Expr):
            exec(compile(tree, "<md-demo>", "exec"), self.globals, self.globals)
            return

        setup = ast.Module(body=tree.body[:-1], type_ignores=tree.type_ignores)
        if setup.body:
            exec(compile(setup, "<md-demo>", "exec"), self.globals, self.globals)

        expression = ast.Expression(tree.body[-1].value)
        value = eval(compile(expression, "<md-demo>", "eval"), self.globals, self.globals)
        if value is not None:
            print(pprint.pformat(value))


def final_statement_has_semicolon(code: str) -> bool:
    last_type = None
    last_string = ""
    try:
        tokens = tokenize.generate_tokens(io.StringIO(code).readline)
        for token in tokens:
            if token.type in {
                tokenize.COMMENT,
                tokenize.DEDENT,
                tokenize.ENDMARKER,
                tokenize.ENCODING,
                tokenize.INDENT,
                tokenize.NL,
                tokenize.NEWLINE,
            }:
                continue
            last_type = token.type
            last_string = token.string
    except tokenize.TokenError:
        return False
    return last_type == tokenize.OP and last_string == ";"


class BashRunner(Runner):
    def __init__(self, cwd: Path):
        self.sentinel = f"__MD_DEMO_{uuid.uuid4().hex}__"
        self.proc = subprocess.Popen(
            ["bash"],
            cwd=str(cwd),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

    def run_block(self, code: str) -> BlockResult:
        if self.proc.stdin is None or self.proc.stdout is None:
            return BlockResult("bash runner is not available\n", False)
        marker = f"{self.sentinel}_{uuid.uuid4().hex}"
        self.proc.stdin.write(code)
        if code and not code.endswith("\n"):
            self.proc.stdin.write("\n")
        self.proc.stdin.write(f"printf '\\n{marker}:%s\\n' \"$?\"\n")
        self.proc.stdin.flush()

        lines: list[str] = []
        status: int | None = None
        for line in self.proc.stdout:
            stripped = line.rstrip("\n")
            if stripped.startswith(f"{marker}:"):
                try:
                    status = int(stripped.rsplit(":", 1)[1])
                except ValueError:
                    status = 1
                break
            lines.append(line)
        if status is None:
            return BlockResult(clean_output("bash runner ended before block completed\n"), False)
        if lines and lines[-1] == "\n":
            lines.pop()
        return BlockResult(clean_output("".join(lines)), status == 0)

    def close(self) -> None:
        if self.proc.stdin is not None:
            try:
                self.proc.stdin.write("exit\n")
                self.proc.stdin.flush()
            except BrokenPipeError:
                pass
        try:
            self.proc.wait(timeout=1)
        except subprocess.TimeoutExpired:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.proc.kill()


def make_runner(runtime: str, cwd: Path, display: DisplayMode = "last-expression") -> Runner:
    if runtime == "python":
        return PythonRunner(cwd, display)
    if runtime == "bash":
        return BashRunner(cwd)
    raise ValueError(f"unsupported normalized runtime: {runtime}")

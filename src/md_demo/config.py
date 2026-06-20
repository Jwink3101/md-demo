from __future__ import annotations

import dataclasses
from typing import Literal

import yaml

from .errors import MdDemoError

ConfigStyle = Literal["preserve", "front-matter", "hidden"]


@dataclasses.dataclass(frozen=True)
class ConfigBlock:
    config: dict
    body_start: int
    style: str
    front_matter: dict


def parse_config(lines: list[str]) -> ConfigBlock:
    if not lines:
        return default_config()
    first = lines[0].strip()
    if first == "---":
        end_index = _find_end(lines, start=1, marker="---", error="unterminated YAML front matter")
        data = load_yaml_config("".join(lines[1:end_index]), "front matter")
        config = data.get("md-demo")
        if config is None:
            config = {"runtime": "python"}
        if not isinstance(config, dict):
            raise MdDemoError("md-demo front matter config must be a mapping")
        front_matter = dict(data)
        front_matter.pop("md-demo", None)
        return ConfigBlock(
            config=config, body_start=end_index + 1, style="front-matter", front_matter=front_matter
        )
    if first.startswith("<!-- md-demo") and first[len("<!-- md-demo") :].strip() in {"", "-->"}:
        if first.endswith("-->"):
            raise MdDemoError("missing md-demo.runtime")
        end_index = _find_end(
            lines,
            start=1,
            marker="-->",
            error="unterminated md-demo HTML comment config",
        )
        data = load_yaml_config("".join(lines[1:end_index]), "md-demo HTML comment config")
        config = data.get("md-demo") if isinstance(data.get("md-demo"), dict) else data
        if not isinstance(config, dict):
            raise MdDemoError("md-demo HTML comment config must be a mapping")
        body_start = end_index + 1
        front_matter: dict = {}
        front_matter_start = body_start
        while front_matter_start < len(lines) and lines[front_matter_start].strip() == "":
            front_matter_start += 1
        if front_matter_start < len(lines) and lines[front_matter_start].strip() == "---":
            fm_end = _find_end(
                lines,
                start=front_matter_start + 1,
                marker="---",
                error="unterminated YAML front matter",
            )
            front_matter = load_yaml_config(
                "".join(lines[front_matter_start + 1 : fm_end]), "front matter"
            )
            body_start = fm_end + 1
        return ConfigBlock(
            config=config, body_start=body_start, style="hidden", front_matter=front_matter
        )
    return default_config()


def default_config() -> ConfigBlock:
    return ConfigBlock(
        config={"runtime": "python"},
        body_start=0,
        style="default",
        front_matter={},
    )


def render_config(block: ConfigBlock, newline: str, style: ConfigStyle) -> list[str]:
    if style == "preserve":
        return []
    if style == "front-matter":
        data = dict(block.front_matter)
        data["md-demo"] = dict(block.config)
        return ["---" + newline, dump_yaml(data, newline), "---" + newline]
    if style == "hidden":
        front_matter = dict(block.front_matter)
        front_matter.pop("md-demo", None)
        lines = ["<!-- md-demo" + newline, dump_yaml(block.config, newline), "-->" + newline]
        if front_matter:
            lines.extend(
                [newline, "---" + newline, dump_yaml(front_matter, newline), "---" + newline]
            )
        return lines
    raise MdDemoError(f"unsupported config style: {style}")


def load_yaml_config(text: str, label: str) -> dict:
    try:
        data = yaml.safe_load(text) or {}
    except yaml.YAMLError as exc:
        raise MdDemoError(f"invalid YAML {label}: {exc}") from exc
    if not isinstance(data, dict):
        raise MdDemoError(f"YAML {label} must be a mapping")
    return data


def dump_yaml(data: dict, newline: str) -> str:
    text = yaml.safe_dump(data, sort_keys=False, default_flow_style=False)
    return text.replace("\n", newline)


def _find_end(lines: list[str], *, start: int, marker: str, error: str) -> int:
    for index in range(start, len(lines)):
        if lines[index].strip() == marker:
            return index
    raise MdDemoError(error)

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .document import process_file, write_output
from .errors import ExecutionFailed, MdDemoError
from .manual import MANUAL

HELP_DESCRIPTION = """A lightweight Markdown demo runner.

By default, md-demo updates FILE in place.
Use --output PATH to write elsewhere, or --output - to write to stdout.

Markdown documents run as Python with default settings when no header is present.
Optional header reference:
  YAML front matter uses md-demo:; hidden comment config is YAML with direct keys.

  Key           Default          Purpose
  runtime       python           python, python3, bash, or shell
  display       last-expression  use none to disable Python final-expression output
  preface-text  empty            text inserted before generated result fences
  result-language empty          info string for generated result fences
  setup         empty            hidden code run before the first executable block

Warning: md-demo executes code from the document. Run only trusted files.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="md-demo",
        description=HELP_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("file", nargs="?", help="Markdown file to process")
    parser.add_argument(
        "--clear", action="store_true", help="remove generated result blocks without executing code"
    )
    parser.add_argument(
        "--config-style",
        choices=["preserve", "front-matter", "hidden"],
        default="preserve",
        help="config rewrite style; default preserve keeps the existing style",
    )
    parser.add_argument("--output", help="write updated Markdown to PATH; use - for stdout")
    parser.add_argument(
        "--manual", action="store_true", help="print the detailed authoring and usage guide"
    )
    parser.add_argument("--version", action="version", version=f"md-demo {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.manual:
        print(MANUAL, end="")
        return 0
    if not args.file:
        parser.error("FILE is required unless --manual is used")
    path = Path(args.file)
    try:
        result = process_file(path, clear=args.clear, config_style=args.config_style)
        write_output(path, result.text, args.output)
        for warning in result.warnings:
            print(warning, file=sys.stderr)
        if args.output is None:
            print(f"updated {path}", file=sys.stderr)
        return 0
    except ExecutionFailed as exc:
        write_output(path, exc.document, args.output)
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except MdDemoError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

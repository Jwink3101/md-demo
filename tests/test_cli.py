from __future__ import annotations

from pathlib import Path

from md_demo.cli import main


def doc(body: str) -> str:
    return f"---\nmd-demo:\n  runtime: python\n---\n\n{body}"


def test_default_invocation_updates_file_in_place(tmp_path: Path):
    path = tmp_path / "demo.md"
    path.write_text(doc("```python exe\nprint('hello')\n```\n"))
    assert main([str(path)]) == 0
    assert "hello" in path.read_text()


def test_output_path_leaves_source_unchanged(tmp_path: Path):
    source = tmp_path / "demo.md"
    rendered = tmp_path / "rendered.md"
    original = doc("```python exe\nprint('hello')\n```\n")
    source.write_text(original)
    assert main([str(source), "--output", str(rendered)]) == 0
    assert source.read_text() == original
    assert "hello" in rendered.read_text()


def test_output_dash_prints_to_stdout(tmp_path: Path, capsys):
    source = tmp_path / "demo.md"
    original = doc("```python exe\nprint('hello')\n```\n")
    source.write_text(original)
    assert main([str(source), "--output", "-"]) == 0
    captured = capsys.readouterr()
    assert "hello" in captured.out
    assert source.read_text() == original


def test_config_style_hidden_updates_config_style(tmp_path: Path):
    source = tmp_path / "demo.md"
    source.write_text(doc("```python exe\nprint('hello')\n```\n"))
    assert main([str(source), "--config-style", "hidden"]) == 0
    text = source.read_text()
    assert text.startswith("<!-- md-demo\nruntime: python\n-->\n")
    assert "---\nmd-demo:" not in text


def test_manual_works_without_file(capsys):
    assert main(["--manual"]) == 0
    captured = capsys.readouterr()
    assert "Agent authoring checklist" in captured.out
    assert "Run only trusted files" in captured.out
    assert "pip install md-demo" in captured.out
    assert 'python -m pip install -e ".[test]"' in captured.out
    assert "python -m compileall -q src" in captured.out
    assert "pytest" in captured.out


def test_help_includes_trusted_warning(capsys):
    try:
        main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
    captured = capsys.readouterr()
    assert "Run only trusted files" in captured.out
    assert "--config-style" in captured.out
    assert "default preserve" in captured.out


def test_failed_execution_exits_nonzero_and_writes_file(tmp_path: Path):
    path = tmp_path / "demo.md"
    path.write_text(doc("```python exe\nraise ValueError('bad')\n```\n"))
    assert main([str(path)]) == 1
    assert "ValueError: bad" in path.read_text()


def test_missing_file_exits_nonzero(capsys):
    assert main(["missing.md"]) == 1
    captured = capsys.readouterr()
    assert "error:" in captured.err

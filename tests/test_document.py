from __future__ import annotations

from pathlib import Path

import pytest

from md_demo.document import RESULT_START, parse_document, process_text
from md_demo.errors import ExecutionFailed, MdDemoError


def doc(runtime: str, body: str) -> str:
    return f"---\nmd-demo:\n  runtime: {runtime}\n---\n\n{body}"


def doc_with_config(config: str, body: str) -> str:
    return f"---\nmd-demo:\n{config}---\n\n{body}"


def hidden_doc(config: str, body: str) -> str:
    return f"<!-- md-demo\n{config}-->\n\n{body}"


def test_front_matter_accepts_runtime_aliases():
    for runtime, normalized in [
        ("python", "python"),
        ("python3", "python"),
        ("bash", "bash"),
        ("shell", "bash"),
    ]:
        parsed = parse_document(doc(runtime, ""))
        assert parsed.runtime == normalized


def test_front_matter_rejects_missing_or_unsupported_runtime():
    with pytest.raises(MdDemoError):
        parse_document("---\ntitle: demo\n---\n")
    with pytest.raises(MdDemoError):
        parse_document(doc("ruby", ""))


def test_front_matter_ignores_unrelated_keys():
    parsed = parse_document("---\ntitle: Demo\nmd-demo:\n  runtime: python\n---\n")
    assert parsed.runtime == "python"


def test_front_matter_accepts_preface_text():
    parsed = parse_document('---\nmd-demo:\n  runtime: python\n  preface-text: "Output:"\n---\n')
    assert parsed.preface_text == "Output:"


def test_front_matter_accepts_display_modes():
    parsed = parse_document("---\nmd-demo:\n  runtime: python\n---\n")
    assert parsed.display == "last-expression"

    parsed = parse_document("---\nmd-demo:\n  runtime: python\n  display: none\n---\n")
    assert parsed.display == "none"


def test_front_matter_rejects_unsupported_display_mode():
    with pytest.raises(MdDemoError, match="md-demo.display"):
        parse_document("---\nmd-demo:\n  runtime: python\n  display: rich\n---\n")


def test_hidden_html_comment_config_accepts_direct_keys():
    parsed = parse_document('<!-- md-demo\nruntime: python\npreface-text: "Output:"\n-->\n')
    assert parsed.runtime == "python"
    assert parsed.preface_text == "Output:"


def test_hidden_html_comment_config_accepts_opening_whitespace():
    parsed = parse_document("<!-- md-demo   \nruntime: python\n-->\n")
    assert parsed.runtime == "python"


def test_hidden_html_comment_config_accepts_namespaced_keys():
    parsed = parse_document("<!-- md-demo\nmd-demo:\n  runtime: shell\n-->\n")
    assert parsed.runtime == "bash"


def test_empty_hidden_html_comment_config_reports_missing_runtime():
    with pytest.raises(MdDemoError, match="missing md-demo.runtime"):
        parse_document("<!-- md-demo -->\n")


def test_front_matter_rejects_non_string_preface_text():
    with pytest.raises(MdDemoError):
        parse_document("---\nmd-demo:\n  runtime: python\n  preface-text: [Output]\n---\n")


def test_python_blocks_insert_results_and_persist_state(tmp_path: Path):
    result = process_text(
        doc(
            "python",
            """```python exe
a = 5
print(a)
```

```python exe
print(a + 1)
```
""",
        ),
        path=tmp_path / "demo.md",
    )
    assert "```text\n5\n```" in result.text
    assert "```text\n6\n```" in result.text


def test_hidden_html_comment_config_runs_document(tmp_path: Path):
    result = process_text(
        hidden_doc(
            'runtime: python\npreface-text: "Output:"\n',
            """```python exe
print("hello")
```
""",
        ),
        path=tmp_path / "demo.md",
    )
    assert '<!-- md-demo\nruntime: python\npreface-text: "Output:"\n-->' in result.text
    assert "Output:\n\n```text\nhello\n```" in result.text


def test_config_style_hidden_converts_front_matter(tmp_path: Path):
    result = process_text(
        doc_with_config(
            '  runtime: python\n  preface-text: "Output:"\n',
            """```python exe
print("hello")
```
""",
        ),
        path=tmp_path / "demo.md",
        config_style="hidden",
    )
    assert result.text.startswith("<!-- md-demo\n")
    assert "runtime: python" in result.text
    assert "preface-text:" in result.text
    assert "---\nmd-demo:" not in result.text


def test_config_style_front_matter_converts_hidden_config(tmp_path: Path):
    result = process_text(
        hidden_doc(
            "runtime: shell\n",
            """```bash exe
echo hello
```
""",
        ),
        path=tmp_path / "demo.md",
        config_style="front-matter",
    )
    assert result.text.startswith("---\nmd-demo:\n  runtime: shell\n---\n")
    assert "<!-- md-demo\nruntime:" not in result.text


def test_config_style_hidden_preserves_unrelated_front_matter(tmp_path: Path):
    result = process_text(
        """---
title: Demo
md-demo:
  runtime: python
---

```python exe
print("hello")
```
""",
        path=tmp_path / "demo.md",
        config_style="hidden",
    )
    assert result.text.startswith("<!-- md-demo\nruntime: python\n-->\n\n---\ntitle: Demo\n---\n")
    assert "md-demo:" not in result.text.split("---", 2)[1]


def test_config_style_front_matter_preserves_unrelated_front_matter_after_hidden(tmp_path: Path):
    result = process_text(
        """<!-- md-demo
runtime: python
-->

---
title: Demo
---

```python exe
print("hello")
```
""",
        path=tmp_path / "demo.md",
        config_style="front-matter",
    )
    assert result.text.startswith("---\ntitle: Demo\nmd-demo:\n  runtime: python\n---\n")
    assert "<!-- md-demo\nruntime:" not in result.text


def test_python_chdir_persists_across_blocks(tmp_path: Path):
    result = process_text(
        doc(
            "python",
            """```python exe
import os
os.mkdir("sub")
os.chdir("sub")
```

```python exe
import os
print(os.getcwd().endswith("sub"))
```
""",
        ),
        path=tmp_path / "demo.md",
    )
    assert "```text\nTrue\n```" in result.text


def test_replaces_attached_old_result(tmp_path: Path):
    result = process_text(
        doc(
            "python",
            """```python exe
print("new")
```

<!-- md-demo: result start. Do not edit; this block is overwritten. -->
```text
old
```
<!-- md-demo: result end -->
""",
        ),
        path=tmp_path / "demo.md",
    )
    assert "new" in result.text
    assert "old" not in result.text


def test_preface_text_is_in_generated_region(tmp_path: Path):
    result = process_text(
        doc_with_config(
            '  runtime: python\n  preface-text: "Output:"\n',
            """```python exe
print("hello")
```
""",
        ),
        path=tmp_path / "demo.md",
    )
    assert (
        "<!-- md-demo: result start. Do not edit; this block is overwritten. -->\n"
        "Output:\n\n"
        "```text\nhello\n```"
    ) in result.text


def test_empty_preface_text_is_skipped(tmp_path: Path):
    result = process_text(
        doc_with_config(
            "  runtime: python\n  preface-text: ''\n",
            """```python exe
print("hello")
```
""",
        ),
        path=tmp_path / "demo.md",
    )
    assert "Output:" not in result.text
    assert (
        "<!-- md-demo: result start. Do not edit; this block is overwritten. -->\n```text"
        in result.text
    )


def test_empty_output_does_not_insert_result_block(tmp_path: Path):
    result = process_text(
        doc(
            "python",
            """```python exe
a = 5
```
""",
        ),
        path=tmp_path / "demo.md",
    )
    assert RESULT_START not in result.text
    assert "```text" not in result.text


def test_python_last_expression_display_is_default(tmp_path: Path):
    result = process_text(
        doc(
            "python",
            """```python exe
a = 5
a + 1
```
""",
        ),
        path=tmp_path / "demo.md",
    )
    assert "```text\n6\n```" in result.text


def test_python_last_expression_display_uses_pformat(tmp_path: Path):
    result = process_text(
        doc(
            "python",
            """```python exe
{"b": [1, 2, 3], "a": {"nested": True}}
```
""",
        ),
        path=tmp_path / "demo.md",
    )
    assert "{'a': {'nested': True}, 'b': [1, 2, 3]}" in result.text


def test_python_last_expression_display_skips_assignment_none_and_semicolon(tmp_path: Path):
    assigned = process_text(
        doc(
            "python",
            """```python exe
a = 5
```
""",
        ),
        path=tmp_path / "assigned.md",
    )
    assert RESULT_START not in assigned.text

    none_value = process_text(
        doc(
            "python",
            """```python exe
None
```
""",
        ),
        path=tmp_path / "none.md",
    )
    assert RESULT_START not in none_value.text

    semicolon = process_text(
        doc(
            "python",
            """```python exe
5 + 1;  # suppress display
```
""",
        ),
        path=tmp_path / "semicolon.md",
    )
    assert RESULT_START not in semicolon.text


def test_python_last_expression_display_can_be_disabled(tmp_path: Path):
    result = process_text(
        doc_with_config(
            "  runtime: python\n  display: none\n",
            """```python exe
5 + 1
```
""",
        ),
        path=tmp_path / "demo.md",
    )
    assert RESULT_START not in result.text


def test_empty_output_removes_old_attached_result_block(tmp_path: Path):
    result = process_text(
        doc(
            "python",
            """```python exe
a = 5
```

<!-- md-demo: result start. Do not edit; this block is overwritten. -->
```text
old
```
<!-- md-demo: result end -->
""",
        ),
        path=tmp_path / "demo.md",
    )
    assert RESULT_START not in result.text
    assert "old" not in result.text


def test_changed_preface_text_replaces_old_generated_region(tmp_path: Path):
    result = process_text(
        doc_with_config(
            '  runtime: python\n  preface-text: "Result:"\n',
            """```python exe
print("new")
```

<!-- md-demo: result start. Do not edit; this block is overwritten. -->
Output:

```text
old
```
<!-- md-demo: result end -->
""",
        ),
        path=tmp_path / "demo.md",
    )
    assert "Result:" in result.text
    assert "Output:" not in result.text
    assert "old" not in result.text


def test_stray_result_fails(tmp_path: Path):
    with pytest.raises(MdDemoError):
        process_text(
            doc(
                "python",
                """<!-- md-demo: result start. Do not edit; this block is overwritten. -->
```text
old
```
<!-- md-demo: result end -->
""",
            ),
            path=tmp_path / "demo.md",
        )


def test_clear_removes_attached_results_without_executing(tmp_path: Path):
    result = process_text(
        doc(
            "python",
            """```python exe
raise RuntimeError("would run")
```

<!-- md-demo: result start. Do not edit; this block is overwritten. -->
```text
old
```
<!-- md-demo: result end -->
""",
        ),
        path=tmp_path / "demo.md",
        clear=True,
    )
    assert "old" not in result.text
    assert "would run" in result.text
    assert "raise RuntimeError" in result.text


def test_non_executable_code_block_is_preserved(tmp_path: Path):
    source = doc("python", "```python\nprint('shown')\n```\n")
    result = process_text(source, path=tmp_path / "demo.md")
    assert result.text == source


def test_output_with_backticks_uses_longer_fence(tmp_path: Path):
    result = process_text(
        doc(
            "python",
            """```python exe
print("```")
```
""",
        ),
        path=tmp_path / "demo.md",
    )
    assert "````text\n```\n````" in result.text


def test_ansi_sequences_are_stripped(tmp_path: Path):
    result = process_text(
        doc(
            "python",
            """```python exe
print("\\033[31mred\\033[0m")
```
""",
        ),
        path=tmp_path / "demo.md",
    )
    assert "\033" not in result.text
    assert "red" in result.text


def test_python_exception_stops_and_clears_later_results(tmp_path: Path):
    with pytest.raises(ExecutionFailed) as excinfo:
        process_text(
            doc(
                "python",
                """```python exe
print("before")
```

```python exe
raise ValueError("bad")
```

```python exe
print("after")
```

<!-- md-demo: result start. Do not edit; this block is overwritten. -->
```text
stale after
```
<!-- md-demo: result end -->
""",
            ),
            path=tmp_path / "demo.md",
        )
    output = excinfo.value.document
    assert "before" in output
    assert "ValueError: bad" in output
    assert "stale after" not in output
    assert 'print("after")' in output


def test_bash_state_persists_and_stderr_is_captured(tmp_path: Path):
    result = process_text(
        doc(
            "bash",
            """```bash exe
name=world
mkdir -p sub
cd sub
```

```bash exe
echo "$name"
pwd
echo warning >&2
```
""",
        ),
        path=tmp_path / "demo.md",
    )
    assert "world" in result.text
    assert "/sub" in result.text
    assert "warning" in result.text


def test_bash_output_does_not_get_extra_separator_blank_line(tmp_path: Path):
    result = process_text(
        doc(
            "bash",
            """```bash exe
echo hello
```
""",
        ),
        path=tmp_path / "demo.md",
    )
    assert "```text\nhello\n```" in result.text


def test_bash_nonzero_exit_stops_execution(tmp_path: Path):
    with pytest.raises(ExecutionFailed) as excinfo:
        process_text(
            doc(
                "bash",
                """```bash exe
echo before
false
```

```bash exe
echo after
```
""",
            ),
            path=tmp_path / "demo.md",
        )
    assert "before" in excinfo.value.document
    assert "echo after" in excinfo.value.document
    assert excinfo.value.document.count(RESULT_START) == 1

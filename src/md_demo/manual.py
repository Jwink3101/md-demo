MANUAL = """# md-demo Manual

`md-demo` runs trusted code blocks in a Markdown document and writes generated output back into the document.

It is meant for readable demo documents that stay useful as plain Markdown. It is not a notebook system, a sandbox, or a runner for untrusted code.

## Trust and safety

`md-demo` executes code from the document on your machine. Run only trusted files. Python demos run in-process in v1, and shell demos run arbitrary bash commands.

## Document config

Runnable documents use Python defaults when no config is present. A plain Markdown file with `python exe` blocks is valid:

````markdown
```python exe
print("hello")
```
````

Add config only when you need to change a default, use shell, add a result label, or run hidden setup code before the first executable block. There are two supported forms.

Form 1, YAML front matter:

```yaml
---
md-demo:
  runtime: python
---
```

Form 2, hidden HTML comment config. The content between `<!-- md-demo` and `-->` is YAML:

````markdown
<!-- md-demo
runtime: python
-->
````

Use YAML front matter by default. YAML front matter config must be namespaced under `md-demo:` so it does not collide with other front matter keys. Use hidden HTML comment config when the target Markdown renderer shows front matter as visible page content; the comment body is YAML without the outer `md-demo` key. It preserves the existing config style unless `--config-style` is used.

Convert config style while running or clearing a document:

```bash
md-demo demo.md --config-style preserve
md-demo demo.md --config-style front-matter
md-demo demo.md --config-style hidden
```

`preserve` is the default and does not rewrite the config style. `front-matter` rewrites the document's config as namespaced YAML front matter. `hidden` rewrites the document's config as an HTML comment. Only the `md-demo` config is converted; unrelated front matter is preserved when practical.

Main config options:

| Option | Default | Purpose |
| --- | --- | --- |
| `runtime` | `python` | Selects `python`, `python3`, `bash`, or `shell`. |
| `display` | `last-expression` | Set to `none` to disable Python final-expression output. |
| `preface-text` | empty | Adds visible text before each generated output block. |
| `result-language` | `""` | Sets the info string for generated result fences, such as `text` or `console`. |
| `setup` | empty | Runs hidden setup code before the first executable block. |

In YAML front matter, these options must live under the `md-demo:` key. In hidden HTML comment config, the comment body is YAML and uses the option names directly.

Supported runtime values are `python`, `python3`, `bash`, and `shell`. `python3` is an alias for the Python runner. `shell` is an alias for the bash runner, not `/bin/sh`.

You may optionally add visible text before every generated output block:

```yaml
---
md-demo:
  runtime: python
  preface-text: "Output:"
---
```

With hidden HTML comment config, write YAML with the same option names:

````markdown
<!-- md-demo
runtime: python
preface-text: "Output:"
-->
````

If `preface-text` is missing, empty, or `null`, no label is inserted. The label is generated inside the result region, so changing `preface-text` updates existing results the next time `md-demo` runs.

Python last-expression display is enabled by default. To capture only stdout and stderr, set `display: none`:

```yaml
---
md-demo:
  display: none
---
```

Use `setup` for imports or initialization that should run before the first executable block without being shown in generated output:

```yaml
---
md-demo:
  setup: |
    import os
    from pathlib import Path
---
```

Setup code uses the document runtime, shares the same persistent state as visible blocks, and runs after the runner has changed into the current working directory. Output from successful setup code is discarded. If setup fails, `md-demo` writes the failure output at the block that could not run and stops.

Setup code runs before visible executable blocks. If a library reads environment variables when it is imported, put those environment variables in `setup` before importing the library there. Environment variables assigned in later visible blocks cannot affect import-time configuration that has already happened in `setup`.

## Executable blocks

Only matching-language code blocks marked with `exe` run.

````markdown
```python exe
print("hello")
```
````

Ordinary code blocks are examples only and are not executed.

## Results

Generated result blocks are inserted immediately after executable blocks that produce output.

````markdown
<!-- md-demo: result start. Do not edit; this block is overwritten. -->
Output:

```
hello
```
<!-- md-demo: result end -->
````

Do not edit generated result blocks. They are removed and recreated on each normal run. If a block produces no output, no result block is inserted. If `preface-text` is not configured, the generated result starts directly with the output fence. Set `result-language` to add an info string such as `text` or `console` to generated result fences.

## Execution model

Blocks run top-to-bottom in one persistent runtime. Python variables, imports, functions, shell variables, and shell directory changes can carry forward to later executable blocks. Python blocks can import modules from the Markdown file's directory. If `setup` is configured, it runs before the first executable block in that same persistent runtime.

Output is stdout and stderr. Python logging handlers created in one block with `logging.StreamHandler()`, `logging.StreamHandler(sys.stderr)`, or `logging.StreamHandler(sys.stdout)` are captured in the block where each log is emitted. For Python blocks, the final expression is also displayed by default when it is not assigned, does not evaluate to `None`, and is not followed by a trailing semicolon. Shell blocks should use `echo` or commands that naturally print output.

`md-demo` is intended for non-interactive demos. Blocks should not require prompts or terminal input.

## Failure behavior

A normal run behaves like clear and execute. Old result blocks are cleared first, then fresh results are inserted for blocks that produce output.

If a block fails, `md-demo` writes output through the failed block, stops before later executable blocks, and exits nonzero. Later executable blocks are left without result blocks because they did not run.

Intentional failures should be caught inside the demo code.

```python
try:
    validate("")
except ValueError as exc:
    print(type(exc).__name__, exc)
```

## CLI

Run and update a document in place:

```bash
md-demo demo.md
```

Write the updated Markdown elsewhere:

```bash
md-demo demo.md --output rendered.md
```

Write the updated Markdown to stdout:

```bash
md-demo demo.md --output -
```

Clear generated results without executing code:

```bash
md-demo demo.md --clear
```

Rewrite config style without executing code:

```bash
md-demo demo.md --clear --config-style hidden
```

Print concise help:

```bash
md-demo --help
```

Print this manual:

```bash
md-demo --manual
```

Print the installed version:

```bash
md-demo --version
```

## Project

Repository: [Jwink3101/md-demo](https://github.com/Jwink3101/md-demo)

Install the released package:

```bash
pip install md-demo
```

## Building and verifying

When working from a source checkout, install the project in editable mode with test dependencies:

```bash
python -m pip install -e ".[test]"
```

Verify the package and tests:

```bash
python -m compileall -q src
pytest
```

Write the generated Markdown to stdout without rewriting the source document:

```bash
md-demo demo.md --output -
```

This still executes the demo code. The code may modify files, services, or other external state even though the Markdown source is not rewritten.

Clear generated result blocks without executing code:

```bash
md-demo demo.md --clear --output -
```

## Repository agent guidance

Repositories containing `md-demo` demos can include the following minimal guidance in `AGENTS.md`:

```markdown
## md-demo demos

- The `md-demo` demos are [list the repository's demo files or directories here]. Do not leave this unspecified: agents need repository-specific paths to distinguish demos from ordinary Markdown.
- Executable fenced code blocks are marked with `exe`, run top-to-bottom in one persistent runtime, and have their captured output written into generated result blocks.
- Edit the demo prose and executable source blocks, not generated `md-demo` result blocks. Inspect the executable blocks before running them, regenerate output with `md-demo path/to/demo.md`, require a successful exit, and review the resulting diff.
- Run only trusted demos because their code executes locally.
- If the `md-demo` command is unavailable, install it with `pip install md-demo` or use the repository's documented development installation.
- Use `md-demo --manual` when authoring or troubleshooting a demo requires more detail. Do not call it by default for unrelated repository work.
```

## Agent authoring checklist

- Add config only when the Python defaults are not enough, or use the hidden HTML comment config when front matter renders visibly.
- Use one runtime per document.
- Use `--config-style hidden` or `--config-style front-matter` only when intentionally rewriting config style.
- Use `preface-text` only when rendered documents need a visible output label.
- Use `setup` for hidden imports or startup code that executable blocks need.
- Mark executable blocks with `exe`.
- Put expected displayed values on stdout, stderr, or the final Python expression.
- Let `md-demo` create, position, and replace generated result blocks.
- Do not edit generated result blocks.
- Handle intentional failures inside the code block.
- Do not rely on interactive input.
- Use `md-demo --output -` to inspect generated Markdown without rewriting the source document, remembering that it still executes the demo code.
- Run `python -m compileall -q src` and `pytest` after changing the tool.
"""

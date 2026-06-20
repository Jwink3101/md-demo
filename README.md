# md-demo

`md-demo` is a lightweight Markdown demo runner. It executes explicitly marked code blocks, captures stdout, stderr, and Python last expressions, and writes generated output back into the Markdown file.

It is meant for readable demo documents that stay useful as plain Markdown. It is not a notebook system, a sandbox, or a runner for untrusted code.

Repository: [Jwink3101/md-demo](https://github.com/Jwink3101/md-demo)

Warning: `md-demo` executes code from the document. Run only trusted files.

## Install

```bash
pip install md-demo
```

For development from a source checkout, install in editable mode with test dependencies and verify the checkout:

```bash
python -m pip install -e ".[test]"
python -m compileall -q src
pytest
```

## Quick start

Create a Markdown file with an executable Python block. No config header is needed for the Python defaults.

````markdown
```python exe
print("hello")
```
````

Run:

```bash
md-demo demo.md
```

`md-demo` updates the file in place by default and inserts a generated result block:

````markdown
```python exe
print("hello")
```

<!-- md-demo: result start. Do not edit; this block is overwritten. -->
```
hello
```
<!-- md-demo: result end -->
````

Do not edit generated result blocks. They are cleared and recreated on normal runs.

## Document config

Runnable documents use Python defaults when no config is present. Add config only when you need to change a default, use shell, add a result label, or run hidden setup code before the first executable block. There are two supported forms.

Use YAML front matter by default:

```yaml
---
md-demo:
  runtime: python
---
```

If your Markdown renderer shows front matter as visible page content, use hidden HTML comment config instead. The content between `<!-- md-demo` and `-->` is YAML:

````markdown
<!-- md-demo
runtime: python
-->
````

Both forms are parsed only at the top of the document. YAML front matter config must be namespaced under `md-demo:` so it does not collide with other front matter keys. Hidden HTML comment config is also YAML, but uses the same option names without the outer `md-demo` key. `md-demo` preserves whichever form the document already uses by default.

To convert config style while running or clearing a document, use `--config-style`:

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

Supported runtime values:

- `python`
- `python3`
- `bash`
- `shell`

`python3` is an alias for the Python runner. `shell` is an alias for the bash runner, not `/bin/sh`.

## Output labels

You can optionally add visible text before every generated output block with `preface-text`.

YAML front matter:

```yaml
---
md-demo:
  runtime: python
  preface-text: "Output:"
---
```

Hidden HTML comment config with a YAML body:

````markdown
<!-- md-demo
runtime: python
preface-text: "Output:"
-->
````

If `preface-text` is missing, empty, or `null`, no label is inserted. The label is generated inside the result region, so changing `preface-text` updates existing results the next time `md-demo` runs.

Generated result fences have no info string by default. Set `result-language` to add one, such as `text` or `console`.

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

## Executable blocks

Only matching-language fenced code blocks marked with `exe` run.

````markdown
```python exe
print("runs")
```
````

Ordinary code blocks are examples only:

````markdown
```python
print("shown, not run")
```
````

Executable blocks run top-to-bottom in one persistent runtime. Python variables, imports, functions, shell variables, and shell directory changes can carry forward to later executable blocks. Python blocks can import modules from the Markdown file's directory. If `setup` is configured, it runs before the first executable block in that same persistent runtime.

`md-demo` captures stdout and stderr. For Python blocks, the final expression is also displayed by default when it is not assigned, does not evaluate to `None`, and is not followed by a trailing semicolon.

## CLI

Update a document in place:

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

Clear generated result blocks without executing code:

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

Print the installed version:

```bash
md-demo --version
```

Print the detailed manual:

```bash
md-demo --manual
```

## Failure behavior

A normal run behaves like clear and execute:

1. Old generated results are cleared.
2. Executable blocks run top-to-bottom.
3. Fresh result blocks are inserted for blocks that produced output.

If a block fails, `md-demo` writes output through the failed block, stops before later executable blocks, and exits nonzero. Later executable blocks are left without result blocks because they did not run.

Intentional failures should be handled inside the demo code:

```python
try:
    validate("")
except ValueError as exc:
    print(type(exc).__name__, exc)
```

## Converting existing documents

- See [docs/markdown-conversion.md](docs/markdown-conversion.md) for converting ordinary Markdown documents.
- See [docs/jupyter-conversion.md](docs/jupyter-conversion.md) for converting Jupyter notebooks, usually by exporting to Markdown first.
- See [docs/design.md](docs/design.md) for the design.


## AI Disclosure

This tool was primarily generated with assistance from ChatGPT Codex, guided and directed by a human developer. Human involvement included requirements definition, some implementation direction, and cursory code review. The code has not undergone a comprehensive human audit or formal security review.

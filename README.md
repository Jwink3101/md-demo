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

Create a Markdown file with one runtime and one executable block.

````markdown
---
md-demo:
  runtime: python
---

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
```text
hello
```
<!-- md-demo: result end -->
````

Do not edit generated result blocks. They are cleared and recreated on normal runs.

## Document config

Every runnable document needs config with one runtime. There are two supported forms.

Use YAML front matter by default:

```yaml
---
md-demo:
  runtime: python
---
```

If your Markdown renderer shows front matter as visible page content, use hidden HTML comment config instead:

````markdown
<!-- md-demo
runtime: python
-->
````

Both forms are parsed only at the top of the document. `md-demo` preserves whichever form the document already uses by default.

To convert config style while running or clearing a document, use `--config-style`:

```bash
md-demo demo.md --config-style preserve
md-demo demo.md --config-style front-matter
md-demo demo.md --config-style hidden
```

`preserve` is the default and does not rewrite the config style. `front-matter` rewrites the document's `md-demo` config as YAML front matter. `hidden` rewrites the document's `md-demo` config as an HTML comment. Only the `md-demo` config is converted; unrelated front matter is preserved when practical.

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

Hidden HTML comment config:

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
  runtime: python
  display: none
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

Executable blocks run top-to-bottom in one persistent runtime. Python variables, imports, functions, shell variables, and shell directory changes can carry forward to later executable blocks.

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

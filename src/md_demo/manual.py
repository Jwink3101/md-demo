MANUAL = """# md-demo Manual

`md-demo` runs trusted code blocks in a Markdown document and writes generated output back into the document.

## Trust and safety

`md-demo` executes code from the document on your machine. Run only trusted files. Python demos run in-process in v1, and shell demos run arbitrary bash commands.

## Document config

Every runnable document needs config with one runtime. There are two supported forms.

Form 1, YAML front matter:

```yaml
---
md-demo:
  runtime: python
---
```

Form 2, hidden HTML comment config:

````markdown
<!-- md-demo
runtime: python
-->
````

Use YAML front matter by default. Use hidden HTML comment config when the target Markdown renderer shows front matter as visible page content. `md-demo` preserves the existing config style unless `--config-style` is used.

Convert config style while running or clearing a document:

```bash
md-demo demo.md --config-style preserve
md-demo demo.md --config-style front-matter
md-demo demo.md --config-style hidden
```

`preserve` is the default and does not rewrite the config style. `front-matter` rewrites the document's `md-demo` config as YAML front matter. `hidden` rewrites the document's `md-demo` config as an HTML comment. Only the `md-demo` config is converted; unrelated front matter is preserved when practical.

Supported runtime values are `python`, `python3`, `bash`, and `shell`. `python3` is an alias for the Python runner. `shell` is an alias for the bash runner, not `/bin/sh`.

You may optionally add visible text before every generated output block:

```yaml
---
md-demo:
  runtime: python
  preface-text: "Output:"
---
```

With YAML front matter, `preface-text` belongs under the `md-demo` key. With hidden HTML comment config, use the same option names without the outer `md-demo` key:

````markdown
<!-- md-demo
runtime: python
preface-text: "Output:"
-->
````

If `preface-text` is missing or empty, no label is inserted. The label is generated inside the result region, so changing `preface-text` updates existing results the next time `md-demo` runs.

## Executable blocks

Only matching-language code blocks marked with `exe` run.

````markdown
```python exe
print("hello")
```
````

Ordinary code blocks are examples only and are not executed.

## Results

Generated result blocks are inserted immediately after executable blocks.

````markdown
<!-- md-demo: result start. Do not edit; this block is overwritten. -->
Output:

```text
hello
```
<!-- md-demo: result end -->
````

Do not edit generated result blocks. They are removed and recreated on each normal run. If `preface-text` is not configured, the generated result starts directly with the `text` fence.

## Execution model

Blocks run top-to-bottom in one persistent runtime. Python variables, imports, functions, shell variables, and shell directory changes can carry forward to later executable blocks.

Output is stdout and stderr. Python blocks should use `print` for values that should appear in the document. Shell blocks should use `echo` or commands that naturally print output. Python last-expression display is not part of v1.

`md-demo` is intended for non-interactive demos. Blocks should not require prompts or terminal input.

## Failure behavior

A normal run behaves like clear and execute. Old result blocks are cleared first, then fresh results are inserted for blocks that run.

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

Print this manual:

```bash
md-demo --manual
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

Preview a document without modifying it:

```bash
md-demo demo.md --output -
```

Clear generated result blocks without executing code:

```bash
md-demo demo.md --clear --output -
```

## Agent authoring checklist

- Add `md-demo.runtime` front matter, or use the hidden HTML comment config when front matter renders visibly.
- Use one runtime per document.
- Use `--config-style hidden` or `--config-style front-matter` only when intentionally rewriting config style.
- Use `md-demo.preface-text` only when rendered documents need a visible output label.
- Mark executable blocks with `exe`.
- Put expected displayed values on stdout or stderr.
- Leave generated result blocks immediately after their source block.
- Do not edit generated result blocks.
- Handle intentional failures inside the code block.
- Do not rely on interactive input.
- Use `md-demo --output -` to preview generated Markdown before overwriting a document.
- Run `python -m compileall -q src` and `pytest` after changing the tool.
"""

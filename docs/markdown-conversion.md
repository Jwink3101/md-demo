# Converting Markdown Documents to md-demo

This guide describes how to convert an existing Markdown document into `md-demo` Markdown. It is written for both humans and coding agents.

The main job is judgment: decide which code blocks are demo steps that should run, which blocks are examples that should stay inert, and which nearby text or code blocks are old demo output that should be regenerated.

Warning: `md-demo` executes code from the document. Convert and run only documents you trust.

## Conversion workflow

1. Read the document before editing.
2. Identify whether the document is primarily a Python demo, bash demo, or ordinary documentation.
3. Add hidden `md-demo` config only when the document should become executable.
4. Mark only intended executable blocks with `exe`.
5. Convert expected displayed values to executable output.
6. Remove or preserve existing output based on the rules below.
7. Preview with `md-demo document.md --output -`.
8. Update in place only after reviewing the preview.

## Decide whether the document should become md-demo

Convert the document when it is meant to show a runnable sequence:

- A tutorial with setup, commands, and expected output.
- A walkthrough where later code depends on earlier code.
- A README section that demonstrates an API or CLI.
- A reproducible example where output should stay current.

Do not convert the whole document when it is mostly reference material:

- API reference pages with many independent examples.
- Conceptual documentation with illustrative snippets.
- Documents that mix many languages equally.
- Documents with commands that require credentials, remote services, destructive changes, or interactive input.

For mixed documents, convert only the runnable section or split the demo into a separate `md-demo` document.

## Add md-demo config

For converted Markdown documents, default to hidden HTML comment config. It avoids renderers that show YAML front matter as visible page content.

For Python demos:

````markdown
<!-- md-demo
runtime: python
-->
````

For shell demos:

````markdown
<!-- md-demo
runtime: bash
-->
````

YAML front matter is also supported if that better fits the target documentation system:

```yaml
---
md-demo:
  runtime: python
---
```

You can also rewrite the config style during a preview or cleanup run. The default is `--config-style preserve`, which keeps the existing style.

```bash
md-demo document.md --output - --config-style hidden
md-demo document.md --clear --config-style hidden
```

Use one runtime per document. If the existing Markdown mixes Python and shell snippets, choose the main runtime and leave the other language as non-executed examples, or split the document.

If rendered output blocks need a visible label, add `preface-text`:

````markdown
<!-- md-demo
runtime: python
preface-text: "Output:"
-->
````

If `preface-text` is missing or empty, no label is inserted.

## Mark executable blocks

Only add `exe` to blocks that should run every time the document is refreshed.

Before:

````markdown
```python
print("hello")
```
````

After:

````markdown
```python exe
print("hello")
```
````

Leave examples inert when they are illustrative, partial, unsafe, or not part of the linear demo.

````markdown
```python
# Shown as an example, not executed.
print("hello")
```
````

## Decide whether nearby content is demo output

Existing Markdown often has text or code blocks that look like command output. Do not remove them automatically. Classify each candidate carefully.

Treat nearby content as old demo output when most of these are true:

- It appears immediately after a runnable code block.
- It is a `text`, `console`, `output`, or unlabeled fenced block.
- The prose introduces it as output, result, traceback, response, or expected output.
- It matches what the preceding code would likely print.
- It has no explanation that would be useful if the code output changed.

Preserve nearby content as authored documentation when any of these are true:

- It explains concepts, tradeoffs, or interpretation.
- It is referenced by surrounding prose as an example, not as generated output.
- It contains hand-written commentary mixed with output.
- It is a fixture, input file, configuration sample, or expected-output contract.
- It is not immediately attached to the preceding runnable block.

When unsure, preserve the content and add `exe` only to the runnable code. After previewing `md-demo --output -`, a human can decide whether the old content should be removed.

## Convert old output to md-demo output

If a block is clearly old output, remove it before running `md-demo`. The tool will insert a generated result block.

Before:

````markdown
```python
print("hello")
```

```text
hello
```
````

After:

````markdown
```python exe
print("hello")
```
````

Then preview:

```bash
md-demo document.md --output -
```

If the preview is correct, update the document:

```bash
md-demo document.md
```

## Convert implicit displays to executable output

`md-demo` captures stdout and stderr. Python executable blocks also display the final expression by default when it is not assigned, does not evaluate to `None`, and is not followed by a trailing semicolon.

Before:

````markdown
```python
value + 1
```
````

After:

````markdown
```python exe
value + 1
```
````

For tabular data or other rich objects, prefer stable text output:

````markdown
```python exe
print(df.head().to_string())
```
````

## Preserve runnable order

`md-demo` runs executable blocks top-to-bottom in one persistent runtime. Move setup before dependent blocks. Remove assumptions from previous interactive sessions, hidden state, or manual out-of-order execution.

If the existing document has independent examples, either keep them non-executed or rewrite each example so the required setup is shown before it.

## Handle risky or interactive commands

Do not mark blocks with `exe` when they require:

- interactive input
- credentials not available in the environment
- remote services that may fail unpredictably
- destructive filesystem or database changes
- long-running processes meant to stay alive

Rewrite those sections as prose or non-executed examples.

## Handle intentional failures

`md-demo` stops on the first failed executable block. If the document intentionally demonstrates an error, catch or handle it inside the block.

Python:

```python
try:
    validate("")
except ValueError as exc:
    print(type(exc).__name__, exc)
```

Bash:

```bash
if ! grep "needle" missing.txt; then
  echo "grep failed as expected"
fi
```

## Agent conversion checklist

- Read the whole section before changing code fences.
- Decide whether the document is a Python demo, bash demo, or not a good `md-demo` candidate.
- Add hidden HTML comment config only when the document should be executable.
- Use YAML front matter only when it better fits the target documentation system.
- Use `--config-style hidden` or `--config-style front-matter` only when intentionally rewriting existing config style.
- Use `preface-text` only when rendered output needs a visible label.
- Mark only true demo steps with `exe`.
- Leave illustrative, partial, unsafe, or cross-language examples without `exe`.
- Keep simple Python expression displays as final expressions, or convert them to `print(...)` when explicit stdout is clearer.
- Remove nearby output only when it is clearly old demo output.
- Preserve authored explanations, fixtures, inputs, and expected-output contracts.
- Preview with `md-demo document.md --output -`.
- Use `md-demo document.md --clear --output -` to inspect the source without generated results.
- Run `python -m compileall -q src` and `pytest` after changing the tool.

## Quick decision table

| Existing content | Convert? | Reason |
| --- | --- | --- |
| `python` block followed by matching `text` output | Usually yes | Likely a runnable demo plus old output |
| `bash` command in a step-by-step tutorial | Usually yes | CLI demos benefit from refreshed output |
| Partial code fragment in an API reference | Usually no | It may not run by itself |
| Config file sample | No | It is input material, not executable demo code |
| Expected output in a test explanation | Usually no | It may be a contract, not generated output |
| Code requiring credentials or a remote service | Usually no | Output may be unstable or unsafe |

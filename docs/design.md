# md-demo Design

`md-demo` is a lightweight Markdown demo runner. It keeps Markdown as the source of truth, executes selected code blocks, and writes the captured results back into the same Markdown document.

The goal is to support readable, versionable demo documents without the weight or raw-file readability problems of notebooks (e.g., Jupyter Notebooks). The design intentionally starts small: Python demos and bash-style shell demos, explicit execution markers, generated result blocks, and a simple CLI.

## Goals

- Keep demo files readable as plain Markdown.
- Make executable code blocks visually obvious in source.
- Preserve linear demo state across blocks.
- Refresh generated output in place.
- Avoid notebook kernels and complex runtime systems.
- Keep the first implementation predictable and maintainable.

## Non-goals

- This is not a general notebook system.
- This is not a sandbox for untrusted code.
- This is not a multi-language document runner in v1.
- This is not a testing framework with expected failures, assertions, or exit-code matching.
- This is not a public runtime plugin API in v1.

## Document Model

An `md-demo` document is a normal Markdown file. If no `md-demo` config is present, the document uses Python defaults.

````markdown
```python exe
print("hello")
```
````

Config is optional and is needed only when changing defaults, using a shell runtime, adding result labels, or configuring setup code. The preferred YAML front matter form is namespaced under `md-demo:`:

```yaml
---
md-demo:
  runtime: python
---
```

The tool should parse YAML front matter with a YAML parser and ignore unrelated front matter keys. Direct top-level front matter keys such as `runtime` or `setup` are document metadata, not `md-demo` config.

Some Markdown renderers display YAML front matter. For those renderers, a document may instead use a top-of-file HTML comment config. The content between `<!-- md-demo` and `-->` is YAML:

````markdown
<!-- md-demo
runtime: python
-->
````

The hidden HTML comment form uses the same option names without the outer `md-demo` key. The normal YAML front matter remains the default documented form because it is more conventional and interoperates with other Markdown tooling. Both forms are parsed only at the top of the document.

The CLI preserves the existing config style by default. It may also convert style explicitly:

```bash
md-demo demo.md --config-style preserve
md-demo demo.md --config-style front-matter
md-demo demo.md --config-style hidden
```

`preserve` is the default and does not rewrite the config style. `front-matter` rewrites the document's config as namespaced YAML front matter. `hidden` rewrites the document's config as HTML comment config. The conversion should only rewrite the `md-demo` config and preserve unrelated front matter when practical.

The optional config declares one runtime when the Python default should be changed. Supported v1 runtime values are:

- `python`
- `python3`
- `bash`
- `shell`

Internally these normalize to two runners:

- `python` and `python3` use the Python runner.
- `bash` and `shell` use the bash runner.

Future versions may add more runtimes, but v1 should keep execution simple and predictable.

The document may also set optional visible text before each generated result:

```yaml
---
md-demo:
  runtime: python
  preface-text: "Output:"
---
```

Hidden config uses:

````markdown
<!-- md-demo
runtime: python
preface-text: "Output:"
-->
````

If `preface-text` is missing or empty, no label is inserted. The label is part of the generated result region, so changing the setting updates existing results on the next run.

Python documents may configure display behavior:

```yaml
---
md-demo:
  display: none
---
```

Supported display values are `last-expression` and `none`. The default is `last-expression`.

Documents may configure setup code:

```yaml
---
md-demo:
  setup: |
    import os
    from pathlib import Path
---
```

Setup code uses the configured runtime, shares the same persistent runtime state as executable blocks, and runs before the first executable block. It runs after the runner changes into the current working directory. Output from successful setup is discarded. If setup fails, the failure output is written at the block that could not run and execution stops.

## Executable Blocks

Code blocks execute only when explicitly marked with `exe`.

````markdown
```python exe
print("hello")
```
````

For a Python document, `python exe` and `python3 exe` blocks execute. For a bash/shell document, `bash exe` and `shell exe` blocks execute. Wrong-runtime `exe` blocks should warn rather than execute.

Ordinary code blocks are examples only:

````markdown
```python
print("shown, not run")
```
````

This explicit marker is important for least astonishment. Markdown files often contain code examples that should not run.

## Execution Semantics

Executable blocks run top-to-bottom in one persistent runtime for the document.

Python example:

````markdown
```python exe
a = 5
```

```python exe
print(a + 1)
```
````

The second block sees `a` and prints `6`.

Bash example:

````markdown
```bash exe
name=world
```

```bash exe
echo "$name"
```
````

The second block sees `name` and prints `world`.

If `setup` is configured, it runs before the first executable block in that same persistent runtime. It can define imports, helper functions, or startup code that should stay out of the rendered demo output.

Execution uses the Markdown file's directory as the working directory. Python execution also puts that directory first on `sys.path` while a block runs so adjacent modules can be imported. The process inherits the user's environment. v1 should not define special `md-demo` environment variables unless a concrete need emerges. Because setup code runs before visible executable blocks, libraries that read environment variables at import time should have those environment variables assigned in setup before the import.

`md-demo` is intended for non-interactive demos. Blocks should not require interactive input. This is guidance rather than a hard guarantee; v1 does not need special prompt handling.

## Output Semantics

v1 captures stdout and stderr. Python logging handlers created in one block with `logging.StreamHandler()`, `logging.StreamHandler(sys.stderr)`, or `logging.StreamHandler(sys.stdout)` should be captured in the block where each log is emitted. Python blocks also display the final expression by default when it is not assigned, does not evaluate to `None`, and is not followed by a trailing semicolon. Users may set `display: none` to capture only stdout and stderr.

Displayed Python expressions are appended to the same text output as stdout and stderr. They are formatted with Python's pretty-printer rather than notebook rich display hooks.

Captured output is written as text. ANSI color and control codes should be stripped by default so generated Markdown remains readable.

If output contains Markdown fences, the generated result block should use a long enough fence to preserve the output exactly without breaking Markdown.

Generated result fences have no info string by default. Users may set `result-language` to values such as `text` or `console` when a renderer should style generated output with a specific language.

## Generated Result Blocks

Generated output is written immediately after the executable block that produced it. If a block produces no output, no result block is inserted.

````markdown
<!-- md-demo: result start. Do not edit; this block is overwritten. -->
```
hello
```
<!-- md-demo: result end -->
````

The start comment includes the "do not edit" warning. The end comment stays short. Result comments should not include timestamps, durations, status metadata, block IDs, or hashes in v1. Stable generated output keeps diffs clean.

When `preface-text` is configured, it is generated inside the result region before the output fence:

````markdown
<!-- md-demo: result start. Do not edit; this block is overwritten. -->
Output:

```
hello
```
<!-- md-demo: result end -->
````

No explicit block IDs are required. Result blocks are paired by immediate adjacency:

1. Find an executable block.
2. Look immediately after it, ignoring blank lines.
3. If an attached `md-demo` result block exists, remove or replace it.
4. If no attached result block exists, insert one after execution only when output is non-empty.

Generated result blocks that are not immediately attached to an executable block are stray result blocks. A normal run should fail if any stray result block exists. This avoids leaving stale output in the document or deleting ambiguous content.

## Clear and Execute

A normal run behaves like "clear and execute":

1. Parse the document.
2. Validate the generated result block structure.
3. Remove old result blocks attached to executable blocks.
4. Execute blocks top-to-bottom.
5. Insert fresh result blocks for blocks that produced output.
6. Write the reconstructed document.

If a block produces no output, `md-demo` leaves no result block behind. This keeps quiet setup code from adding empty generated regions.

If execution fails, `md-demo` writes fresh output through the failed block, stops execution, and exits nonzero. Later executable blocks do not receive result blocks, because they did not run. This mirrors a notebook-style clear-and-execute workflow and avoids stale later outputs.

Intentional failures should be handled inside the demo code rather than by special v1 syntax.

Python:

````markdown
```python exe
try:
    validate("")
except ValueError as exc:
    print(type(exc).__name__, exc)
```
````

Bash:

````markdown
```bash exe
if ! grep "needle" missing.txt; then
  echo "grep failed as expected"
fi
```
````

## Clear-only Mode

The CLI should support a clear-only mode:

```bash
md-demo demo.md --clear
```

`--clear` removes attached generated result blocks without executing code. It should still validate document structure and fail on stray result blocks. Because it does not execute code, it should not check or start the configured runtime.

`--clear` writes in place by default and should also respect `--output`.

## Failure Behavior

Default behavior is stop on first execution failure.

On failure:

- Capture and insert the failed block's stdout/stderr.
- Stop before later executable blocks.
- Leave later executable blocks without result blocks because the run cleared old output first.
- Write the reconstructed document.
- Exit nonzero.

Stderr alone is not failure. Failure is based on the runtime's execution status: an unhandled Python exception, a bash block returning nonzero, or a runner-level error.

Exit codes should stay simple in v1:

- `0` means success.
- Nonzero means parse failure, invalid front matter, stray result block, execution failure, write failure, or another error.

No detailed exit-code taxonomy is needed in v1.

## CLI

The normal command accepts one Markdown file.

```bash
md-demo demo.md
```

By default, this updates `demo.md` in place.

To write somewhere else:

```bash
md-demo demo.md --output rendered.md
```

To write the updated Markdown to stdout:

```bash
md-demo demo.md --output -
```

In-place writes should be atomic: build the complete updated document first, write to a temporary file in the same directory, then replace the original.

`--help` should be concise and include the trusted-code warning:

```text
Usage: md-demo [options] FILE

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

Options:
  --clear        remove generated result blocks without executing code
  --output PATH  write updated Markdown to PATH; use - for stdout
  --manual       print the detailed authoring and usage guide
  --version      show the installed version and exit
  -h, --help     show this help

Warning: md-demo executes code from the document. Run only trusted files.
```

`--manual` prints the detailed authoring and usage guide. It should work without a file argument and should not parse or execute any document.

`--version` prints the installed package version and exits without requiring a file argument.

The manual should cover:

- optional front matter
- runtime values and aliases
- setup code
- executable block syntax
- generated result blocks
- clear-and-execute behavior
- clear-only mode
- failure behavior
- intentional failure patterns
- trusted-code warning
- examples

## Trust and Safety

`md-demo` executes local code from Markdown documents. Users should run it only on documents they trust.

The warning belongs in both `--help` and `--manual`.

v1 should not add interactive confirmation prompts, `--trusted` flags, or sandboxing. Those would add friction and complexity without changing the core fact that this is a local code execution tool.

Python demos may run in-process in v1 for implementation simplicity. Shell demos can run arbitrary shell commands. Both should be documented as trusted-code execution.

## Implementation Shape

The document pipeline should be shared across runtimes:

1. Read the file.
2. Parse optional config.
3. Scan Markdown for fenced code blocks and generated result blocks.
4. Validate pairing and fail on strays.
5. Clear attached results.
6. Select a runner from the normalized runtime.
7. Execute blocks in order.
8. Insert result blocks.
9. Write the updated document.

Use a simple line-oriented scanner or a lightweight Markdown parser with source positions. Avoid regex-only parsing for the full document rewrite.

Preserve existing line endings when practical.

The runtime layer should use a narrow internal abstraction:

```python
class Runner:
    def run_block(self, code: str) -> BlockResult:
        ...

    def close(self) -> None:
        ...
```

This abstraction is internal in v1. The public interface is the CLI and the documented Markdown format.

## Python Runner

The Python runner should execute blocks in a persistent Python context.

If implemented in Python, the simplest v1 approach is shared globals with `exec`:

```python
globals_dict = {}

for block in executable_blocks:
    exec(block.code, globals_dict, globals_dict)
```

For `display: last-expression`, the runner parses each block and, when the final statement is an expression without a trailing semicolon, evaluates that expression separately after executing the preceding statements. If the value is not `None`, it is formatted with `pprint.pformat` and appended to captured output.

For each block, temporarily capture `sys.stdout` and `sys.stderr` so output can be attached to that block. Python stdout and stderr capture should use persistent proxy streams whose targets change per block, so logging handlers or other objects that bind `sys.stdout` or `sys.stderr` in one block still write into the current block's output later.

This is straightforward and avoids a notebook kernel. It also means Python demo code is trusted and can affect the `md-demo` process. That tradeoff is acceptable for v1 and should be documented.

## Bash Runner

The bash/shell runner should execute blocks in one persistent bash process.

This preserves shell variables, functions, aliases where applicable, and directory changes across blocks. It is more complex than running one shell per block, but it matches the document execution model.

The implementation can send each block to a long-lived bash process and use a unique sentinel to identify block completion and exit status.

`shell` is a user-facing alias for the bash runner, not `/bin/sh`.

## Future Possibilities

These are intentionally not v1 requirements:

- More runtimes.
- Python expression display.
- Expected-failure block modifiers.
- Runtime plugin APIs.
- Structured result metadata.
- ANSI preservation or HTML color rendering.
- Verbose live terminal streaming.
- Multi-file processing.
- stdin input documents.
- Timeouts.
- Sandboxed execution.

The initial design should leave room for these without committing to them early.

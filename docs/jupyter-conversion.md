# Converting Jupyter Notebooks to md-demo

This guide describes a practical way to convert a Jupyter notebook into `md-demo` Markdown. It is written for both humans and coding agents.

The recommended workflow is:

1. Export the notebook to Markdown with a Jupyter converter.
2. Clean up the exported Markdown.
3. Add `md-demo` config only when the Python defaults are not enough.
4. Mark the code blocks that should execute with `exe`.
5. Convert rich notebook display assumptions into explicit text or files.
6. Run `md-demo` and review the generated result blocks.

Warning: `md-demo` executes code from the document. Convert and run only notebooks you trust.

## Export the notebook

Start by converting the notebook to Markdown. If Jupyter is available, use `nbconvert`:

```bash
jupyter nbconvert --to markdown notebook.ipynb
```

This usually creates `notebook.md` and may create a companion asset directory for images or other outputs.

If `jupyter` is not available, install the needed Jupyter tooling in your environment first. The exact install command depends on the environment, but the converter step should still produce ordinary Markdown before `md-demo` edits begin.

## Add md-demo config

Python notebooks do not need config when the defaults are enough. A plain Markdown document with `python exe` blocks runs as Python with last-expression display enabled, no result label, and no setup code.

Add config when the converted notebook needs a shell runtime, disabled last-expression display, a result label, or hidden setup code. For converted notebooks that need config, default to hidden HTML comment config. It avoids renderers that show YAML front matter as visible page content. The content between `<!-- md-demo` and `-->` is YAML.

For a Python notebook:

````markdown
<!-- md-demo
runtime: python
-->
````

For a shell-oriented notebook:

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
md-demo notebook.md --output - --config-style hidden
md-demo notebook.md --clear --config-style hidden
```

Use one runtime per document. If the notebook mixes Python and shell cells, choose the main demo runtime and convert the other cells into prose, non-executed examples, or separate `md-demo` documents.

Config options:

| Option | Default | Purpose |
| --- | --- | --- |
| `runtime` | `python` | Selects `python`, `python3`, `bash`, or `shell`. |
| `display` | `last-expression` | Set to `none` to disable Python final-expression output. |
| `preface-text` | empty | Adds visible text before each generated output block. |
| `result-language` | `""` | Sets the info string for generated result fences, such as `text` or `console`. |
| `setup` | empty | Runs hidden setup code before the first executable block. |

In YAML front matter, these options must live under the `md-demo:` key. In hidden HTML comment config, the comment body is YAML and uses the option names directly.

## Mark executable cells

`md-demo` executes only fenced code blocks marked with `exe`.

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

Do not mark every code block automatically unless that is truly intended. Many notebooks contain scratch cells, setup alternatives, debugging snippets, or examples that should remain visible but not run.

## Convert notebook output expectations

Jupyter often displays the value of the last expression in a cell. `md-demo` does the same for Python executable blocks by default, using plain text pretty-printing.

Before:

````markdown
```python
a + 1
```
````

After:

````markdown
```python exe
a + 1
```
````

If a Python expression should not display, end the final statement with `;` or set `display: none` in the document config. For rich displays, convert to explicit text output or write files intentionally.

Before:

````markdown
```python
df.head()
```
````

After:

````markdown
```python exe
print(df.head().to_string())
```
````

If the notebook output depends on display hooks, HTML rendering, widgets, interactive prompts, or hidden notebook state, rewrite that cell into explicit non-interactive code before running `md-demo`.

## Handle existing notebook outputs

Markdown exported by Jupyter may include old outputs as images, tables, plain text, or rendered Markdown. `md-demo` does not know which exported blocks came from notebook outputs.

Recommended cleanup:

- Remove old notebook output blocks that should be regenerated.
- Keep authored prose and explanatory examples.
- Keep image assets only when they are intentional source material, not stale generated output.
- Do not manually create `md-demo` result blocks unless needed for migration; `md-demo` will insert them when it runs.

After cleanup, run:

```bash
md-demo notebook.md --output -
```

Review the generated Markdown. If it looks right, run:

```bash
md-demo notebook.md
```

## Preserve state intentionally

`md-demo` runs executable blocks top-to-bottom in one persistent runtime. This is similar to running a notebook from a clean kernel in order.

Move any required setup before the blocks that depend on it, or use config `setup` for imports and initialization that should run before the first executable block without being shown in generated output. Remove dependencies on hidden notebook state, out-of-order execution, or variables created only during an interactive session.

If a notebook only works after cells are run manually out of order, reorder or rewrite it before converting.

## Handle failures

`md-demo` stops on the first failed executable block. If the notebook intentionally demonstrates an error, catch and print it inside the code.

```python
try:
    validate("")
except ValueError as exc:
    print(type(exc).__name__, exc)
```

For shell demos:

```bash
if ! grep "needle" missing.txt; then
  echo "grep failed as expected"
fi
```

## Agent conversion checklist

- Convert `.ipynb` to Markdown first, preferably with `jupyter nbconvert --to markdown`.
- Add config only when the Python defaults are not enough.
- Use YAML front matter only when it better fits the target documentation system.
- Use `--config-style hidden` or `--config-style front-matter` only when intentionally rewriting existing config style.
- Use exactly one runtime for the converted document.
- Use `setup` for hidden imports or startup code that executable blocks need.
- Mark only intended executable blocks with `exe`.
- Keep simple Python last-expression displays as final expressions, or convert them to `print(...)` when explicit stdout is clearer.
- Remove stale exported notebook outputs that should be regenerated.
- Keep non-executed examples as normal fenced code blocks without `exe`.
- Ensure blocks are non-interactive and do not rely on hidden notebook state.
- Preview with `md-demo notebook.md --output -`.
- Clear generated results with `md-demo notebook.md --clear --output -` if needed.
- Verify tool changes with `python -m compileall -q src` and `pytest`.

## Common conversion patterns

Python expression display:

````markdown
```python exe
value
```
````

Pandas preview:

````markdown
```python exe
print(df.head().to_string())
```
````

Matplotlib file output:

````markdown
```python exe
fig.savefig("plot.png")
print("wrote plot.png")
```
````

Shell command:

````markdown
```bash exe
echo "hello"
```
````

Non-executed example:

````markdown
```python
print("shown but not run")
```
````

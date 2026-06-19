## Documentation and Formatting

- For all Markdown files:
    - Do not use hard line breaks
    - Ensure there is always a blank line after a section header
    - Prefer `-` to `*` for itemize but also prefer consistency with the rest of the document or block 
    - Never use full filesystem paths to cross-reference docs. Always prefer them to be relative links.
- For public Python functions, use NumPy style but prefer Markdown-esque formatting
- Assume isort and Python black will be used. Add these to a `pyproject.toml` as needed

## Specifications

- Code specification documents exist. If the user requests a change that is not in agreement with the specification, alert them and confirm. Then update as needed
- Keep specification documents up to date when possible.
- Keep the internal `md-demo --manual` text in sync with user-facing behavior and documentation changes.
- When generating design documents, do not over-specify the problem. Especially if the behavior is expected

## Other Notes

- When building `pyproject.toml` or the like, always use a dynamic version where the version is stored in the project
- Versioning should only be bumped if requested. Assume semantic versioning or date-based. semantic will look like A.B.C and date may look like YYYYMMDD.N where .N may be bumped as requested. Use the local date when updating.

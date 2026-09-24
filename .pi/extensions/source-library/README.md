# source-library Pi extension

Indexes files from the project `sources/` directory into disposable data under `.learning/source-index/`.

## Commands

- `/index-sources` → `uv run python .pi/extensions/source-library/bin/source_library.py index-sources`
- `/sources` → `uv run python .pi/extensions/source-library/bin/source_library.py sources`

## Tools

Tool wrappers read a JSON object from stdin and return JSON on stdout:

- `search_sources`: `{ "query": "...", "max_results": 8, "source": "optional filename" }`
- `read_source_pages`: `{ "source": "file.pdf", "start_page": 1, "end_page": 3 }`

## Dependencies

All Python dependencies must come from the project-root `pyproject.toml` and be executed through `uv run python`.

PDF extraction currently uses the `pypdf` dependency declared in the project root:

```toml
[project]
dependencies = [
    "pypdf>=6.19.0",
]
```

Do not install packages globally. Use `uv sync` if the project environment needs to be created/updated.

Plain text and Markdown indexing use only Python's standard library.

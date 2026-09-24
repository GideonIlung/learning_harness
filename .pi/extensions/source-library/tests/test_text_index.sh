#!/usr/bin/env bash
set -euo pipefail
ROOT="$(mktemp -d)"
mkdir -p "$ROOT/sources"
printf 'Alpha beta gamma\nPump efficiency and shaft power.\n' > "$ROOT/sources/sample notes.md"
printf 'Another file about thermodynamics and entropy.\n' > "$ROOT/sources/plain text.txt"
SOURCE_LIBRARY_PROJECT_ROOT="$ROOT" uv run python "$(dirname "$0")/../bin/source_library.py" index-sources >/tmp/source-library-test-index.out
SOURCE_LIBRARY_PROJECT_ROOT="$ROOT" uv run python "$(dirname "$0")/../bin/source_library.py" sources >/tmp/source-library-test-sources.out
SEARCH_OUT=$(printf '{"query":"pump efficiency","max_results":3}' | SOURCE_LIBRARY_PROJECT_ROOT="$ROOT" uv run python "$(dirname "$0")/../tools/search_sources.py")
echo "$SEARCH_OUT" | grep -q 'sample notes.md'
echo "$SEARCH_OUT" | grep -q 'Pump.*efficiency'
rm -rf "$ROOT"
echo "text indexing/search test passed"

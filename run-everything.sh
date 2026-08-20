#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
PORT="${PORT:-8787}"

cd "$ROOT"

if [[ "${1:-}" == "--discover" ]]; then
  echo "→ Searching GitHub for new candidates"
  python3 -m pipeline.discover --limit "${LIMIT:-8}"
  echo "→ Publishing the daily strict selection"
  python3 -m pipeline.autopublish --limit 1
fi

echo "→ Refreshing tool catalogue and GitHub trust evidence"
python3 -m pipeline.lifecycle
python3 -m pipeline.catalog

echo "→ Rendering the static PWA"
python3 -m pipeline.render

if curl --silent --fail "http://127.0.0.1:${PORT}/" >/dev/null 2>&1; then
  echo "✓ Site is already running at http://127.0.0.1:${PORT}"
  exit 0
fi

echo "→ Starting kgnx at http://127.0.0.1:${PORT}"
exec python3 -m http.server "$PORT" --bind 127.0.0.1 --directory site

#!/usr/bin/env bash
set -euo pipefail

cd /d/EnglishLearning

printf '%s\n' 'Updating local repository...'
if git pull; then
    printf '%s\n' 'Git pull succeeded.'
else
    printf '%s\n' 'Git pull failed. Starting the local app with current files...'
fi

printf '%s\n' 'Opening browser at http://127.0.0.1:8031'
python - <<'PY'
import webbrowser

webbrowser.open("http://127.0.0.1:8031")
PY

uv run python -m src.web_entrypoint

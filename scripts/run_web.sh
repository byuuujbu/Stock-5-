#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

exec "$PROJECT_ROOT/.venv/bin/python" -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"


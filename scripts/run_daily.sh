#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
mkdir -p logs

timestamp="$(date +%Y%m%d-%H%M%S)"
exec "$PROJECT_ROOT/.venv/bin/python" -m app.agent >> "logs/daily-$timestamp.out.log" 2>> "logs/daily-$timestamp.err.log"


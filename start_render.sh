#!/usr/bin/env bash
set -euo pipefail

python -m lemming.cli run &
ENGINE_PID=$!

cleanup() {
  echo "Stopping LeMMing Engine..."
  kill "$ENGINE_PID" 2>/dev/null || true
}
trap cleanup EXIT

python -m lemming.cli serve --host 0.0.0.0 --port "${PORT:-8000}" &
API_PID=$!

wait "$API_PID"

#!/usr/bin/env bash
# Starts the Farm2Feed server on macOS.
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  echo "Run ./setup_mac.sh first."; exit 1
fi
# shellcheck disable=SC1091
source .venv/bin/activate
export PYTHONUTF8=1
PORT_VALUE=$(grep -E '^PORT=' .env 2>/dev/null | cut -d= -f2 | tr -d '\r')
echo "Farm2Feed is starting. Open http://localhost:${PORT_VALUE:-5001}  (press Ctrl+C to stop)"
exec python -m uvicorn asgi:application --host 0.0.0.0 --port "${PORT_VALUE:-5001}"

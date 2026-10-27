#!/bin/sh
# Starts the backend and the TV simulator. Usage: ./run_server.sh [--port 8765] [--reset]
cd "$(dirname "$0")" || exit 1

for candidate in python3 python "py -3"; do
  if $candidate -c "import sys; sys.exit(sys.version_info < (3, 9))" >/dev/null 2>&1; then PY="$candidate"; break; fi
done
if [ -z "$PY" ] && [ -x python/python.exe ]; then PY="python/python.exe"; fi
if [ -z "$PY" ]; then
  echo "Nie znaleziono Pythona 3.9+. Zobacz README.md, sekcja 'Brak Pythona'." >&2
  exit 1
fi

exec $PY -m backend "$@"

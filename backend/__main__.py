"""Run the backend: ``python -m backend [--port 8765] [--reset]``."""

import argparse
import os

from backend.server import make_server
from backend.storage import JsonStore


def main():
    parser = argparse.ArgumentParser(prog="python -m backend")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.environ.get("TV_PORT", "8765")))
    parser.add_argument("--reset", action="store_true", help="restore the device registry from fixtures")
    args = parser.parse_args()

    store = JsonStore()
    if args.reset:
        store.reset()
    server = make_server(store, host=args.host, port=args.port)
    base = "http://localhost:%d" % server.server_address[1]
    print("Lumio TV backend: %s/api/health" % base)
    print("Telewizory:       %s/tv/?device=TV-001  (TV-001 ... TV-007)" % base)
    print("Ctrl+C zatrzymuje serwer.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import http.server
import socketserver
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    handler = lambda *handler_args, **handler_kwargs: http.server.SimpleHTTPRequestHandler(  # noqa: E731
        *handler_args,
        directory=str(ROOT_DIR),
        **handler_kwargs,
    )
    with socketserver.ThreadingTCPServer((args.host, args.port), handler) as httpd:
        print(f"Serving {ROOT_DIR} at http://{args.host}:{args.port}/dashboard/ch4_fincpa/index.html")
        httpd.serve_forever()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

MAX_U64 = 2**64 - 1


def is_valid_u64(value_str: str) -> bool:
    try:
        n = int(value_str, 10)
        return 0 <= n <= MAX_U64
    except Exception:
        return False


class EvenOddHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _bad_request(self, msg: str) -> None:
        self._send_json(400, {"error": msg})

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/healthz":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"ok")
            return

        if parsed.path == "/is-even":
            params = parse_qs(parsed.query or "")
            values = params.get("value") or params.get("v") or []
            if not values:
                self._bad_request("missing query param 'value'")
                return
            value_str = values[0]
            if not is_valid_u64(value_str):
                self._bad_request("value must be u64 (0..2^64-1)")
                return
            n = int(value_str, 10)
            self._send_json(200, {"value": n, "even": (n % 2 == 0)})
            return

        self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/is-even":
            self._send_json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        try:
            raw = self.rfile.read(length) if length > 0 else b""
            payload = json.loads(raw or b"{}")
        except Exception:
            self._bad_request("invalid JSON")
            return
        value = payload.get("value")
        if value is None:
            self._bad_request("missing JSON field 'value'")
            return
        if isinstance(value, int):
            n = value
            if not (0 <= n <= MAX_U64):
                self._bad_request("value must be u64 (0..2^64-1)")
                return
        else:
            value_str = str(value)
            if not is_valid_u64(value_str):
                self._bad_request("value must be u64 (0..2^64-1)")
                return
            n = int(value_str, 10)
        self._send_json(200, {"value": n, "even": (n % 2 == 0)})


def main() -> None:
    port_str = os.getenv("MODEL_PORT", "8080")
    try:
        port = int(port_str, 10)
    except Exception:
        port = 8080
    server = HTTPServer(("0.0.0.0", port), EvenOddHandler)
    print(f"Mock inference server listening on 0.0.0.0:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()



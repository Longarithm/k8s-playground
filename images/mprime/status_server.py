import http.server
import socketserver
import os
import json
import pathlib
import io


port = int(os.environ.get("MODEL_PORT", "8080"))
base_dir = pathlib.Path("/opt/mprime")


def tail_file(path: pathlib.Path, max_bytes: int = 8192) -> str:
    try:
        with path.open("rb") as f:
            try:
                f.seek(-max_bytes, io.SEEK_END)
            except Exception:
                # File smaller than max_bytes
                pass
            data = f.read()
        return data.decode("utf-8", errors="replace")
    except FileNotFoundError:
        return ""


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/health", "/ready"):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
            return
        if self.path == "/status":
            results_tail = tail_file(base_dir / "results.txt")
            log_tail = tail_file(base_dir / "prime.log")
            body = json.dumps(
                {
                    "results_tail": results_tail[-8192:],  # final bytes after decode
                    "log_tail": log_tail[-8192:],
                }
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("content-type", "application/json; charset=utf-8")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"not found")

    def log_message(self, *args, **kwargs):
        pass


with socketserver.TCPServer(("", port), Handler) as httpd:
    httpd.serve_forever()



import argparse
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from api.analyze import handler as AnalysisHandler

ROOT = Path(__file__).resolve().parent


class LocalHandler(SimpleHTTPRequestHandler, AnalysisHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def is_api(self):
        return urlsplit(self.path).path.rstrip("/") == "/api/analyze"

    def static_path_allowed(self):
        path = unquote(urlsplit(self.path).path)
        if path == "/":
            return True
        parts = path.lstrip("/").split("/")
        if any(part.startswith(".") for part in parts):
            return False
        target = (ROOT / path.lstrip("/")).resolve()
        if not target.is_relative_to(ROOT):
            return False
        if path.startswith("/assets/"):
            return target.suffix.lower() in {".css", ".js", ".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".mp4", ".webm", ".ogg", ".vtt", ".woff", ".woff2"}
        return len(parts) == 1 and target.suffix.lower() in {".html", ".ico"}

    def do_GET(self):
        if self.is_api():
            AnalysisHandler.do_GET(self)
        elif self.static_path_allowed():
            SimpleHTTPRequestHandler.do_GET(self)
        else:
            self.send_error(404)

    def do_HEAD(self):
        if self.is_api():
            AnalysisHandler.do_HEAD(self)
        elif self.static_path_allowed():
            SimpleHTTPRequestHandler.do_HEAD(self)
        else:
            self.send_error(404)

    def do_POST(self):
        if self.is_api():
            AnalysisHandler.do_POST(self)
        else:
            self.send_json(404, {"error": {"code": "not_found", "message": "This endpoint does not exist."}})

    def list_directory(self, path):
        self.send_error(404)
        return None

    def log_message(self, format, *args):
        return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), LocalHandler)
    print(f"Open http://127.0.0.1:{args.port} — press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

import json
import socket
import os
import time
import traceback
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from agent.ask import ask


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        p = urlparse(self.path)
        if p.path == "/health":
            self._send_json({"status": "ok"})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        p = urlparse(self.path)
        if p.path != "/ask":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("content-length", 0))
        body = self.rfile.read(length).decode("utf-8")
        try:
            payload = json.loads(body)
        except Exception:
            self._send_json({"error": "invalid json"}, code=400)
            return

        q = payload.get("question")
        collection = payload.get("collection", "court-files")
        top_k = int(payload.get("top_k", 5))
        format_mode = payload.get("format", payload.get("format_mode", "compact"))
        path_contains = payload.get("path_contains")
        date_from = payload.get("date_from")
        date_to = payload.get("date_to")
        file_ext = payload.get("file_ext")

        try:
            logging.info("/ask request: %s (collection=%s, top_k=%s)", q, collection, top_k)
            ans = ask(q, collection=collection, top_k=top_k, format_mode=format_mode, path_contains=path_contains, date_from=date_from, date_to=date_to, file_ext=file_ext)
            self._send_json({"answer": ans})
        except Exception as e:
            logging.exception("error handling /ask")
            self._send_json({"error": str(e)}, code=500)

    def log_message(self, format, *args):
        # write HTTP request logs to the logging facility
        logging.info("%s - - [%s] %s\n", self.client_address[0], self.log_date_time_string(), format % args)


def find_free_port(start=8000, end=8100):
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("no free port")


def run():
    # ensure logging directory exists and configure logging
    os.makedirs("web", exist_ok=True)
    log_path = os.path.join("web", "server.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler()
        ],
    )

    port = find_free_port()
    server = HTTPServer(("127.0.0.1", port), Handler)
    # write port and pid to files so external tools can discover them
    try:
        pf_path = os.path.join("web", "server.port")
        pid_path = os.path.join("web", "server.pid")
        with open(pf_path, "w", encoding="utf-8") as pf:
            pf.write(str(port))
            pf.flush()
            try:
                os.fsync(pf.fileno())
            except Exception:
                pass
        with open(pid_path, "w", encoding="utf-8") as pf:
            pf.write(str(os.getpid()))
            pf.flush()
            try:
                os.fsync(pf.fileno())
            except Exception:
                pass
        logging.info("wrote port=%s pid=%s", port, os.getpid())
    except Exception:
        logging.exception("failed writing port/pid files")

    logging.info("simple_server running on http://127.0.0.1:%s", port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("keyboard interrupt received, shutting down")
        server.shutdown()
    except Exception:
        logging.exception("server crashed")
    finally:
        try:
            pf_path = os.path.join("web", "server.port")
            pid_path = os.path.join("web", "server.pid")
            if os.path.exists(pf_path):
                os.remove(pf_path)
            if os.path.exists(pid_path):
                os.remove(pid_path)
        except Exception:
            logging.exception("error cleaning up port/pid files")


if __name__ == "__main__":
    run()

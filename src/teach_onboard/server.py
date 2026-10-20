"""A small local web server for onboarding. Standard library only; one learner, one machine by default."""
from __future__ import annotations

import json
import re
import traceback
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .course import CourseExists
from .llm import LLMError
from .onboarding import FlowError, Onboarding

STATIC = Path(__file__).resolve().parent / "static"
FILES = {"/": ("index.html", "text/html; charset=utf-8"),
         "/app.js": ("app.js", "text/javascript; charset=utf-8"),
         "/style.css": ("style.css", "text/css; charset=utf-8")}
MAX_BODY = 1_000_000
ROUTE = re.compile(r"^/api/session/([A-Za-z0-9_-]+)/([a-z/]+)$")


def make_handler(app: Onboarding, info: dict):
    class Handler(BaseHTTPRequestHandler):
        server_version = "teach-onboard"

        def log_message(self, fmt, *args):  # quieter console: one line per API call
            if self.path.startswith("/api/"):
                super().log_message(fmt, *args)

        def _send(self, status: int, body: bytes, ctype: str):
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status: int, data: dict):
            self._send(status, json.dumps(data).encode(), "application/json")

        def _body(self) -> dict:
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAX_BODY:
                raise FlowError("request too large")
            raw = self.rfile.read(n) if n else b"{}"
            data = json.loads(raw or b"{}")
            if not isinstance(data, dict):
                raise FlowError("expected a JSON object")
            return data

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path in FILES:
                name, ctype = FILES[path]
                return self._send(200, (STATIC / name).read_bytes(), ctype)
            if path == "/api/config":
                return self._json(200, info)
            m = ROUTE.match(path)
            if m and m.group(2) == "summary":
                return self._guard(lambda: app.summary(app.get(m.group(1))))
            self._json(404, {"error": "not found"})

        def do_POST(self):
            path = self.path.split("?", 1)[0]
            if path == "/api/session":
                def start():
                    b = self._body()
                    s = app.start(str(b.get("subject", "")), str(b.get("pack", "")))
                    return {"id": s.id, "subject": s.subject, "pack": s.pack.name if s.pack else ""}
                return self._guard(start)
            m = ROUTE.match(path)
            if not m:
                return self._json(404, {"error": "not found"})
            sid, action = m.groups()

            def run():
                s = app.get(sid)
                b = self._body()
                if action == "mission":
                    return app.submit_mission(s, b.get("answers", {}), str(b.get("follow_up_answer", "")))
                if action == "map":
                    return app.draft_map(s)
                if action == "map/confirm":
                    return app.set_map(s, b.get("skills", []), b.get("drop", []), b.get("flagged", []))
                if action == "placement/next":
                    return app.next_item(s)
                if action == "placement/answer":
                    return app.answer(s, str(b.get("answer", "")), bool(b.get("dont_know")))
                if action == "placement/dispute":
                    return app.dispute(s, int(b.get("index", -1)))
                if action == "finish":
                    return app.finish(s)
                raise FlowError("unknown action")

            self._guard(run)

        def _guard(self, fn):
            try:
                self._json(200, fn())
            except (FlowError, CourseExists, ValueError, json.JSONDecodeError) as e:
                self._json(HTTPStatus.BAD_REQUEST, {"error": str(e)})
            except LLMError as e:
                self._json(HTTPStatus.BAD_GATEWAY, {"error": str(e), "retry": True})
            except Exception as e:  # keep the server up; show the cause in the console
                traceback.print_exc()
                self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"unexpected error: {e}"})

    return Handler


def serve(app: Onboarding, info: dict, host: str, port: int) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), make_handler(app, info))

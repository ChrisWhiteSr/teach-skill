"""`teach-onboard serve`: a small local server for one course folder's lessons. Standard library only.

It serves lessons/, reference/, assets/ and the course's Markdown files read-only, and a JSON API the
lesson kit uses to save answers, log quiz clicks and run the review and draft jobs. By default it listens
on this machine only. API writes need a JSON body from a page this server served (Host and Origin checks),
so another website open in the same browser cannot post answers or start jobs.
"""
from __future__ import annotations

import json
import mimetypes
import re
import traceback
from html import escape
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from .files import Conflict, WriteRefused
from .llm import LLMError
from .method import skill_dir
from .runner import LessonRunner, RunnerError

MAX_BODY = 200_000
STATIC_DIRS = ("lessons", "reference", "assets")
STATIC_TYPES = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
                ".js": "text/javascript; charset=utf-8", ".svg": "image/svg+xml", ".png": "image/png",
                ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp",
                ".md": "text/plain; charset=utf-8", ".txt": "text/plain; charset=utf-8"}
KIT_FILES = ("lesson-kit.js", "lesson-kit.css")
JOB = re.compile(r"^/api/jobs/(\d+)$")
LOCAL = {"127.0.0.1", "localhost", "::1"}


def kit_dir() -> Path:
    return skill_dir() / "assets"


def install_kit(course: Path, overwrite: bool = False) -> list[Path]:
    """Copy the lesson kit into the course's assets/ folder. Only the kit's own files are written."""
    dest = Path(course).expanduser().resolve() / "assets"
    dest.mkdir(parents=True, exist_ok=True)
    written = []
    for name in KIT_FILES:
        target = dest / name
        if overwrite or not target.exists():
            target.write_bytes((kit_dir() / name).read_bytes())
            written.append(target)
    return written


def _course_page(runner: LessonRunner) -> bytes:
    rows = []
    labels = {"not_started": "Not started", "answered": "Answers waiting for feedback", "reviewed": "Feedback ready"}
    for c in runner.course():
        tag = f' <span class="tag">AI-drafted {escape(c["ai_drafted"])}</span>' if c["ai_drafted"] else ""
        rows.append(f'<li><a href="/lessons/{escape(c["lesson"])}.html">{escape(c["title"])}</a>{tag}'
                    f'<span class="small">{escape(labels.get(c["status"], c["status"]))}</span></li>')
    subject = escape(runner.subject())
    body = "\n".join(rows) or "<li>No HTML lessons yet. Lessons live in <code>lessons/NNNN-slug.html</code>.</li>"
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{subject}</title><link rel="stylesheet" href="/assets/lesson-kit.css"><style>
body{{font:17px/1.6 system-ui,sans-serif;max-width:760px;margin:40px auto;padding:0 20px;color:#1d2b2f}}
ol{{padding-left:1.2em}}li{{margin:12px 0}}li a{{font-weight:650}}.small{{display:block;font-size:.85rem;color:#586a6e}}
.tag{{font-size:.75rem;background:#f4e8c9;padding:2px 7px;border-radius:5px;margin-left:6px}}
</style></head><body><h1>{subject}</h1><p class="small">Course folder: {escape(runner.root.name)}. Progress lives in
<a href="/MAP.md">MAP.md</a> and <a href="/LOG.md">LOG.md</a>.</p><h2>Lessons</h2><ol>{body}</ol></body></html>""".encode()


def make_handler(runner: LessonRunner, info: dict):
    class Handler(BaseHTTPRequestHandler):
        server_version = "teach-lessons"

        def log_message(self, fmt, *args):
            if self.path.startswith("/api/") and not self.path.startswith("/api/jobs/"):
                super().log_message(fmt, *args)

        # ---- responses --------------------------------------------------------
        def _send(self, status: int, body: bytes, ctype: str):
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Frame-Options", "SAMEORIGIN")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status: int, data):
            self._send(status, json.dumps(data).encode(), "application/json")

        def _guard(self, fn):
            try:
                self._json(200, fn())
            except (RunnerError, WriteRefused, ValueError, json.JSONDecodeError) as e:
                self._json(HTTPStatus.BAD_REQUEST, {"error": str(e)})
            except Conflict as e:
                self._json(HTTPStatus.CONFLICT, {"error": f"{e} changed while saving; try again"})
            except LLMError as e:
                self._json(HTTPStatus.BAD_GATEWAY, {"error": str(e)})
            except Exception as e:  # keep serving; the cause goes to the console
                traceback.print_exc()
                self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"unexpected error: {e}"})

        # ---- request checks ---------------------------------------------------
        def _host_ok(self) -> bool:
            host = (self.headers.get("Host") or "").strip().lower()
            name = host.rsplit(":", 1)[0].strip("[]") if not host.startswith("[") else host[1:].split("]")[0]
            return name in LOCAL or name == info.get("host", "").lower()

        def _origin_ok(self) -> bool:
            origin = self.headers.get("Origin")
            if origin is None:
                return True
            host = self.headers.get("Host") or ""
            return origin in (f"http://{host}", f"https://{host}")

        def _body(self) -> dict:
            if (self.headers.get("Content-Type") or "").split(";")[0].strip().lower() != "application/json":
                raise RunnerError("expected a JSON body")
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAX_BODY:
                raise RunnerError("request too large")
            data = json.loads(self.rfile.read(n) or b"{}")
            if not isinstance(data, dict):
                raise RunnerError("expected a JSON object")
            return data

        # ---- static files -----------------------------------------------------
        def _static(self, path: str):
            rel = unquote(path).lstrip("/")
            parts = rel.split("/")
            if any(p in ("", ".", "..") or p.startswith(".") for p in parts):
                return self._json(404, {"error": "not found"})
            ext = Path(rel).suffix.lower()
            top_md = len(parts) == 1 and ext == ".md"
            if not (top_md or (parts[0] in STATIC_DIRS and len(parts) >= 2 and ext in STATIC_TYPES)):
                return self._json(404, {"error": "not found"})
            p = (runner.root / rel).resolve()
            if runner.root not in p.parents or not p.is_file():
                if parts[0] == "assets" and len(parts) == 2 and parts[1] in KIT_FILES:
                    p = kit_dir() / parts[1]  # the course has no copy yet: serve the bundled kit
                else:
                    return self._json(404, {"error": "not found"})
            ctype = STATIC_TYPES.get(ext) or mimetypes.guess_type(p.name)[0] or "application/octet-stream"
            self._send(200, p.read_bytes(), ctype)

        # ---- routes -----------------------------------------------------------
        def do_GET(self):
            if not self._host_ok():
                return self._json(HTTPStatus.MISDIRECTED_REQUEST, {"error": "unexpected Host header"})
            url = urlsplit(self.path)
            path, q = url.path, {k: v[0] for k, v in parse_qs(url.query).items()}
            if path == "/":
                return self._guard_page()
            if path == "/api/ping":
                return self._json(200, {"teach": True, **info})
            if path == "/api/course":
                return self._guard(lambda: {"subject": runner.subject(), "lessons": runner.course()})
            if path == "/api/lesson":
                return self._guard(lambda: runner.status(q.get("lesson", "")))
            if path == "/api/answers":
                return self._guard(lambda: {"answers": runner.answers_for(q.get("lesson", ""), q.get("prompt"))})
            m = JOB.match(path)
            if m:
                return self._guard(lambda: runner.job(int(m.group(1))))
            if path.startswith("/api/"):
                return self._json(404, {"error": "not found"})
            self._static(path)

        def _guard_page(self):
            try:
                self._send(200, _course_page(runner), "text/html; charset=utf-8")
            except Exception as e:
                traceback.print_exc()
                self._json(500, {"error": f"unexpected error: {e}"})

        def do_POST(self):
            if not self._host_ok():
                return self._json(HTTPStatus.MISDIRECTED_REQUEST, {"error": "unexpected Host header"})
            if not self._origin_ok():
                return self._json(HTTPStatus.FORBIDDEN, {"error": "requests must come from a page this server served"})
            path = urlsplit(self.path).path

            def run():
                b = self._body()
                lesson = str(b.get("lesson", ""))
                if path == "/api/answer":
                    return runner.save_answer(lesson, str(b.get("prompt", "")), str(b.get("answer", "")),
                                              str(b.get("prompt_text", "")))
                if path == "/api/event":
                    runner.record_event(b)
                    return {"ok": True}
                if path == "/api/review":
                    return {"job": runner.start_review(lesson)}
                if path == "/api/draft":
                    return {"job": runner.start_draft(lesson)}
                raise RunnerError("not found")

            self._guard(run)

    return Handler


def serve_lessons(runner: LessonRunner, info: dict, host: str, port: int) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), make_handler(runner, {**info, "host": host}))

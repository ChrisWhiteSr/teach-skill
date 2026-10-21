"""Background jobs for the lesson runner: reviewing saved answers and drafting the next lesson.

Jobs are kept in the course's .teach/jobs.json, so a closed tab, a reload or a restart loses nothing:
the page only polls a job by id. One worker runs one job at a time, so two jobs never write the same
files at once. A job left running by a restart goes back in the queue.
"""
from __future__ import annotations

import json
import threading
import time
import traceback
from typing import Callable

from .files import CourseFiles
from .llm import LLMError

ACTIVE = ("queued", "running")
STATE = ".teach/jobs.json"
KEEP = 200


class JobError(Exception):
    """A failure with a message fit to show the learner. Nothing half-written is left behind."""


class Job:
    def __init__(self, queue: "JobQueue", record: dict):
        self.queue = queue
        self.id = record["id"]
        self.kind = record["kind"]
        self.lesson = record["lesson"]
        self.payload = record.get("payload", {})

    def progress(self, text: str) -> None:
        self.queue._set(self.id, progress=text[:300])


Handler = Callable[[Job], dict]


class JobQueue:
    def __init__(self, files: CourseFiles, handlers: dict[str, Handler]):
        self.files = files
        self.handlers = handlers
        self._lock = threading.RLock()
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.jobs: list[dict] = self._load()
        for j in self.jobs:
            if j["status"] == "running":
                j.update(status="queued", progress="Resuming after a restart")
        self._save()

    # ---- state ------------------------------------------------------------------
    def _load(self) -> list[dict]:
        text, _ = self.files.read(STATE, internal=True)
        try:
            data = json.loads(text) if text.strip() else []
        except json.JSONDecodeError:
            data = []
        return [j for j in data if isinstance(j, dict) and "id" in j] if isinstance(data, list) else []

    def _save(self) -> None:
        with self._lock:
            finished = [j for j in self.jobs if j["status"] not in ACTIVE]
            drop = {j["id"] for j in finished[:-KEEP]} if len(finished) > KEEP else set()
            self.jobs = [j for j in self.jobs if j["id"] not in drop]
            snapshot = json.dumps(self.jobs, indent=1)
        self.files.update(STATE, lambda _old: snapshot, internal=True)

    def _set(self, job_id: int, **fields) -> None:
        with self._lock:
            for j in self.jobs:
                if j["id"] == job_id:
                    j.update(fields, updated=time.time())
            self._save()

    # ---- queries ----------------------------------------------------------------
    def get(self, job_id: int) -> dict | None:
        with self._lock:
            return next((dict(j) for j in self.jobs if j["id"] == job_id), None)

    def latest(self, kind: str, lesson: str, status: str | None = None) -> dict | None:
        with self._lock:
            for j in reversed(self.jobs):
                if j["kind"] == kind and j["lesson"] == lesson and (status is None or j["status"] == status):
                    return dict(j)
        return None

    # ---- queue ------------------------------------------------------------------
    def enqueue(self, kind: str, lesson: str, payload: dict | None = None) -> dict:
        """Queue a job, or return the one already queued or running for the same lesson."""
        if kind not in self.handlers:
            raise ValueError(f"unknown job kind {kind!r}")
        with self._lock:
            for j in self.jobs:
                if j["kind"] == kind and j["lesson"] == lesson and j["status"] in ACTIVE:
                    return dict(j)
            now = time.time()
            job = {"id": max((j["id"] for j in self.jobs), default=0) + 1, "kind": kind, "lesson": lesson,
                   "payload": payload or {}, "status": "queued", "progress": "Waiting to start",
                   "created": now, "updated": now, "attempts": 0, "result": None, "error": None}
            self.jobs.append(job)
            self._save()
        self._wake.set()
        return dict(job)

    def run_one(self) -> bool:
        with self._lock:
            rec = next((j for j in self.jobs if j["status"] == "queued"), None)
            if rec is None:
                return False
            rec.update(status="running", progress="Starting", attempts=rec.get("attempts", 0) + 1, updated=time.time())
            self._save()
            job = Job(self, rec)
        try:
            result = self.handlers[job.kind](job)
            self._set(job.id, status="done", result=result, progress="Done", error=None)
        except (JobError, LLMError) as e:
            self._set(job.id, status="failed", error=str(e)[:500], progress="Stopped")
        except Exception as e:  # unexpected: retry once, then stop with a plain message
            traceback.print_exc()
            again = rec.get("attempts", 1) < 2
            self._set(job.id, status="queued" if again else "failed", progress="Trying once more" if again else "Stopped",
                      error=f"Something went wrong ({type(e).__name__}: {e})"[:500])
        return True

    def run_pending(self) -> None:
        while self.run_one():
            pass

    # ---- worker -----------------------------------------------------------------
    def start(self) -> None:
        if self._thread:
            return
        self._thread = threading.Thread(target=self._loop, name="teach-jobs", daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        while not self._stop.is_set():
            if not self.run_one():
                self._wake.wait(1.0)
                self._wake.clear()

    def stop(self) -> None:
        self._stop.set()
        self._wake.set()
        if self._thread:
            self._thread.join(timeout=5)

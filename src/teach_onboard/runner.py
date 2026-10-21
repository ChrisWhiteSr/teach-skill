"""The lesson runner: one course folder, its HTML lessons, saved answers and background jobs.

Everything it writes goes through files.CourseFiles, so writes stay inside the course folder,
shared files are hash-checked and merged, and HTML is only ever a new, sanitized lesson.
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path

from . import answers as A
from .files import CourseFiles, WriteRefused
from .jobs import JobQueue
from .llm import Provider
from .method import Method

LESSON_FILE = re.compile(r"^(\d{4})-[a-z0-9][a-z0-9-]*\.html$")
MAX_ANSWER = 12000
MAX_PROMPT_TEXT = 2000
AGENT = "teach-onboard serve"


class RunnerError(ValueError):
    """A request the runner refuses, with a message for the learner."""


class LessonRunner:
    def __init__(self, course: Path, provider: Provider, method: Method, agent: str = AGENT, start_worker: bool = True):
        self.files = CourseFiles(course)
        self.root = self.files.root
        if not self.root.is_dir():
            raise RunnerError(f"{self.root} is not a folder")
        self.provider = provider
        self.method = method
        self.agent = agent
        from . import tutor  # late import: tutor uses this module's types

        self.jobs = JobQueue(self.files, {"review": lambda job: tutor.review(self, job),
                                          "draft": lambda job: tutor.draft(self, job)})
        if start_worker:
            self.jobs.start()

    def close(self) -> None:
        self.jobs.stop()

    # ---- lessons ----------------------------------------------------------------
    def lesson_ids(self) -> list[str]:
        d = self.root / "lessons"
        if not d.is_dir():
            return []
        return sorted(p.stem for p in d.iterdir() if p.is_file() and LESSON_FILE.match(p.name))

    def lesson_html(self, lesson: str) -> str:
        if not A.LESSON_ID.match(lesson or "") or lesson not in self.lesson_ids():
            raise RunnerError("unknown lesson")
        return (self.root / "lessons" / f"{lesson}.html").read_text(encoding="utf-8")

    def page(self, lesson: str) -> A.LessonPage:
        return A.read_lesson(lesson, self.lesson_html(lesson))

    def entries(self, lesson: str) -> list[A.Entry]:
        text, _ = self.files.read(A.answers_path(lesson))
        return A.parse(text)

    def subject(self) -> str:
        text, _ = self.files.read("MAP.md")
        m = re.search(r"^# Skill map: (.+)$", text, re.M)
        return m.group(1).strip() if m else self.root.name

    def status(self, lesson: str) -> dict:
        page = self.page(lesson)
        entries = self.entries(lesson)
        latest = {e.prompt: e for e in entries}
        prompts = []
        for p in page.prompts:
            e = latest.get(p.prompt)
            prompts.append({"prompt": p.prompt, "label": p.label, "kind": p.kind, "skill": p.skill,
                            "saved": e is not None, "when": e.when if e else None,
                            "reviewed": bool(e and e.feedback is not None), "judgment": e.judgment if e else None})
        pending = sum(1 for e in entries if e.feedback is None)
        if not entries:
            state = "not_started"
        elif pending:
            state = "answered"
        else:
            state = "reviewed"
        ids = self.lesson_ids()
        i = ids.index(lesson)
        link = lambda lid: {"lesson": lid, "href": f"/lessons/{lid}.html", "title": self.page(lid).title}
        review = self.jobs.latest("review", lesson, "done")
        return {
            "lesson": lesson, "title": page.title, "skill": page.skill, "ai_drafted": page.ai_drafted,
            "prompts": prompts, "answers": len(entries), "pending": pending, "status": state,
            "prev": link(ids[i - 1]) if i > 0 else None, "next": link(ids[i + 1]) if i + 1 < len(ids) else None,
            "course_href": "/",
            "review_job": self.jobs.latest("review", lesson), "draft_job": self.jobs.latest("draft", lesson),
            "last_review": (review or {}).get("result"),
        }

    def course(self) -> list[dict]:
        out = []
        for lid in self.lesson_ids():
            s = self.status(lid)
            out.append({k: s[k] for k in ("lesson", "title", "skill", "status", "answers", "pending", "ai_drafted")})
        return out

    # ---- answers and events -----------------------------------------------------
    def save_answer(self, lesson: str, prompt: str, answer: str, prompt_text: str = "") -> dict:
        page = self.page(lesson)
        box = page.prompt(prompt or "")
        if box is None:
            raise RunnerError("that answer box is not in this lesson")
        answer = (answer or "").strip()
        if not answer:
            raise RunnerError("write an answer first")
        if len(answer) > MAX_ANSWER:
            raise RunnerError(f"answers are limited to {MAX_ANSWER} characters")
        text_of_prompt = (prompt_text or box.text or box.label).strip()[:MAX_PROMPT_TEXT]
        now = datetime.now()
        rel = A.answers_path(lesson)

        def add(text: str) -> str:
            when = A.entry_time(text, prompt, now)
            entry = A.render_entry(prompt, when, text_of_prompt, answer, box.skill, box.kind)
            return A.append_entry(text, entry, lesson, page.title)

        self.files.update(rel, add)
        return {"path": rel, "answers": [e.public() for e in self.entries(lesson) if e.prompt == prompt]}

    def answers_for(self, lesson: str, prompt: str | None = None) -> list[dict]:
        self.page(lesson)  # validates the lesson
        return [e.public() for e in self.entries(lesson) if prompt is None or e.prompt == prompt]

    def record_event(self, event: dict) -> None:
        """Quiz clicks: light evidence only, kept apart from MAP.md (rule 3)."""
        lesson = str(event.get("lesson", ""))
        if not A.LESSON_ID.match(lesson):
            raise RunnerError("unknown lesson")
        rec = {"ts": round(time.time(), 3), "type": str(event.get("type", "quiz"))[:20], "lesson": lesson,
               "quiz": str(event.get("quiz", ""))[:40], "choice": str(event.get("choice", ""))[:200],
               "correct": bool(event.get("correct"))}
        line = json.dumps(rec)
        self.files.update(".teach/events.jsonl", lambda t: t + line + "\n", internal=True)

    # ---- jobs -------------------------------------------------------------------
    def start_review(self, lesson: str) -> dict:
        self.page(lesson)
        if not any(e.feedback is None for e in self.entries(lesson)):
            raise RunnerError("every saved answer already has feedback; save a new answer to get more")
        return self.jobs.enqueue("review", lesson)

    def start_draft(self, lesson: str) -> dict:
        self.page(lesson)
        ids = self.lesson_ids()
        if ids[-1] != lesson:
            raise RunnerError("the next lesson already exists")
        if self.status(lesson)["status"] != "reviewed":
            raise RunnerError("get feedback on this lesson first, so the next one builds on it")
        return self.jobs.enqueue("draft", lesson)

    def job(self, job_id: int) -> dict:
        j = self.jobs.get(job_id)
        if j is None:
            raise RunnerError("unknown job")
        return j


__all__ = ["LessonRunner", "RunnerError", "WriteRefused", "AGENT"]

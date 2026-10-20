"""One onboarding session: subject, mission, map, placement, then a course folder on disk."""
from __future__ import annotations

import secrets
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from . import prompts
from .course import course_path, write_course
from .engine import Result, Skill, drop_skills, next_skill, resolve, summary_counts, validate_map
from .llm import LLMError, Provider
from .method import Method
from .packs import Pack


class FlowError(Exception):
    """A request that doesn't fit the session's current step."""


@dataclass
class Session:
    id: str
    subject: str
    pack: Pack | None = None
    created: float = field(default_factory=time.time)
    answers: dict = field(default_factory=dict)
    follow_up: str = ""
    follow_up_answer: str = ""
    mission: dict | None = None
    skills: list[Skill] = field(default_factory=list)
    resources: list[dict] = field(default_factory=list)
    flagged: set[str] = field(default_factory=set)
    map_confirmed: bool = False
    results: list[Result] = field(default_factory=list)
    current: dict | None = None
    used_bank: dict[str, int] = field(default_factory=dict)
    prefetch: dict[tuple[str, int], Future] = field(default_factory=dict)
    placement_done: bool = False
    saved_to: str = ""
    lock: threading.Lock = field(default_factory=threading.Lock)


class Onboarding:
    def __init__(self, provider: Provider, method: Method, courses_home: Path, packs: dict[str, Pack] | None = None):
        self.provider = provider
        self.method = method
        self.courses_home = courses_home
        self.packs = packs or {}
        self.sessions: dict[str, Session] = {}
        self.pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="prefetch")

    def close(self) -> None:
        self.pool.shutdown(wait=False, cancel_futures=True)

    # ------------------------------------------------------------ helpers

    def get(self, sid: str) -> Session:
        if sid not in self.sessions:
            raise FlowError("unknown session; start again")
        return self.sessions[sid]

    def _skill(self, s: Session, sid: str) -> Skill:
        return next(k for k in s.skills if k.id == sid)

    # ------------------------------------------------------------ steps

    def start(self, subject: str, pack_name: str = "") -> Session:
        pack = None
        if pack_name:
            if pack_name not in self.packs:
                raise FlowError(f"no pack named {pack_name!r}")
            pack = self.packs[pack_name]
            subject = subject.strip() or pack.subject
        subject = " ".join(subject.split())[:120]
        if not subject:
            raise FlowError("say what you want to learn")
        s = Session(id=secrets.token_urlsafe(12), subject=subject, pack=pack)
        self.sessions[s.id] = s
        return s

    def submit_mission(self, s: Session, answers: dict, follow_up_answer: str = "") -> dict:
        with s.lock:
            keep = ("why", "success", "deadline", "background", "minutes")
            s.answers = {k: str(answers.get(k, s.answers.get(k, ""))).strip()[:2000] for k in keep}
            if not s.answers["why"]:
                raise FlowError("tell us why you want to learn this")
            force = bool(s.follow_up)        # one follow-up round at most, then accept the best mission
            fu = (s.follow_up, follow_up_answer) if s.follow_up else None
            if fu:
                s.follow_up_answer = follow_up_answer.strip()[:2000]
            out = self.provider.json(
                task="mission", system=prompts.MISSION_SYSTEM,
                user=prompts.mission_user(s.subject, s.answers, fu, force),
                schema=prompts.MISSION_SCHEMA, effort="medium",
            )
            if not out["acceptable"] and not force:
                s.follow_up = out["follow_up"].strip() or "What will you be able to do once you've learned this?"
                return {"follow_up": s.follow_up}
            mission = out["mission"]
            try:
                minutes = int(s.answers.get("minutes") or self.method.session_minutes)
            except ValueError:
                minutes = self.method.session_minutes
            mission["session_minutes"] = max(5, min(minutes, 180))
            s.mission = mission
            return {"mission": mission}

    def draft_map(self, s: Session) -> dict:
        with s.lock:
            if not s.mission:
                raise FlowError("finish the mission step first")
            if s.pack:
                s.skills = [Skill(k.id, k.text, list(k.needs)) for k in s.pack.skills]
                s.resources = list(s.pack.resources)
            elif not s.skills:
                problems: list[str] | None = None
                for _ in range(2):
                    out = self.provider.json(
                        task="map", system=prompts.map_system(self.method, s.mission.get("session_minutes", self.method.session_minutes)),
                        user=prompts.map_user(s.subject, s.mission, s.answers.get("background", ""), problems),
                        schema=prompts.MAP_SCHEMA, effort="high",
                    )
                    skills = [Skill(k["id"].strip(), k["skill"].strip(), [n.strip() for n in k["needs"]]) for k in out["skills"]]
                    problems = validate_map(skills, self.method)
                    if not problems:
                        s.skills, s.resources = skills, out["resources"]
                        break
                else:
                    raise LLMError("the drafted map had problems twice: " + "; ".join(problems or []))
            return self.map_view(s)

    def map_view(self, s: Session) -> dict:
        return {
            "skills": [{"id": k.id, "skill": k.text, "needs": k.needs} for k in s.skills],
            "resources": s.resources,
            "flagged": sorted(s.flagged),
            "from_pack": bool(s.pack),
        }

    def set_map(self, s: Session, skills: list[dict], drop: list[str], flagged: list[str]) -> dict:
        with s.lock:
            if s.results:
                raise FlowError("placement has started; the map is fixed now")
            edited = [Skill(str(k["id"]), " ".join(str(k["skill"]).split())[:300], [str(n) for n in k.get("needs", [])])
                      for k in skills]
            edited = drop_skills(edited, set(drop))
            errors = validate_map(edited, self.method)
            if errors:
                raise FlowError("; ".join(errors))
            s.skills = edited
            s.flagged = {f for f in flagged if any(k.id == f for k in edited)}
            s.map_confirmed = True
            first = next_skill(s.skills, [], self.method, s.flagged)
            if first:
                self._prefetch(s, first, [])
            return self.map_view(s)

    def next_item(self, s: Session) -> dict:
        with s.lock:
            if not s.map_confirmed:
                raise FlowError("confirm the map first")
            if s.current:
                return self._item_view(s)
            sid = None if s.placement_done else next_skill(s.skills, s.results, self.method, s.flagged)
            if sid is None:
                s.placement_done = True
                return {"done": True}
            item = self._bank_item(s, sid)
            if item is None:
                previous = [r.question for r in s.results if r.skill_id == sid]
                fut = s.prefetch.pop((sid, len(previous)), None)
                try:
                    item = fut.result() if fut else None
                except Exception:
                    item = None          # a failed prefetch is retried in the foreground
                item = item or self._write_item(s, sid, previous)
            s.current = {"skill_id": sid, **item}
            self._prefetch_branches(s)
            return self._item_view(s)

    def _write_item(self, s: Session, sid: str, previous: list[str]) -> dict:
        skill = self._skill(s, sid)
        prereqs = [self._skill(s, n) for n in skill.needs]
        return self.provider.json(
            task="item", system=prompts.ITEM_SYSTEM,
            user=prompts.item_user(s.subject, s.mission or {}, skill, prereqs, previous),
            schema=prompts.ITEM_SCHEMA, effort="low",
        )

    def _prefetch(self, s: Session, sid: str, previous: list[str]) -> None:
        key = (sid, len(previous))
        if key not in s.prefetch and not self._has_bank(s, sid):
            s.prefetch[key] = self.pool.submit(self._write_item, s, sid, list(previous))

    def _prefetch_branches(self, s: Session) -> None:
        """While the learner answers, write the next question for both outcomes, so only grading is left to wait for."""
        cur = s.current
        for correct in (True, False):
            hyp = s.results + [Result(cur["skill_id"], cur["question"], "", "", correct)]
            nsid = next_skill(s.skills, hyp, self.method, s.flagged)
            if nsid:
                self._prefetch(s, nsid, [r.question for r in hyp if r.skill_id == nsid])

    def _has_bank(self, s: Session, sid: str) -> bool:
        if not s.pack or sid not in s.pack.items:
            return False
        original = next((pk for pk in s.pack.skills if pk.id == sid), None)
        return bool(original and original.text == self._skill(s, sid).text
                    and s.used_bank.get(sid, 0) < len(s.pack.items[sid]))

    def _bank_item(self, s: Session, sid: str) -> dict | None:
        """The next unused bank question for this skill, unless the learner rewrote the skill."""
        if not self._has_bank(s, sid):
            return None
        i = s.used_bank.get(sid, 0)
        s.used_bank[sid] = i + 1
        return dict(s.pack.items[sid][i])

    def _item_view(self, s: Session) -> dict:
        return {"done": False, "number": len(s.results) + 1, "max": self.method.placement_max_items,
                "question": s.current["question"]}

    def answer(self, s: Session, answer: str, dont_know: bool) -> dict:
        with s.lock:
            if not s.current:
                raise FlowError("there is no open question")
            cur = s.current
            answer = answer.strip()[:4000]
            if dont_know or not answer:
                correct, feedback, dont_know = False, f"Model answer: {cur['answer']}", True
            else:
                g = self.provider.json(
                    task="grade", system=prompts.GRADE_SYSTEM,
                    user=prompts.grade_user(cur["question"], cur["answer"], cur["rubric"], answer),
                    schema=prompts.GRADE_SCHEMA, effort="low",
                )
                correct, feedback = bool(g["correct"]), g["feedback"]
            s.results.append(Result(cur["skill_id"], cur["question"], answer, cur["answer"], correct, dont_know, feedback))
            s.current = None
            return {"correct": correct}

    def dispute(self, s: Session, index: int) -> dict:
        with s.lock:
            if not (0 <= index < len(s.results)):
                raise FlowError("no such answer")
            r = s.results[index]
            if r.dont_know:
                raise FlowError("an 'I don't know' can't be regraded")
            r.correct, r.disputed = True, True
            return self.summary(s)

    def summary(self, s: Session) -> dict:
        statuses = resolve(s.skills, s.results, self.method)
        return {
            "subject": s.subject,
            "counts": summary_counts(statuses),
            "skills": [{"id": k.id, "skill": k.text, "needs": k.needs, "status": statuses[k.id].status,
                        "source": statuses[k.id].source, "inferred_from": statuses[k.id].inferred_from}
                       for k in s.skills],
            "answers": [{"index": i, "skill_id": r.skill_id, "question": r.question, "answer": r.answer,
                         "key": r.key, "correct": r.correct, "dont_know": r.dont_know, "feedback": r.feedback,
                         "disputed": r.disputed} for i, r in enumerate(s.results)],
            "saved_to": s.saved_to,
        }

    def finish(self, s: Session, today: date | None = None) -> dict:
        with s.lock:
            if not s.placement_done:
                raise FlowError("placement isn't finished")
            if s.saved_to:
                return {"path": s.saved_to}
            statuses = resolve(s.skills, s.results, self.method)
            path = course_path(self.courses_home, s.subject)
            minutes = max(1, round((time.time() - s.created) / 60))
            write_course(
                path, subject=s.subject, mission=s.mission or {}, skills=s.skills, statuses=statuses,
                results=s.results, resources=s.resources, resources_verified=bool(s.pack),
                background=s.answers.get("background", ""), method=self.method, minutes=minutes,
                today=today, source=s.pack.name if s.pack else "",
            )
            s.saved_to = str(path)
            return {"path": s.saved_to}

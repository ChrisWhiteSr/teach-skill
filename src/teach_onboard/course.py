"""Write a course folder in the formats the teach skill reads (skill/references/*-format.md)."""
from __future__ import annotations

import json
import re
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path

from .engine import Result, Skill, SkillStatus, summary_counts
from .method import Method


class CourseExists(Exception):
    pass


def slugify(subject: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", subject.lower()).strip("-")
    return slug[:60].strip("-") or "course"


def course_path(courses_home: Path, subject: str) -> Path:
    home = courses_home.expanduser().resolve()
    path = (home / slugify(subject)).resolve()
    if home not in path.parents:
        raise ValueError("course path escapes the courses home")
    return path


def _cell(text: str) -> str:
    return " ".join(str(text).split()).replace("|", "/")


def _bullets(items: list[str], empty: str) -> str:
    items = [i.strip() for i in items if i and i.strip()]
    return "\n".join(f"- {i}" for i in items) if items else f"- {empty}"


def render_mission(subject: str, mission: dict, session_minutes: int) -> str:
    constraints = [f"Session length: {session_minutes} minutes"]
    if mission.get("deadline"):
        constraints.append(f"Deadline: {mission['deadline']}")
    constraints += mission.get("constraints", [])
    return (
        f"# Mission: {mission.get('title') or subject}\n\n"
        f"## Why\n{mission['why'].strip()}\n\n"
        f"## Success looks like\n{_bullets(mission.get('success', []), 'To be agreed in the first session')}\n\n"
        f"## Constraints\n{_bullets(constraints, 'None stated')}\n\n"
        f"## Out of scope\n{_bullets(mission.get('out_of_scope', []), 'Nothing ruled out yet')}\n"
    )


def render_map(
    subject: str, skills: list[Skill], statuses: dict[str, SkillStatus], results: list[Result],
    method: Method, today: date,
) -> str:
    rows = []
    for s in skills:
        st = statuses[s.id]
        needs = ", ".join(s.needs) or "-"
        if st.status == "mastered":
            step = method.inferred_start_step if st.source == "inferred" else method.tested_start_step
            nxt = (today + timedelta(days=method.interval_for_step(step))).isoformat()
            best = f"inferred from {st.inferred_from}" if st.source == "inferred" else f"placement {st.correct}/{st.correct + st.missed}"
            rows.append(f"| {s.id} | {_cell(s.text)} | {needs} | mastered | {best} | {today.isoformat()} | {step} | {nxt} |")
        elif st.source == "tested":
            rows.append(f"| {s.id} | {_cell(s.text)} | {needs} | {st.status} | placement {st.correct}/{st.correct + st.missed} | {today.isoformat()} | - | - |")
        else:
            rows.append(f"| {s.id} | {_cell(s.text)} | {needs} | new | - | - | - | - |")

    missed = []
    for r in results:
        if not r.correct:
            said = "I don't know" if r.dont_know else _cell(r.answer)[:200]
            missed.append(f"- {r.skill_id} ({today.isoformat()}): {_cell(r.question)} Answered: {said}")

    return (
        f"# Skill map: {subject}\n\n"
        f"Mission: [[MISSION]] · Updated: {today.isoformat()} by onboarding (placement)\n\n"
        "| ID | Skill (the learner can…) | Needs | Status | Best check | Last | Step | Next review |\n"
        "|---|---|---|---|---|---|---|---|\n"
        + "\n".join(rows)
        + "\n\n## Missed items\n"
        + ("\n".join(missed) if missed else "- None from placement.")
        + "\n\n## Holes\n- None found yet.\n"
    )


def render_resources(subject: str, resources: list[dict], verified: bool) -> str:
    tag = "" if verified else " #needs-verification"
    knowledge, communities = [], []
    for r in resources:
        title = _cell(r.get("title", "")).strip()
        if not title:
            continue
        url = (r.get("url") or "").strip()
        head = f"[{title}]({url})" if url else title
        line = f"- {head}{tag}\n  {_cell(r.get('use', ''))}"
        (communities if r.get("kind") == "community" else knowledge).append(line)
    note = "" if verified else (
        "\nDrafted by a model during onboarding, without web search. Each source is tagged "
        "#needs-verification: check it before a lesson cites it, then remove the tag.\n"
    )
    return (
        f"# {subject} Resources\n{note}\n"
        "## Knowledge\n\n" + ("\n".join(knowledge) or "- None yet.") + "\n\n"
        "## Wisdom (Communities)\n\n" + ("\n".join(communities) or "- None yet.") + "\n"
    )


def render_log(subject: str, today: date, minutes: int, statuses: dict[str, SkillStatus], n_items: int) -> str:
    c = summary_counts(statuses)
    note = (f"placement, {n_items} items: {c['mastered_tested']} mastered by test, "
            f"{c['mastered_inferred']} by inference, {c['learning']} learning, {c['new']} new")
    return (
        f"# Session log: {subject}\n\n"
        "| Date | Agent | Minutes | XP | Reviews | Check | Taught | Note |\n"
        "|---|---|---|---|---|---|---|---|\n"
        f"| {today.isoformat()} | onboarding | {minutes} | - | - | placement | - | {note} |\n"
    )


def write_course(
    path: Path, *, subject: str, mission: dict, skills: list[Skill], statuses: dict[str, SkillStatus],
    results: list[Result], resources: list[dict], resources_verified: bool, background: str,
    method: Method, minutes: int, today: date | None = None, source: str = "",
) -> list[Path]:
    today = today or date.today()
    if path.exists() and any(path.iterdir()):
        raise CourseExists(f"{path} already holds files; pick another subject name or move that folder")
    path.mkdir(parents=True, exist_ok=True)
    session_minutes = int(mission.get("session_minutes") or method.session_minutes)

    files: dict[str, str] = {
        "MISSION.md": render_mission(subject, mission, session_minutes),
        "MAP.md": render_map(subject, skills, statuses, results, method, today),
        "RESOURCES.md": render_resources(subject, resources, resources_verified),
        "LOG.md": render_log(subject, today, minutes, statuses, len(results)),
        "NOTES.md": (
            f"# Notes\n\n- Course set up with the onboarding app on {today.isoformat()}"
            + (f" from the `{source}` pack" if source else "") + ".\n"
        ),
    }
    if background.strip():
        files["learning-records/0001-stated-background.md"] = (
            "# Stated background\n\n"
            f"At onboarding the learner described their background: \"{' '.join(background.split())}\"\n\n"
            "**Evidence:** placement on the same day tested these claims; `MAP.md` holds the result.\n"
        )
    files[".teach/placement.json"] = json.dumps({
        "date": today.isoformat(),
        "subject": subject,
        "mission": mission,
        "skills": [asdict(s) for s in skills],
        "results": [asdict(r) for r in results],
        "statuses": {k: asdict(v) for k, v in statuses.items()},
    }, indent=2)

    written = []
    for rel, text in files.items():
        p = path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        written.append(p)
    return written

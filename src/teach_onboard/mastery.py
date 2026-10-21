"""Turn judged answers into MAP.md changes, by the skill's rules. Code decides; the model only judges.

- Partial counts as a miss when scoring. Only the first answer to a check or review prompt is fresh.
- A mastery check needs every check box for the skill in the lesson answered and judged, at least
  mastery_min_items of them, scored at mastery_threshold or better.
- A review item on a mastered skill is a review: all correct moves it one step; any miss sends it back to learning.
- Practice moves a new skill to learning and nothing else. Quiz clicks never reach this module.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta

from .answers import Entry, LessonPage
from .method import Method


@dataclass
class Outcome:
    skill: str
    kind: str                     # check | review | practice
    correct: int = 0
    total: int = 0
    misses: list[Entry] = field(default_factory=list)


def evaluate(page: LessonPage, entries: list[Entry], judged_now: set[tuple[str, str]], method: Method) -> list[Outcome]:
    """Outcomes for the skills touched by the answers judged in this review."""
    first: dict[str, Entry] = {}
    for e in entries:
        first.setdefault(e.prompt, e)
    by_prompt = {p.prompt: p for p in page.prompts}
    touched = [e for e in entries if e.key in judged_now and e.judgment]
    outcomes: dict[tuple[str, str], Outcome] = {}

    def outcome(skill: str, kind: str) -> Outcome:
        return outcomes.setdefault((skill, kind), Outcome(skill, kind))

    for kind in ("check", "review"):
        skills = {by_prompt[e.prompt].skill for e in touched
                  if e.prompt in by_prompt and by_prompt[e.prompt].kind == kind and first.get(e.prompt) is e}
        for skill in sorted(s for s in skills if s):
            boxes = [p for p in page.prompts if p.kind == kind and p.skill == skill]
            firsts = [first.get(p.prompt) for p in boxes]
            if not all(f is not None and f.judgment for f in firsts):
                outcome(skill, "practice")           # incomplete: wait for the rest before scoring
                continue
            if kind == "check" and len(boxes) < method.mastery_min_items:
                outcome(skill, "practice")           # too few items to be a mastery check
                continue
            o = outcome(skill, kind)
            o.total = len(firsts)
            o.correct = sum(1 for f in firsts if f.judgment == "correct")
            o.misses = [f for f in firsts if f.judgment != "correct"]

    for e in touched:
        p = by_prompt.get(e.prompt)
        if p and p.skill and (p.kind == "practice" or first.get(e.prompt) is not e):
            outcome(p.skill, "practice")
    return list(outcomes.values())


# ---- MAP.md ------------------------------------------------------------------------

ROW = re.compile(r"^\|\s*(S\d+[a-z]?)\s*\|")


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def _score(best: str) -> float:
    m = re.fullmatch(r"(\d+)/(\d+)", best.strip())
    return int(m.group(1)) / int(m.group(2)) if m and int(m.group(2)) else -1.0


def _flat(s: str, n: int = 200) -> str:
    s = " ".join(s.split()).replace("|", "/")
    return s if len(s) <= n else s[: n - 3].rstrip() + "..."


def apply(map_text: str, outcomes: list[Outcome], today: date, method: Method, agent: str) -> tuple[str, list[str]]:
    """Return the new MAP.md text and a plain list of what changed. Pure, so it can be re-run on a newer MAP.md."""
    lines = map_text.splitlines()
    rows = {m.group(1): i for i, line in enumerate(lines) if (m := ROW.match(line))}
    changes: list[str] = []
    missed: list[str] = []
    clear_missed: set[str] = set()
    day = today.isoformat()
    by_skill: dict[str, list[Outcome]] = {}
    for o in outcomes:
        by_skill.setdefault(o.skill, []).append(o)

    for skill, outs in by_skill.items():
        if skill not in rows:
            changes.append(f"{skill} is not in MAP.md, so it was left alone")
            continue
        i = rows[skill]
        c = _cells(lines[i])
        if len(c) < 8:
            changes.append(f"{skill}: the MAP.md row has an unexpected shape, so it was left alone")
            continue
        status, best, step = c[3], c[4], c[6]
        kinds = {o.kind: o for o in outs}
        if "check" in kinds:
            o = kinds["check"]
            score = f"{o.correct}/{o.total}"
            if o.total and o.correct / o.total >= method.mastery_threshold - 1e-9:
                c[3], c[5], c[6] = "mastered", day, "0"
                c[7] = (today + timedelta(days=method.interval_for_step(0))).isoformat()
                clear_missed.add(skill)
                changes.append(f"{skill} mastered: check {score}; first review {c[7]}")
            else:
                c[3], c[5], c[6], c[7] = "learning", day, "-", "-"
                changes.append(f"{skill} still learning: check {score}, below {round(method.mastery_threshold * 100)}%")
            if _score(score) > _score(best):
                c[4] = score
            missed += [f"- {skill} ({day}): {_flat(m.prompt_text)} Answered: {_flat(m.answer)} ({m.judgment})" for m in o.misses]
        elif "review" in kinds and status == "mastered":
            o = kinds["review"]
            if o.correct == o.total:
                new_step = (int(step) + 1) if step.isdigit() else 0
                c[5], c[6] = day, str(new_step)
                c[7] = (today + timedelta(days=method.interval_for_step(new_step))).isoformat()
                changes.append(f"{skill} review passed ({o.correct}/{o.total}); next review {c[7]}")
            else:
                c[3], c[5], c[6], c[7] = "learning", day, "-", "-"
                missed += [f"- {skill} ({day}): {_flat(m.prompt_text)} Answered: {_flat(m.answer)} ({m.judgment})" for m in o.misses]
                changes.append(f"{skill} review missed ({o.correct}/{o.total}); back to learning")
        elif status == "new":
            c[3], c[5] = "learning", day
            changes.append(f"{skill} now learning (practice answers)")
        lines[i] = _row(c)

    if not changes:
        return map_text, []
    text = "\n".join(lines) + ("\n" if map_text.endswith("\n") else "")
    text = re.sub(r"Updated: [^\n]*", f"Updated: {day} by {agent}", text, count=1)
    text = _edit_missed(text, missed, clear_missed)
    return text, changes


def _edit_missed(text: str, add: list[str], clear: set[str]) -> str:
    if not add and not clear:
        return text
    m = re.search(r"^## Missed items[^\n]*\n", text, re.M)
    if not m:
        return text.rstrip("\n") + "\n\n## Missed items\n" + "\n".join(add) + "\n" if add else text
    start = m.end()
    nxt = re.search(r"^## ", text[start:], re.M)
    end = start + nxt.start() if nxt else len(text)
    items = [line for line in text[start:end].splitlines() if line.strip()]
    items = [line for line in items if not re.match(r"^- None\b", line)]
    items = [line for line in items if not any(line.startswith(f"- {s} (") for s in clear)]
    items += [a for a in add if a not in items]
    block = "\n".join(items or ["- None."]) + "\n" + ("\n" if nxt else "")
    return text[:start] + block + text[end:]


def next_skill(map_text: str) -> tuple[str, str] | None:
    """The first skill not mastered whose prerequisites all are (the Orient rule in SKILL.md)."""
    rows = [_cells(line) for line in map_text.splitlines() if ROW.match(line)]
    status = {c[0]: c[3] for c in rows if len(c) >= 4}
    for c in rows:
        if len(c) >= 4 and c[3] != "mastered":
            needs = [n.strip() for n in c[2].split(",") if n.strip() not in ("", "-")]
            if all(status.get(n) == "mastered" for n in needs):
                return c[0], c[1]
    return None

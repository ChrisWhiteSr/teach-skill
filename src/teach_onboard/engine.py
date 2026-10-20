"""Placement logic. Pure functions over the skill map and the answers so far.

The model writes questions and grades answers. Everything that decides where a learner
starts lives here, in code, so the method's rules cannot drift with a prompt.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from statistics import median_low

from .method import Method

ID_RE = re.compile(r"^S\d+[a-z]?$")


@dataclass
class Skill:
    id: str
    text: str
    needs: list[str] = field(default_factory=list)


@dataclass
class Result:
    skill_id: str
    question: str
    answer: str
    key: str
    correct: bool
    dont_know: bool = False
    feedback: str = ""
    disputed: bool = False


@dataclass
class SkillStatus:
    status: str                 # mastered | learning | new
    source: str = ""            # tested | inferred | "" (untested)
    correct: int = 0
    missed: int = 0
    inferred_from: str = ""


# ---------------------------------------------------------------- map structure

def validate_map(skills: list[Skill], method: Method | None = None) -> list[str]:
    errors: list[str] = []
    if not skills:
        return ["the map has no skills"]
    ids = [s.id for s in skills]
    seen: set[str] = set()
    for s in skills:
        if not ID_RE.match(s.id):
            errors.append(f"{s.id}: ids look like S1, S2, S2a")
        if s.id in seen:
            errors.append(f"{s.id}: duplicate id")
        seen.add(s.id)
        if not s.text.strip():
            errors.append(f"{s.id}: the skill has no text")
        for n in s.needs:
            if n == s.id:
                errors.append(f"{s.id}: a skill cannot need itself")
            elif n not in ids:
                errors.append(f"{s.id}: needs {n}, which is not on the map")
    if not errors and _has_cycle(skills):
        errors.append("the prerequisites loop back on themselves")
    if method and not errors and len(skills) > method.map_max_skills:
        errors.append(f"the map has {len(skills)} skills; keep it to {method.map_max_skills} or fewer")
    return errors


def _has_cycle(skills: list[Skill]) -> bool:
    graph = {s.id: s.needs for s in skills}
    state: dict[str, int] = {}

    def visit(n: str) -> bool:
        if state.get(n) == 1:
            return True
        if state.get(n) == 2:
            return False
        state[n] = 1
        if any(visit(m) for m in graph.get(n, [])):
            return True
        state[n] = 2
        return False

    return any(visit(s.id) for s in skills)


def depths(skills: list[Skill]) -> dict[str, int]:
    graph = {s.id: s.needs for s in skills}
    memo: dict[str, int] = {}

    def depth(n: str) -> int:
        if n not in memo:
            needs = graph.get(n, [])
            memo[n] = 0 if not needs else 1 + max(depth(m) for m in needs)
        return memo[n]

    return {s.id: depth(s.id) for s in skills}


def ancestors(skills: list[Skill], sid: str) -> set[str]:
    graph = {s.id: s.needs for s in skills}
    out: set[str] = set()
    stack = list(graph.get(sid, []))
    while stack:
        n = stack.pop()
        if n not in out:
            out.add(n)
            stack.extend(graph.get(n, []))
    return out


def descendants(skills: list[Skill], sid: str) -> set[str]:
    return {s.id for s in skills if sid in ancestors(skills, s.id)}


def drop_skills(skills: list[Skill], drop: set[str]) -> list[Skill]:
    """Remove skills and any prerequisite links that pointed at them."""
    return [Skill(s.id, s.text, [n for n in s.needs if n not in drop]) for s in skills if s.id not in drop]


# ---------------------------------------------------------------- placement

def tally(results: list[Result]) -> dict[str, tuple[int, int]]:
    out: dict[str, tuple[int, int]] = {}
    for r in results:
        c, m = out.get(r.skill_id, (0, 0))
        out[r.skill_id] = (c + 1, m) if r.correct else (c, m + 1)
    return out


def _tested_mastered(counts: tuple[int, int], method: Method) -> bool:
    c, m = counts
    return c >= method.correct_to_place and m == 0


def resolve(skills: list[Skill], results: list[Result], method: Method) -> dict[str, SkillStatus]:
    """Final status of every skill from the answers so far.

    Tested evidence always wins. An untested skill counts as mastered by inference when a skill
    that depends on it was placed as mastered; its first review then confirms or demotes it.
    """
    t = tally(results)
    out: dict[str, SkillStatus] = {}
    mastered_tested = [sid for sid, cm in t.items() if _tested_mastered(cm, method)]
    order = {s.id: i for i, s in enumerate(skills)}
    for s in skills:
        if s.id in t:
            c, m = t[s.id]
            if _tested_mastered((c, m), method):
                out[s.id] = SkillStatus("mastered", "tested", c, m)
            elif c >= 1:
                out[s.id] = SkillStatus("learning", "tested", c, m)
            else:
                out[s.id] = SkillStatus("new", "tested", c, m)
            continue
        sources = sorted((d for d in mastered_tested if s.id in ancestors(skills, d)), key=lambda d: order.get(d, 0))
        if sources:
            out[s.id] = SkillStatus("mastered", "inferred", inferred_from=sources[0])
        else:
            out[s.id] = SkillStatus("new")
    return out


def next_skill(
    skills: list[Skill], results: list[Result], method: Method, flagged: set[str] | frozenset[str] = frozenset()
) -> str | None:
    """Which skill the next placement question should test, or None when placement is done."""
    if len(results) >= method.placement_max_items:
        return None
    t = tally(results)

    # One correct answer is not enough to place a skill: confirm it with a second item.
    if results:
        last = results[-1].skill_id
        c, m = t[last]
        if m == 0 and 0 < c < method.correct_to_place:
            return last

    statuses = resolve(skills, results, method)
    resolved = set(t)
    resolved |= {sid for sid, st in statuses.items() if st.source == "inferred"}
    for sid, cm in t.items():
        if not _tested_mastered(cm, method):
            resolved |= descendants(skills, sid)   # can't place above a missing prerequisite

    unresolved = [s for s in skills if s.id not in resolved]
    if not unresolved:
        # Everything is placed. If that took very few questions, spot-check skills that were only inferred.
        if len(results) < method.placement_min_items:
            unresolved = [s for s in skills if statuses[s.id].source == "inferred"]
        if not unresolved:
            return None

    pool = unresolved
    if results:
        last = results[-1].skill_id
        if _tested_mastered(t[last], method):
            up = descendants(skills, last)
            pool = [s for s in unresolved if s.id in up] or unresolved
        else:
            down = ancestors(skills, last)
            pool = [s for s in unresolved if s.id in down] or unresolved

    d = depths(skills)
    target = median_low(sorted(d[s.id] for s in pool))
    order = {s.id: i for i, s in enumerate(skills)}
    best = min(pool, key=lambda s: (abs(d[s.id] - target), 0 if s.id in flagged else 1, order[s.id]))
    return best.id


def summary_counts(statuses: dict[str, SkillStatus]) -> dict[str, int]:
    out = {"mastered_tested": 0, "mastered_inferred": 0, "learning": 0, "new": 0}
    for st in statuses.values():
        if st.status == "mastered":
            out["mastered_inferred" if st.source == "inferred" else "mastered_tested"] += 1
        else:
            out[st.status] += 1
    return out

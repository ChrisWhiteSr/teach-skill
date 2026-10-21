"""The answers file (skill/references/answers-format.md) and the parts of a lesson page the runner reads.

Pure text functions: parse an answers file, append an entry, write feedback in place, and read a lesson's
title, skill and answer boxes from its HTML. Nothing here touches the disk.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from html import unescape

JUDGMENTS = ("correct", "partial", "incorrect")
KINDS = ("practice", "check", "review")
WAITING = "*Waiting for teacher feedback.*"
PROMPT_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,60}$")
LESSON_ID = re.compile(r"^\d{4}-[a-z0-9][a-z0-9-]{0,60}$")
ENTRY = re.compile(r"^## Answer · (?P<prompt>[a-z0-9][a-z0-9-]*) · (?P<when>[^\n]+?)\s*$", re.M)
FEEDBACK = re.compile(r"^\*\*Teacher feedback\*\*", re.M)


def answers_path(lesson: str) -> str:
    return f"answers/{lesson}.md"


@dataclass
class Entry:
    prompt: str
    when: str
    answer: str
    prompt_text: str = ""
    skill: str = ""
    kind: str = "practice"
    feedback: str | None = None
    feedback_by: str | None = None
    feedback_date: str | None = None
    judgment: str | None = None

    @property
    def key(self) -> tuple[str, str]:
        return (self.prompt, self.when)

    def public(self) -> dict:
        return {"prompt": self.prompt, "when": self.when, "answer": self.answer, "skill": self.skill, "kind": self.kind,
                "feedback": self.feedback, "feedback_by": self.feedback_by, "feedback_date": self.feedback_date,
                "judgment": self.judgment}


def _quote(text: str) -> str:
    return "\n".join("> " + line if line.strip() else ">" for line in text.strip().splitlines())


def _unquote(block: str) -> str:
    return "\n".join(re.sub(r"^> ?", "", line) for line in block.strip().splitlines()).strip()


def _section(body: str, label: str) -> str:
    m = re.search(rf"^\*\*{label}\*\*\s*\n\n(?P<q>(?:>.*(?:\n|$))+)", body, re.M)
    return _unquote(m.group("q")) if m else ""


def header(lesson: str, title: str) -> str:
    return (
        f"# Answers: {title}\n\n"
        f"Answers saved from `lessons/{lesson}.html`, newest last.\n"
        "Teachers: write feedback under an answer by replacing its waiting line. "
        "The format is in the teach skill's `references/answers-format.md`.\n"
    )


def render_entry(prompt: str, when: str, prompt_text: str, answer: str, skill: str, kind: str) -> str:
    return (
        f"## Answer · {prompt} · {when}\n\n"
        f"Skill: {skill or '-'} · Kind: {kind}\n\n"
        f"**Prompt**\n\n{_quote(prompt_text) or '>'}\n\n"
        f"**Answer**\n\n{_quote(answer)}\n\n"
        f"{WAITING}\n"
    )


def append_entry(text: str, entry: str, lesson: str, title: str) -> str:
    """Add an entry at the end, creating the header when the file is new. Safe to re-run on newer text."""
    base = text if text.strip() else header(lesson, title)
    return base.rstrip("\n") + "\n\n" + entry


def entry_time(text: str, prompt: str, now: datetime) -> str:
    """Minutes are enough, unless this prompt already has an entry in the same minute."""
    when = now.strftime("%Y-%m-%d %H:%M")
    taken = {e.when for e in parse(text) if e.prompt == prompt}
    return now.strftime("%Y-%m-%d %H:%M:%S") if when in taken else when


def parse_feedback(raw: str) -> dict:
    """Split '(date, teacher[, model]): **Judgment: partial.** ...' into its parts."""
    raw = raw.strip(" :\n")
    by = day = None
    m = re.match(r"\(([^)]*)\)\s*:?\s*", raw)
    if m:
        bits = [b.strip() for b in m.group(1).split(",") if b.strip()]
        if bits and re.fullmatch(r"\d{4}-\d{2}-\d{2}", bits[0]):
            day, bits = bits[0], bits[1:]
        by = ", ".join(bits) or None
        raw = raw[m.end():]
    j = re.match(r"\**\s*Judgment:\s*(correct|partial|incorrect)\s*\.?\s*\**\s*", raw, re.I)
    judgment = j.group(1).lower() if j else None
    if j:
        raw = raw[j.end():]
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", raw).strip()
    return {"feedback": text, "feedback_by": by, "feedback_date": day, "judgment": judgment}


def parse(text: str) -> list[Entry]:
    marks = list(ENTRY.finditer(text))
    out = []
    for i, m in enumerate(marks):
        body = text[m.end(): marks[i + 1].start() if i + 1 < len(marks) else len(text)]
        meta = re.search(r"^Skill:\s*(?P<skill>\S+)\s*·\s*Kind:\s*(?P<kind>[a-z]+)", body, re.M)
        fb = FEEDBACK.search(body)
        e = Entry(
            prompt=m.group("prompt"), when=m.group("when").strip(),
            answer=_section(body, "Answer"), prompt_text=_section(body, "Prompt"),
            skill=(meta.group("skill") if meta and meta.group("skill") != "-" else ""),
            kind=(meta.group("kind") if meta and meta.group("kind") in KINDS else "practice"),
        )
        if fb:
            parts = parse_feedback(body[fb.end():])
            e.feedback, e.feedback_by, e.feedback_date, e.judgment = (
                parts["feedback"], parts["feedback_by"], parts["feedback_date"], parts["judgment"])
        out.append(e)
    return out


def pending(text: str) -> list[Entry]:
    return [e for e in parse(text) if e.feedback is None]


def _one_paragraph(s: str) -> str:
    return re.sub(r"\n\s*\n+", "\n", s.strip())


def feedback_block(day: str, teacher: str, judgment: str, right: str, fix: str, next_step: str) -> str:
    if judgment not in JUDGMENTS:
        raise ValueError(f"judgment must be one of {', '.join(JUDGMENTS)}")
    parts = [f"**Teacher feedback** ({day}, {teacher}): **Judgment: {judgment}.**"]
    for label, value in (("What you got right", right), ("What to add or fix", fix), ("Smallest next step", next_step)):
        if value and value.strip():
            parts.append(f"{label}: {_one_paragraph(value)}")
    return "\n\n".join(parts) + "\n"


def apply_feedback(text: str, blocks: dict[tuple[str, str], str]) -> tuple[str, int]:
    """Replace the waiting line of each entry keyed (prompt, when). Entries that already have feedback are left alone."""
    marks = list(ENTRY.finditer(text))
    out, last, n = [], 0, 0
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        body = text[m.start():end]
        key = (m.group("prompt"), m.group("when").strip())
        if key in blocks and WAITING in body and not FEEDBACK.search(body):
            body = body.replace(WAITING + "\n", blocks[key], 1) if WAITING + "\n" in body else body.replace(WAITING, blocks[key].rstrip("\n"), 1)
            n += 1
        out.append(text[last:m.start()] + body)
        last = end
    out.append(text[last:])
    return "".join(out), n


# ---- reading a lesson page --------------------------------------------------------

def _text(html: str) -> str:
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", html)).split())


def _attr(tag: str, name: str) -> str | None:
    m = re.search(rf"""\b{name}\s*=\s*(?:"([^"]*)"|'([^']*)')""", tag, re.I)
    return unescape(m.group(1) if m.group(1) is not None else m.group(2)) if m else None


@dataclass
class Prompt:
    prompt: str
    label: str
    kind: str = "practice"
    skill: str = ""
    text: str = ""


@dataclass
class LessonPage:
    lesson: str
    title: str
    skill: str
    prompts: list[Prompt] = field(default_factory=list)
    ai_drafted: str | None = None

    def prompt(self, pid: str) -> Prompt | None:
        return next((p for p in self.prompts if p.prompt == pid), None)


def read_lesson(lesson: str, html: str) -> LessonPage:
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S | re.I)
    title = _text(h1.group(1)) if h1 else lesson
    main = re.search(r"<main\b[^>]*>", html, re.I)
    skill = (_attr(main.group(0), "data-skill") or "") if main else ""
    if not skill:
        m = re.search(r"\b(S\d+[a-z]?)\b", title)
        skill = m.group(1) if m else ""
    drafted = re.search(r"AI-drafted on ([^;<]+);", html)
    prompts = []
    for m in re.finditer(r"<form\b[^>]*\bdata-answer\b[^>]*>", html, re.I):
        tag = m.group(0)
        pid = _attr(tag, "data-prompt")
        if not pid or not PROMPT_ID.match(pid) or any(p.prompt == pid for p in prompts):
            continue
        kind = _attr(tag, "data-kind") or "practice"
        before = html[: m.start()]
        section_start = before.lower().rfind("<section")
        scope = before[section_start:] if section_start >= 0 else before[-4000:]
        heads = re.findall(r"<h[23][^>]*>(.*?)</h[23]>", scope, re.S | re.I)
        items = re.findall(r"<li[^>]*>(.*?)</li>", scope, re.S | re.I)
        text = _attr(tag, "data-prompt-text") or "\n".join(_text(x) for x in heads + items)
        prompts.append(Prompt(
            prompt=pid, label=_text(heads[-1]) if heads else pid,
            kind=kind if kind in KINDS else "practice",
            skill=_attr(tag, "data-skill") or skill, text=text.strip(),
        ))
    return LessonPage(lesson, title, skill, prompts, drafted.group(1).strip() if drafted else None)


def lesson_text(html: str, limit: int = 30000) -> str:
    """The readable text of a lesson, for a model to judge answers against."""
    body = re.sub(r"<(script|style)\b.*?</\1\s*>", " ", html, flags=re.S | re.I)
    body = re.sub(r"<(br|p|li|h[1-6]|section|div|pre|tr)\b[^>]*>", "\n", body, flags=re.I)
    text = unescape(re.sub(r"<[^>]+>", "", body))
    text = "\n".join(" ".join(line.split()) for line in text.splitlines())
    return re.sub(r"\n{3,}", "\n\n", text).strip()[:limit]

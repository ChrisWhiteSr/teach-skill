"""Every write the lesson runner makes to a course folder goes through here.

- Paths are confined to the course folder, and only known files can be written.
- Shared files are written only if they still match the version that was read (a hash check).
  On a mismatch the caller's change is re-applied to the newer text, so another teacher's edit
  is merged, never overwritten. This is the procedure in skill/references/map-format.md.
- HTML is written only as a new lessons/NNNN-<slug>.html, with every script except the lesson kit removed.
"""
from __future__ import annotations

import fnmatch
import hashlib
import os
import re
import threading
from html import unescape
from pathlib import Path
from typing import Callable

KIT_SCRIPT = "../assets/lesson-kit.js"
LESSON_PATH = re.compile(r"^lessons/\d{4}-[a-z0-9][a-z0-9-]{0,60}\.html$")

# Markdown the runner may write, and its own state under .teach/.
WRITABLE = ("MAP.md", "LOG.md", "NOTES.md", "RESOURCES.md", "answers/*.md", "learning-records/[0-9][0-9][0-9][0-9]-*.md")
INTERNAL = (".teach/jobs.json", ".teach/events.jsonl")


class WriteRefused(ValueError):
    """A write the rules do not allow."""


class Conflict(Exception):
    """The file changed since it was read."""


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class CourseFiles:
    def __init__(self, root: Path):
        self.root = Path(root).expanduser().resolve()
        self._lock = threading.Lock()

    # ---- paths ------------------------------------------------------------------
    def path(self, rel: str, internal: bool = False) -> Path:
        rel = str(rel).replace("\\", "/").strip("/")
        parts = rel.split("/")
        if not rel or any(p in ("", ".", "..") for p in parts):
            raise WriteRefused(f"invalid path: {rel!r}")
        hidden = [p for p in parts if p.startswith(".")]
        if hidden and not (internal and parts[0] == ".teach" and len(hidden) == 1):
            raise WriteRefused(f"hidden paths are off limits: {rel}")
        p = (self.root / rel).resolve()
        if self.root not in p.parents:
            raise WriteRefused(f"{rel} is outside the course folder")
        return p

    def _check_writable(self, rel: str, internal: bool) -> str:
        rel = rel.replace("\\", "/").strip("/")
        allowed = INTERNAL if internal else WRITABLE
        if not any(rel.count("/") == pat.count("/") and fnmatch.fnmatchcase(rel, pat) for pat in allowed):
            raise WriteRefused(f"{rel} is not a file the lesson runner writes")
        return rel

    # ---- reads ------------------------------------------------------------------
    def read(self, rel: str, internal: bool = False) -> tuple[str, str | None]:
        """The text and its hash, or ("", None) when the file does not exist."""
        p = self.path(rel, internal)
        if not p.is_file():
            return "", None
        text = p.read_text(encoding="utf-8")
        return text, sha(text)

    # ---- writes -----------------------------------------------------------------
    def _atomic(self, p: Path, text: str) -> None:
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_name(f".{p.name}.{os.getpid()}.tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, p)

    def write(self, rel: str, text: str, base_sha: str | None, internal: bool = False) -> str:
        """Write text if the file still has base_sha (None: the file must not exist yet). Returns the new hash."""
        rel = self._check_writable(rel, internal)
        p = self.path(rel, internal)
        with self._lock:
            current = sha(p.read_text(encoding="utf-8")) if p.is_file() else None
            if current != base_sha:
                raise Conflict(rel)
            self._atomic(p, text)
        return sha(text)

    def update(self, rel: str, change: Callable[[str], str], internal: bool = False, attempts: int = 5) -> tuple[str, bool]:
        """Apply change() to the current text and write it, re-reading and re-applying if someone else wrote meanwhile.

        change() must be a pure function of the text it gets, so running it again on a newer version
        merges this change into that version. Returns (text now on disk, whether it changed).
        """
        for _ in range(attempts):
            text, base = self.read(rel, internal)
            new = change(text)
            if new == text:
                return text, False
            try:
                self.write(rel, new, base, internal)
                return new, True
            except Conflict:
                continue
        raise Conflict(f"{rel} kept changing; try again")

    def create(self, rel: str, text: str) -> None:
        """Create a new file; never replaces one."""
        self.write(rel, text, None)

    # ---- lessons ----------------------------------------------------------------
    def write_lesson(self, rel: str, html: str) -> str:
        rel = rel.replace("\\", "/").strip("/")
        if not LESSON_PATH.match(rel):
            raise WriteRefused("a new lesson must be named lessons/NNNN-<slug>.html")
        p = self.path(rel)
        clean = sanitize_lesson_html(html)
        if "<main" not in clean:
            raise WriteRefused("a lesson needs a <main> element")
        with self._lock:
            if p.exists():
                raise WriteRefused(f"{rel} already exists; lessons are only ever created, never replaced")
            self._atomic(p, clean if clean.endswith("\n") else clean + "\n")
        return rel


_SCRIPT = re.compile(r"<script\b(?P<attrs>[^>]*)>(?P<body>.*?)</script\s*>", re.I | re.S)
_SRC = re.compile(r"""\bsrc\s*=\s*["']([^"']+)["']""", re.I)


_URL_ATTR = re.compile(r"""\b(href|src|action|formaction|xlink:href|poster|srcset)\s*=\s*("[^"]*"|'[^']*'|[^\s>]+)""", re.I)


def _safe_url(m: re.Match) -> str:
    value = m.group(2).strip("\"'")
    plain = re.sub(r"[\s\x00-\x1f]+", "", unescape(value)).lower()
    if plain.startswith(("javascript:", "vbscript:", "data:")):
        return f'{m.group(1)}="#"'
    return m.group(0)


def sanitize_lesson_html(html: str) -> str:
    """Keep the lesson kit's script tag and nothing else that can run code."""
    def keep(m: re.Match) -> str:
        src = _SRC.search(m.group("attrs"))
        return m.group(0) if src and src.group(1) == KIT_SCRIPT and not m.group("body").strip() else ""

    out = _SCRIPT.sub(keep, html)
    # Unclosed or self-closing script tags left behind.
    out = re.sub(r"<script\b(?![^>]*\bsrc\s*=\s*[\"']" + re.escape(KIT_SCRIPT) + r"[\"'])[^>]*>", "", out, flags=re.I)
    out = re.sub(r"<(iframe|object|embed|frame|frameset|applet|base)\b[^>]*>(.*?</\1\s*>)?", "", out, flags=re.I | re.S)
    out = re.sub(r"<meta\b[^>]*http-equiv[^>]*>", "", out, flags=re.I)
    out = re.sub(r"""\s+on[a-z]+\s*=\s*("[^"]*"|'[^']*'|[^\s>]+)""", "", out, flags=re.I)
    out = _URL_ATTR.sub(_safe_url, out)
    if KIT_SCRIPT not in out and "</head>" in out:
        out = out.replace("</head>", f'<script defer src="{KIT_SCRIPT}"></script>\n</head>', 1)
    return out

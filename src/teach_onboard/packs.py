"""Course packs: a fixed skill map, curated sources and an optional question bank for a known course.

A pack lives in its own folder as pack.yaml. See packs/git-basics/pack.yaml for the format.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .engine import Skill, validate_map
from .method import Method


@dataclass
class Pack:
    name: str
    title: str
    subject: str
    description: str
    skills: list[Skill]
    resources: list[dict]
    items: dict[str, list[dict]] = field(default_factory=dict)


def load_pack(folder: Path, method: Method | None = None) -> Pack:
    raw = yaml.safe_load((folder / "pack.yaml").read_text(encoding="utf-8"))
    skills, items = [], {}
    for s in raw["skills"]:
        skills.append(Skill(str(s["id"]), str(s["skill"]), [str(n) for n in s.get("needs", [])]))
        bank = []
        for it in s.get("items", []) or []:
            bank.append({"question": str(it["question"]), "answer": str(it["answer"]),
                         "rubric": [str(r) for r in it.get("rubric", [])]})
        if bank:
            items[str(s["id"])] = bank
    errors = validate_map(skills, method)
    if errors:
        raise ValueError(f"pack {folder.name}: " + "; ".join(errors))
    resources = [{"title": str(r["title"]), "url": str(r.get("url", "")), "kind": str(r.get("kind", "article")),
                  "use": str(r.get("use", ""))} for r in raw.get("resources", [])]
    return Pack(
        name=folder.name, title=str(raw["title"]), subject=str(raw.get("subject") or raw["title"]),
        description=str(raw.get("description", "")), skills=skills, resources=resources, items=items,
    )


def list_packs(packs_root: Path, method: Method | None = None) -> dict[str, Pack]:
    out = {}
    if packs_root.is_dir():
        for folder in sorted(p for p in packs_root.iterdir() if (p / "pack.yaml").is_file()):
            out[folder.name] = load_pack(folder, method)
    return out

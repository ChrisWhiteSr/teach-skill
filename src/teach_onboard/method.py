"""Load the method's numbers from skill/method.yaml, the same file the teach skill describes."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent


def _bundled(name: str) -> Path:
    """Find a top-level repo folder: bundled inside the package when installed, beside src/ in a checkout."""
    for candidate in (HERE / name, HERE.parents[1] / name):
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"could not find the {name}/ folder next to the package or the repo root")


def skill_dir() -> Path:
    return _bundled("skill")


def packs_dir() -> Path:
    return _bundled("packs")


@dataclass(frozen=True)
class Method:
    mastery_threshold: float
    mastery_min_items: int
    practice_band: tuple[float, float]
    xp_min_accuracy: float
    session_minutes: int
    review_intervals_days: tuple[int, ...]
    review_interval_after_days: int
    max_reviews_per_session: int
    placement_min_items: int
    placement_max_items: int
    correct_to_place: int
    tested_start_step: int
    inferred_start_step: int
    map_min_skills: int
    map_max_skills: int

    def interval_for_step(self, step: int) -> int:
        if step < len(self.review_intervals_days):
            return self.review_intervals_days[step]
        return self.review_interval_after_days


def load_method(path: Path | None = None) -> Method:
    path = path or skill_dir() / "method.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    p, m = raw["placement"], raw["map"]
    return Method(
        mastery_threshold=float(raw["mastery_threshold"]),
        mastery_min_items=int(raw["mastery_min_items"]),
        practice_band=(float(raw["practice_band"][0]), float(raw["practice_band"][1])),
        xp_min_accuracy=float(raw["xp_min_accuracy"]),
        session_minutes=int(raw["session_minutes"]),
        review_intervals_days=tuple(int(d) for d in raw["review_intervals_days"]),
        review_interval_after_days=int(raw["review_interval_after_days"]),
        max_reviews_per_session=int(raw["max_reviews_per_session"]),
        placement_min_items=int(p["min_items"]),
        placement_max_items=int(p["max_items"]),
        correct_to_place=int(p["correct_to_place"]),
        tested_start_step=int(p["tested_start_step"]),
        inferred_start_step=int(p["inferred_start_step"]),
        map_min_skills=int(m["min_skills"]),
        map_max_skills=int(m["max_skills"]),
    )

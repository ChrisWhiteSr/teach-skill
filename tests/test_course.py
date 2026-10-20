from datetime import date

import pytest

from teach_onboard.course import CourseExists, course_path, slugify, write_course
from teach_onboard.engine import Result, resolve


def test_slug_and_path(tmp_path):
    assert slugify("Statistics for Reading Papers!") == "statistics-for-reading-papers"
    assert slugify("../../etc") == "etc"
    assert course_path(tmp_path, "../../x").parent == tmp_path.resolve()


def test_writes_every_file_in_the_skill_formats(tmp_path, chain, method):
    results = [Result("S4", "Q4?", "yes", "k", True), Result("S4", "Q4b?", "yes", "k", True),
               Result("S6", "Q6?", "", "k", False, dont_know=True)]
    st = resolve(chain, results, method)
    path = tmp_path / "demo"
    write_course(path, subject="Demo", mission={"why": "To ship X.", "success": ["Do A"], "session_minutes": 20},
                 skills=chain, statuses=st, results=results, resources=[{"title": "Book", "url": "https://e.x", "kind": "book", "use": "basics"}],
                 resources_verified=False, background="I know a bit", method=method, minutes=12, today=date(2026, 10, 20))
    names = {p.relative_to(path).as_posix() for p in path.rglob("*") if p.is_file()}
    assert {"MISSION.md", "MAP.md", "RESOURCES.md", "LOG.md", "NOTES.md", ".teach/placement.json",
            "learning-records/0001-stated-background.md"} <= names

    m = (path / "MAP.md").read_text()
    assert "| ID | Skill (the learner can…) | Needs | Status | Best check | Last | Step | Next review |" in m
    assert "| S4 | skill 4 | S3 | mastered | placement 2/2 | 2026-10-20 | 1 | 2026-10-23 |" in m
    assert "| S2 | skill 2 | S1 | mastered | inferred from S4 | 2026-10-20 | 0 | 2026-10-21 |" in m
    assert "| S6 | skill 6 | S5 | new | placement 0/1 | 2026-10-20 | - | - |" in m
    assert "| S8 | skill 8 | S7 | new | - | - | - | - |" in m
    assert "Answered: I don't know" in m

    assert "Session length: 20 minutes" in (path / "MISSION.md").read_text()
    assert "#needs-verification" in (path / "RESOURCES.md").read_text()
    assert "| onboarding | 12 | - |" in (path / "LOG.md").read_text()


def test_refuses_to_overwrite(tmp_path, chain, method):
    path = tmp_path / "taken"
    path.mkdir()
    (path / "MISSION.md").write_text("mine")
    with pytest.raises(CourseExists):
        write_course(path, subject="x", mission={"why": "y"}, skills=chain, statuses=resolve(chain, [], method),
                     results=[], resources=[], resources_verified=True, background="", method=method, minutes=1)
    assert (path / "MISSION.md").read_text() == "mine"

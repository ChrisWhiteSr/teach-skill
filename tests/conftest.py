import pytest

from teach_onboard.engine import Skill
from teach_onboard.method import load_method


@pytest.fixture
def method():
    return load_method()


@pytest.fixture
def chain():
    """S1 <- S2 <- S3 ... <- S8, a straight line of prerequisites."""
    return [Skill(f"S{i}", f"skill {i}", [f"S{i-1}"] if i > 1 else []) for i in range(1, 9)]


@pytest.fixture
def diamond():
    needs = {1: [], 2: ["S1"], 3: ["S1"], 4: ["S2", "S3"], 5: ["S4"], 6: ["S4"], 7: ["S5", "S6"], 8: ["S7"]}
    return [Skill(f"S{i}", f"skill {i}", needs[i]) for i in range(1, 9)]


MAP = """# Skill map: Git basics

Mission: [[MISSION]] · Updated: 2026-10-20 by onboarding (placement)

| ID | Skill (the learner can…) | Needs | Status | Best check | Last | Step | Next review |
|---|---|---|---|---|---|---|---|
| S1 | explain what a commit is and what it records | - | mastered | placement 2/2 | 2026-10-20 | 1 | 2026-10-23 |
| S2 | explain the working tree, the staging area and the repository | S1 | new | - | - | - | - |
| S3 | commit only the changes you choose, with a useful message | S2 | new | - | - | - | - |

## Missed items
- None from placement.

## Holes
- None found yet.
"""

LOG = """# Session log: Git basics

| Date | Agent | Minutes | XP | Reviews | Check | Taught | Note |
|---|---|---|---|---|---|---|---|
| 2026-10-20 | onboarding | 12 | - | - | placement | - | placement |
"""


def lesson_html(n_check=5, skill="S2"):
    checks = "".join(
        f'<section><h2>Check {i}</h2><form data-answer data-prompt="check-{i}" data-kind="check" '
        f'data-prompt-text="Check question {i} about staging?"><label for="c{i}">Answer</label><textarea id="c{i}"></textarea></form></section>'
        for i in range(1, n_check + 1))
    return (
        '<!doctype html><html><head><meta charset="utf-8"><title>0001</title>'
        '<link rel="stylesheet" href="../assets/lesson-kit.css"><script defer src="../assets/lesson-kit.js"></script></head>'
        f'<body><main data-skill="{skill}"><header><h1>0001 · {skill}: the three areas</h1></header>'
        '<section><h2>Warm-up</h2><div data-quiz data-explanation="x"><button data-correct="true">A</button>'
        '<button data-correct="false">B</button><p role="status"></p></div></section>'
        '<section><h2>Practice</h2><ol><li>Where does an edit sit after git add?</li></ol>'
        '<form data-answer data-prompt="practice-1"><label for="p1">Answer</label><textarea id="p1"></textarea></form></section>'
        f'{checks}<section class="sources"><ol><li><a href="https://git-scm.com/book">Pro Git</a></li></ol></section></main></body></html>'
    )


@pytest.fixture
def course(tmp_path):
    root = tmp_path / "git-basics"
    (root / "lessons").mkdir(parents=True)
    (root / "MAP.md").write_text(MAP)
    (root / "LOG.md").write_text(LOG)
    (root / "MISSION.md").write_text("# Mission: Git basics\n\n## Why\nShip clean pull requests at work.\n")
    (root / "NOTES.md").write_text("# Notes\n")
    (root / "RESOURCES.md").write_text("# Git Resources\n\n## Knowledge\n\n- [Pro Git](https://git-scm.com/book)\n  The book.\n")
    (root / "lessons" / "0001-the-three-areas.html").write_text(lesson_html())
    return root

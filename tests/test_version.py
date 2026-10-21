"""The version is recorded in four places; they must agree."""
import re
from pathlib import Path

import teach_onboard
from teach_onboard.method import skill_dir

ROOT = Path(__file__).resolve().parents[1]


def test_versions_agree():
    v = teach_onboard.__version__
    assert re.search(rf'^version = "{re.escape(v)}"$', (ROOT / "pyproject.toml").read_text(), re.M)
    assert re.search(rf"^  version: {re.escape(v)}$", (skill_dir() / "SKILL.md").read_text(), re.M)
    for name in ("lesson-kit.js", "lesson-kit.css"):
        assert f"teach lesson kit {v}" in (skill_dir() / "assets" / name).read_text(), name
    assert f"## {v}" in (ROOT / "CHANGELOG.md").read_text()

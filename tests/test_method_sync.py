"""SKILL.md states the method's numbers in prose; method.yaml holds them for the app. They must agree."""
from teach_onboard.method import load_method, skill_dir


def test_skill_prose_matches_method_yaml():
    m = load_method()
    text = (skill_dir() / "SKILL.md").read_text()
    pct = lambda x: f"{round(x * 100)}%"
    assert f"Mastery gate at {pct(m.mastery_threshold)}" in text
    assert f"at least {pct(m.mastery_threshold)} on a mastery check of five or more" in text and m.mastery_min_items == 5
    assert f"{round(m.practice_band[0] * 100)}–{round(m.practice_band[1] * 100)}% band" in text
    assert f"fell below {pct(m.xp_min_accuracy)} earns zero XP" in text
    assert f"Default {m.session_minutes} minutes" in text
    days = m.review_intervals_days
    assert f"{', '.join(str(d) for d in days[:-1])} and {days[-1]} days apart, then every {m.review_interval_after_days} days" in text
    assert f"Cap reviews at eight items" in text and m.max_reviews_per_session == 8
    assert f"about {m.placement_min_items}–{m.placement_max_items} recall items" in text
    assert "only after two correct, unaided items" in text and m.correct_to_place == 2
    assert f"Draft {m.map_min_skills}–{m.map_max_skills} skills" in text


def test_references_exist():
    refs = skill_dir() / "references"
    text = (skill_dir() / "SKILL.md").read_text()
    import re
    for name in set(re.findall(r"references/([a-z-]+\.md)", text)):
        assert (refs / name).is_file(), name

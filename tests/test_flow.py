from datetime import date

import pytest

from teach_onboard.llm import FakeProvider
from teach_onboard.method import packs_dir
from teach_onboard.onboarding import FlowError, Onboarding
from teach_onboard.packs import list_packs


@pytest.fixture
def app(tmp_path, method):
    return Onboarding(FakeProvider(), method, tmp_path, list_packs(packs_dir(), method))


def place(app, s, knows):
    while not (item := app.next_item(s))["done"]:
        sid = s.current["skill_id"]
        app.answer(s, "right, because" if sid in knows else "no idea really", False)


def test_open_topic_flow_writes_a_course(app, tmp_path):
    s = app.start("Bayesian statistics")
    assert "follow_up" in app.submit_mission(s, {"why": "fun"})          # too vague: one follow-up
    out = app.submit_mission(s, {"why": "fun"}, follow_up_answer="Read papers at work")
    assert out["mission"]["session_minutes"] == 25                       # second round always accepted
    m = app.draft_map(s)
    assert len(m["skills"]) == 8 and not m["from_pack"]
    app.set_map(s, m["skills"], drop=["S8"], flagged=["S2"])
    assert len(s.skills) == 7
    place(app, s, knows={"S1", "S2", "S3", "S4"})
    summary = app.summary(s)
    assert summary["counts"]["mastered_tested"] >= 1
    path = app.finish(s, today=date(2026, 10, 20))["path"]
    assert (tmp_path / "bayesian-statistics" / "MAP.md").is_file() and path.endswith("bayesian-statistics")
    with pytest.raises(FlowError):
        app.set_map(s, m["skills"], [], [])                              # map is fixed once placement starts


def test_pack_uses_its_question_bank_and_sources(app, tmp_path):
    s = app.start("", "git-basics")
    assert s.subject == "Git version control"
    app.submit_mission(s, {"why": "I break my repo every week and want to stop"})
    m = app.draft_map(s)
    assert m["from_pack"] and m["skills"][0]["skill"].startswith("explain what a commit is")
    app.set_map(s, m["skills"], [], [])
    item = app.next_item(s)
    assert item["question"] in {it["question"] for bank in s.pack.items.values() for it in bank}
    calls_before = [c.task for c in app.provider.calls]
    assert "item" not in calls_before
    while not app.next_item(s)["done"]:
        app.answer(s, "", True)
    app.finish(s)
    res = (tmp_path / "git-version-control" / "RESOURCES.md").read_text()
    assert "Pro Git" in res and "#needs-verification" not in res


def test_dispute_regrades(app):
    s = app.start("Chess openings")
    app.submit_mission(s, {"why": "Win more club games on Tuesdays"})
    m = app.draft_map(s)
    app.set_map(s, m["skills"], [], [])
    app.next_item(s)
    app.answer(s, "wrong answer", False)
    before = app.summary(s)["answers"][0]
    assert not before["correct"]
    after = app.dispute(s, 0)["answers"][0]
    assert after["correct"] and after["disputed"]


def test_steps_must_run_in_order(app):
    s = app.start("Welding")
    with pytest.raises(FlowError):
        app.draft_map(s)
    with pytest.raises(FlowError):
        app.next_item(s)
    with pytest.raises(FlowError):
        app.finish(s)


def test_next_question_is_written_ahead_for_both_outcomes(app):
    s = app.start("Bird identification")
    app.submit_mission(s, {"why": "Log every species at my feeder this winter"})
    m = app.draft_map(s)
    app.set_map(s, m["skills"], [], [])
    assert len(s.prefetch) == 1                     # the first question is written while the map is confirmed
    app.next_item(s)
    assert not any(k[1] == 0 and k[0] == s.current["skill_id"] for k in s.prefetch)   # used, not left behind
    assert len(s.prefetch) >= 1                     # both branches queued for the next question
    first = s.current["skill_id"]
    app.answer(s, "right", False)
    item = app.next_item(s)
    assert s.current["skill_id"] == first           # confirm with a second item on the same skill
    assert item["question"] and not item["done"]

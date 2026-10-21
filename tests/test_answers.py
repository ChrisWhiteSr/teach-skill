from datetime import datetime

from teach_onboard import answers as A
from conftest import lesson_html


def test_entry_round_trip():
    entry = A.render_entry("check-1", "2026-10-21 14:05", "Which commands?\nName both.", "git add app.py\n\ngit commit", "S3", "check")
    text = A.append_entry("", entry, "0004-commit", "0004 · S3: commit")
    assert text.startswith("# Answers: 0004 · S3: commit\n")
    [e] = A.parse(text)
    assert (e.prompt, e.when, e.skill, e.kind) == ("check-1", "2026-10-21 14:05", "S3", "check")
    assert e.prompt_text == "Which commands?\nName both."
    assert e.answer == "git add app.py\n\ngit commit"
    assert e.feedback is None and A.pending(text) == [e]


def test_feedback_written_in_place_and_parsed_back():
    one = A.render_entry("p1", "2026-10-21 14:05", "Q1", "first", "S2", "practice")
    two = A.render_entry("p2", "2026-10-21 14:06", "Q2", "second", "S2", "practice")
    text = A.append_entry(A.append_entry("", one, "0001-x", "T"), two, "0001-x", "T")
    block = A.feedback_block("2026-10-21", "claude-code", "partial", "You named the staging area.",
                             "Add the working tree.\n\nIt holds edits.", "Explain one more case.")
    new, n = A.apply_feedback(text, {("p2", "2026-10-21 14:06"): block})
    assert n == 1 and A.WAITING in new.split("## Answer · p2")[0]          # the first entry still waits
    first, second = A.parse(new)
    assert first.feedback is None
    assert second.judgment == "partial" and second.feedback_by == "claude-code" and second.feedback_date == "2026-10-21"
    assert "What to add or fix: Add the working tree.\nIt holds edits." in second.feedback
    assert second.answer == "second"
    again, n2 = A.apply_feedback(new, {("p2", "2026-10-21 14:06"): block})   # idempotent: no second feedback
    assert n2 == 0 and again == new


def test_hand_written_feedback_parses():
    text = A.append_entry("", A.render_entry("p1", "2026-10-21 09:00", "Q", "a", "S1", "review"), "0001-x", "T")
    text = text.replace(A.WAITING, "**Teacher feedback** (2026-10-22, hermes): **Judgment: correct.**\n\nNice.")
    [e] = A.parse(text)
    assert e.judgment == "correct" and e.feedback == "Nice." and e.kind == "review"


def test_same_minute_gets_seconds():
    now = datetime(2026, 10, 21, 14, 5, 31)
    text = A.append_entry("", A.render_entry("p1", "2026-10-21 14:05", "Q", "a", "", "practice"), "0001-x", "T")
    assert A.entry_time(text, "p1", now) == "2026-10-21 14:05:31"
    assert A.entry_time(text, "p2", now) == "2026-10-21 14:05"


def test_read_lesson():
    page = A.read_lesson("0001-the-three-areas", lesson_html())
    assert page.skill == "S2" and page.title == "0001 · S2: the three areas"
    kinds = [(p.prompt, p.kind) for p in page.prompts]
    assert kinds[0] == ("practice-1", "practice") and kinds[1:] == [(f"check-{i}", "check") for i in range(1, 6)]
    assert page.prompt("check-3").text == "Check question 3 about staging?"
    assert "Where does an edit sit" in page.prompt("practice-1").text


def test_block_copied_from_the_kit_parses():
    """The lesson kit's "Copy for your teacher" text (captured from a browser run) is a valid entry."""
    pasted = (
        "For answers/0001-commit-chosen-changes.md:\n\n"
        "## Answer · practice-1 · 2026-10-21 14:00\n\nSkill: S3 · Kind: practice\n\n"
        "**Prompt**\n\n> Practice\n> You changed three files but want two separate commits. Describe the commands, in order.\n\n"
        "**Answer**\n\n> git add a b, commit, then git add c, commit\n\n*Waiting for teacher feedback.*"
    )
    text = A.append_entry("", pasted.split("\n\n", 1)[1] + "\n", "0001-commit-chosen-changes", "T")
    [e] = A.pending(text)
    assert (e.prompt, e.skill, e.kind, e.answer) == ("practice-1", "S3", "practice", "git add a b, commit, then git add c, commit")

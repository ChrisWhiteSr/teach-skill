"""Judged answers map onto the existing mastery rules: the gate, reviews, practice, missed items."""
from datetime import date

from teach_onboard import answers as A
from teach_onboard import mastery
from conftest import MAP, lesson_html

TODAY = date(2026, 10, 22)


def judged(page, judgments, kind_prefix="check"):
    text = ""
    for i, j in enumerate(judgments, 1):
        p = page.prompt(f"{kind_prefix}-{i}")
        text = A.append_entry(text, A.render_entry(p.prompt, f"2026-10-22 10:0{i}", p.text, f"answer {i}", p.skill, p.kind), "x", "T")
        if j:
            text, _ = A.apply_feedback(text, {(p.prompt, f"2026-10-22 10:0{i}"): A.feedback_block("2026-10-22", "t", j, "", "fix", "")})
    return A.parse(text)


def run(page, entries, method, map_text=MAP):
    outs = mastery.evaluate(page, entries, {e.key for e in entries if e.judgment}, method)
    return outs, *mastery.apply(map_text, outs, TODAY, method, "test-agent")


def row(text, sid):
    return next(line for line in text.splitlines() if line.startswith(f"| {sid} |"))


def test_full_check_at_gate_masters(method):
    page = A.read_lesson("0001-x", lesson_html())
    outs, new, changes = run(page, judged(page, ["correct"] * 5), method)
    assert row(new, "S2") == "| S2 | explain the working tree, the staging area and the repository | S1 | mastered | 5/5 | 2026-10-22 | 0 | 2026-10-23 |"
    assert "Updated: 2026-10-22 by test-agent" in new and changes == ["S2 mastered: check 5/5; first review 2026-10-23"]


def test_four_of_five_with_a_partial_stays_learning(method):
    page = A.read_lesson("0001-x", lesson_html())
    _, new, _ = run(page, judged(page, ["correct", "correct", "partial", "correct", "correct"]), method)
    assert "| S2 | explain the working tree, the staging area and the repository | S1 | learning | 4/5 | 2026-10-22 | - | - |" in new
    missed = new.split("## Missed items\n")[1].split("\n## ")[0]
    assert "- None from placement." not in missed
    assert "- S2 (2026-10-22): Check question 3 about staging? Answered: answer 3 (partial)" in missed


def test_incomplete_check_is_practice(method):
    page = A.read_lesson("0001-x", lesson_html())
    outs, new, _ = run(page, judged(page, ["correct"] * 4 + [None]), method)
    assert [o.kind for o in outs] == ["practice"]
    assert "| S2 |" in new and "| learning | - | 2026-10-22 | - | - |" in row(new, "S2")


def test_too_few_check_items_never_master(method):
    page = A.read_lesson("0001-x", lesson_html(n_check=3))
    _, new, _ = run(page, judged(page, ["correct"] * 3), method)
    assert "| learning |" in row(new, "S2") and "mastered" not in row(new, "S2")


def test_only_first_answers_count(method):
    page = A.read_lesson("0001-x", lesson_html())
    entries = judged(page, ["correct", "correct", "incorrect", "correct", "correct"])
    p = page.prompt("check-3")
    retry = A.Entry("check-3", "2026-10-22 11:00", "right now", p.text, "S2", "check", feedback="ok", judgment="correct")
    outs = mastery.evaluate(page, entries + [retry], {retry.key}, method)
    assert [o.kind for o in outs] == ["practice"]          # a second try after feedback is practice


def test_review_pass_and_miss(method):
    html = lesson_html(skill="S1").replace('data-kind="check"', 'data-kind="review"')
    page = A.read_lesson("0001-x", html)
    _, passed, _ = run(page, judged(page, ["correct"] * 5, "check"), method)
    assert row(passed, "S1").endswith("| mastered | placement 2/2 | 2026-10-22 | 2 | 2026-10-29 |")
    _, missed, _ = run(page, judged(page, ["correct", "incorrect", "correct", "correct", "correct"], "check"), method)
    assert row(missed, "S1").endswith("| learning | placement 2/2 | 2026-10-22 | - | - |")
    assert "- S1 (2026-10-22): Check question 2" in missed


def test_mastery_clears_missed_items(method):
    page = A.read_lesson("0001-x", lesson_html())
    _, first, _ = run(page, judged(page, ["incorrect"] + ["correct"] * 4), method)
    assert "- S2 (2026-10-22)" in first
    page2 = A.read_lesson("0001-x", lesson_html().replace("check-", "check2-"))
    entries = judged(page2, ["correct"] * 5, "check2")
    _, second, _ = run(page2, entries, method, first)
    assert "- S2 (" not in second and "- None." in second


def test_next_skill():
    assert mastery.next_skill(MAP) == ("S2", "explain the working tree, the staging area and the repository")

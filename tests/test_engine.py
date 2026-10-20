from teach_onboard.engine import (Result, Skill, ancestors, depths, descendants, drop_skills, next_skill, resolve,
                                  validate_map)


def answer(skill_id, correct, dont_know=False):
    return Result(skill_id, f"q on {skill_id}", "a", "key", correct, dont_know)


def run(skills, method, knows, flagged=frozenset()):
    """Simulate a learner who answers correctly exactly on the skills in `knows`."""
    results = []
    while (sid := next_skill(skills, results, method, flagged)) is not None:
        results.append(answer(sid, sid in knows))
        assert len(results) <= method.placement_max_items
    return results, resolve(skills, results, method)


def test_validate_catches_bad_maps(method):
    assert validate_map([], method) == ["the map has no skills"]
    assert any("not on the map" in e for e in validate_map([Skill("S1", "a", ["S9"])], method))
    assert any("loop back" in e for e in validate_map([Skill("S1", "a", ["S2"]), Skill("S2", "b", ["S1"])], method))
    assert any("duplicate" in e for e in validate_map([Skill("S1", "a"), Skill("S1", "b")], method))
    assert any("ids look like" in e for e in validate_map([Skill("X", "a")], method))
    too_many = [Skill(f"S{i}", "x") for i in range(1, method.map_max_skills + 2)]
    assert any("or fewer" in e for e in validate_map(too_many, method))


def test_graph_helpers(diamond):
    d = depths(diamond)
    assert d["S1"] == 0 and d["S4"] == 2 and d["S8"] == 5
    assert ancestors(diamond, "S4") == {"S1", "S2", "S3"}
    assert descendants(diamond, "S6") == {"S7", "S8"}
    dropped = drop_skills(diamond, {"S3"})
    assert "S3" not in {s.id for s in dropped}
    assert next(s for s in dropped if s.id == "S4").needs == ["S2"]


def test_one_correct_answer_is_confirmed_with_a_second(chain, method):
    results = [answer("S4", True)]
    assert next_skill(chain, results, method) == "S4"


def test_expert_climbs_and_infers_the_foundations(chain, method):
    results, st = run(chain, method, knows={f"S{i}" for i in range(1, 9)})
    assert st["S8"].status == "mastered" and st["S8"].source == "tested"
    assert all(st[f"S{i}"].status == "mastered" for i in range(1, 9))
    assert any(st[f"S{i}"].source == "inferred" for i in range(1, 8))
    assert len(results) <= method.placement_max_items


def test_beginner_steps_down_to_the_bottom(chain, method):
    results, st = run(chain, method, knows=set())
    assert all(s.status == "new" for s in st.values())
    asked = [r.skill_id for r in results]
    assert asked[0] != "S1"          # starts mid-map, not at the bottom
    assert "S1" in asked             # but reaches the bottom when everything is missed
    assert len(results) <= 4


def test_middle_learner_is_placed_at_the_frontier(chain, method):
    _, st = run(chain, method, knows={"S1", "S2", "S3", "S4"})
    assert st["S4"].status == "mastered"
    assert all(st[f"S{i}"].status == "mastered" for i in range(1, 5))
    assert all(st[f"S{i}"].status == "new" for i in range(5, 9))


def test_diamond_with_one_missing_branch(diamond, method):
    _, st = run(diamond, method, knows={"S1", "S2"})
    assert st["S2"].status == "mastered"
    assert st["S3"].status != "mastered"
    assert st["S4"].status == "new" and st["S8"].status == "new"


def test_tested_miss_beats_inference(chain, method):
    results = [answer("S6", True), answer("S6", True), answer("S3", False)]
    st = resolve(chain, results, method)
    assert st["S6"].status == "mastered"
    assert st["S3"].status == "new" and st["S3"].source == "tested"
    assert st["S2"].source == "inferred"


def test_partial_knowledge_is_learning(chain, method):
    st = resolve(chain, [answer("S4", True), answer("S4", False)], method)
    assert st["S4"].status == "learning"


def test_budget_is_respected(diamond, method):
    flaky = {"S1", "S3", "S5", "S7"}
    results, _ = run(diamond, method, knows=flaky)
    assert len(results) <= method.placement_max_items


def test_spot_checks_inferred_skills_when_placement_was_short(chain, method):
    results, st = run(chain, method, knows={f"S{i}" for i in range(1, 9)})
    assert len(results) >= min(method.placement_min_items, len(chain))


def test_flagged_skill_breaks_ties(method):
    skills = [Skill("S1", "a"), Skill("S2", "b"), Skill("S3", "c")]
    assert next_skill(skills, [], method, {"S3"}) == "S3"

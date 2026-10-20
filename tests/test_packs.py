from teach_onboard.method import packs_dir
from teach_onboard.packs import list_packs


def test_example_pack_is_valid_and_banked(method):
    packs = list_packs(packs_dir(), method)
    git = packs["git-basics"]
    assert len(git.skills) == 8
    assert all(len(git.items.get(s.id, [])) >= method.correct_to_place for s in git.skills)
    assert len(git.resources) >= 3

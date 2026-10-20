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

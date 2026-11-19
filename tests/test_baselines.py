import numpy as np
import pytest

from oioa.problem import Problem
from oioa.registry import ABLATION_VARIANTS, MAIN_ALGORITHMS, get_algorithm


def sphere(x):
    return float(np.sum(x ** 2))


@pytest.mark.parametrize("name", list(MAIN_ALGORITHMS))
def test_algorithm_respects_budget_and_beats_random_search(name):
    p = Problem(sphere, [-100] * 4, [100] * 4, 3000)
    get_algorithm(name)(p, np.random.default_rng(0))
    assert p.fe == 3000
    rnd = Problem(sphere, [-100] * 4, [100] * 4, 3000)
    rnd.evaluate(rnd.random_population(np.random.default_rng(0), 3000))
    assert p.best_f < rnd.best_f


@pytest.mark.parametrize("name", list(MAIN_ALGORITHMS))
def test_common_initial_population_is_accepted(name):
    p = Problem(sphere, [-100] * 3, [100] * 3, 1500)
    init = p.random_population(np.random.default_rng(1), 50)
    get_algorithm(name)(p, np.random.default_rng(2), init)
    assert p.fe == 1500


def test_unknown_algorithm_message_lists_choices():
    with pytest.raises(ValueError) as e:
        get_algorithm("nope")
    assert "OIOA" in str(e.value)


def test_ablation_names_resolve():
    for n in ABLATION_VARIANTS:
        assert callable(get_algorithm(n))

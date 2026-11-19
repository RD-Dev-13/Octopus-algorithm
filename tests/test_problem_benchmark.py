import numpy as np
import pytest

from oioa.benchmark import FUNCTION_IDS, make_cec2017
from oioa.problem import Problem


def sphere(x):
    return float(np.sum(x ** 2))


def test_budget_is_never_exceeded():
    p = Problem(sphere, [-5] * 3, [5] * 3, max_fe=25)
    p.evaluate(np.zeros((40, 3)))
    assert p.fe == 25 and p.done


def test_unevaluated_rows_get_inf():
    p = Problem(sphere, [-5] * 2, [5] * 2, max_fe=2)
    out = p.evaluate(np.ones((4, 2)))
    assert np.isfinite(out[:2]).all() and np.isinf(out[2:]).all()


def test_best_tracking_and_history_length():
    p = Problem(sphere, [-5] * 2, [5] * 2, max_fe=100, n_checkpoints=10)
    rng = np.random.default_rng(0)
    p.evaluate(p.random_population(rng, 100))
    assert len(p.history) == 10
    assert all(a >= b for a, b in zip(p.history, p.history[1:]))   # best-so-far never worsens


def test_bad_bounds_rejected():
    with pytest.raises(ValueError):
        Problem(sphere, [1, 1], [0, 2], 10)


def test_wrong_dimension_rejected():
    p = Problem(sphere, [-1] * 3, [1] * 3, 10)
    with pytest.raises(ValueError):
        p.evaluate(np.zeros((1, 2)))


def test_clip_respects_bounds():
    p = Problem(sphere, [-1] * 2, [1] * 2, 10)
    assert np.all(np.abs(p.clip(np.array([[5.0, -5.0]]))) <= 1)


@pytest.mark.parametrize("fid", [1, 4, 10, 17, 29])
def test_cec2017_bias_and_optimum(fid):
    p = make_cec2017(fid, 10, 10)
    assert p.f_offset == pytest.approx(fid * 100.0)         # opfunu convention: optimum of Fk is 100 * k
    assert p.evaluate(np.zeros((1, 10)))[0] >= p.f_offset - 1e-6


def test_cec2017_covers_29_functions():
    assert list(FUNCTION_IDS) == list(range(1, 30))

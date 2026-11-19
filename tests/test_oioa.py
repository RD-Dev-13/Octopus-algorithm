import numpy as np
import pytest

from oioa.oioa import (BEHAVIORS, ESCAPE, OIOAConfig, behavior_probabilities, behavior_scores, levy_steps,
                       make_variant, oioa, population_diversity, progress_rate)
from oioa.problem import Problem


def sphere(x):
    return float(np.sum(x ** 2))


def make(max_fe=3000, d=5):
    return Problem(sphere, [-100] * d, [100] * d, max_fe)


def test_probabilities_are_valid_distributions():
    cfg = OIOAConfig()
    kappa = np.array([0, 3, 5, 8, 12, 20])
    for delta in (0.0, 0.5, 1.0):
        for rho in (0.0, 0.01, 1.0):
            p = behavior_probabilities(delta, rho, kappa, cfg)
            assert np.allclose(p.sum(axis=1), 1.0) and np.all(p >= 0)


def test_escape_is_gated_by_stagnation():
    p = behavior_probabilities(0.1, 0.0, np.array([0, 4, 5]), OIOAConfig())
    assert p[0, ESCAPE] == 0 and p[1, ESCAPE] == 0 and p[2, ESCAPE] > 0


def test_low_diversity_shifts_mass_from_imitate_to_mimic():
    k = np.array([0])
    hi = behavior_probabilities(1.0, 0.0, k, OIOAConfig())[0]
    lo = behavior_probabilities(0.0, 0.0, k, OIOAConfig())[0]
    assert lo[1] > hi[1] and lo[0] < hi[0]


def test_progress_favours_camouflage():
    k = np.array([0])
    no = behavior_probabilities(0.5, 0.0, k, OIOAConfig())[0]
    yes = behavior_probabilities(0.5, 0.05, k, OIOAConfig())[0]
    assert yes[2] > no[2]


def test_disabled_behaviour_gets_zero_probability():
    cfg = OIOAConfig(behaviors=("imitate", "camouflage", "escape"))
    p = behavior_probabilities(0.2, 0.0, np.array([0, 10]), cfg)
    assert np.all(p[:, 1] == 0)


def test_uniform_selector_is_uniform_over_available():
    cfg = OIOAConfig(selector="uniform")
    p = behavior_probabilities(0.3, 0.0, np.array([0, 10]), cfg)
    assert np.allclose(p[0], [1 / 3, 1 / 3, 1 / 3, 0]) and np.allclose(p[1], 0.25)


def test_scores_use_minus_inf_for_unavailable():
    z = behavior_scores(0.5, 0.0, np.array([0]), OIOAConfig())
    assert np.isneginf(z[0, ESCAPE])


def test_config_validation():
    with pytest.raises(ValueError):
        OIOAConfig(selector="nope")
    with pytest.raises(ValueError):
        OIOAConfig(behaviors=())
    with pytest.raises(ValueError):
        OIOAConfig(kappa_min=10, kappa_max=5)


def test_diversity_zero_for_identical_population():
    assert population_diversity(np.ones((5, 3)), 10.0) == 0.0


def test_progress_rate_bounds_and_value():
    assert progress_rate([10.0], [20.0], 5) == 1.0
    assert progress_rate([10.0, 10.0, 10.0], [20.0, 20.0, 20.0], 5) == 0.0
    assert progress_rate([10.0, 5.0], [20.0, 20.0], 5) == pytest.approx(0.5)


def test_levy_steps_shape_and_finite():
    s = levy_steps(np.random.default_rng(0), (100, 4), 1.5)
    assert s.shape == (100, 4) and np.isfinite(s).all()


def test_oioa_respects_budget_and_bounds():
    p = make(2500)
    pop = oioa(p, np.random.default_rng(1))
    assert p.fe == 2500
    assert np.all(pop >= p.lb) and np.all(pop <= p.ub)


def test_oioa_is_deterministic_for_a_seed():
    a, b = make(), make()
    oioa(a, np.random.default_rng(7))
    oioa(b, np.random.default_rng(7))
    assert a.best_f == b.best_f


def test_oioa_improves_on_random_search():
    p = make(5000)
    oioa(p, np.random.default_rng(2))
    rnd = make(5000)
    rnd.evaluate(rnd.random_population(np.random.default_rng(2), 5000))
    assert p.best_f < rnd.best_f


def test_oioa_solves_sphere_to_high_precision():
    p = make(20000, d=5)
    oioa(p, np.random.default_rng(3))
    assert p.best_f < 1e-6


def test_behavior_counts_are_recorded():
    p = make(2000)
    oioa(p, np.random.default_rng(4))
    assert set(p.info["behavior_counts"]) == set(BEHAVIORS)
    assert sum(p.info["behavior_counts"].values()) > 0


def test_warm_start_population_is_used():
    p = make(200)
    oioa(p, np.random.default_rng(5), init_pop=np.zeros((10, 5)))
    assert p.best_f == 0.0


@pytest.mark.parametrize("change", [{"behaviors": ("imitate", "camouflage", "escape")},
                                    {"behaviors": ("imitate", "mimic", "camouflage")},
                                    {"selector": "uniform"}])
def test_variants_run(change):
    p = make(1500)
    make_variant(**change)(p, np.random.default_rng(6))
    assert p.fe == 1500


def test_no_escape_variant_never_escapes():
    p = make(2000)
    make_variant(behaviors=("imitate", "mimic", "camouflage"))(p, np.random.default_rng(8))
    assert p.info["behavior_counts"]["escape"] == 0

import numpy as np
import pytest

from oioa.stats import friedman, holm, mean_ranks, ranksum_counts, ranksum_outcome, wilcoxon_vs_control


def test_mean_ranks_with_ties():
    t = np.array([[1, 2, 3], [1, 1, 3]], float)
    assert np.allclose(mean_ranks(t), [(1 + 1.5) / 2, (2 + 1.5) / 2, 3])


def test_holm_matches_hand_calculation():
    assert np.allclose(holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])
    assert np.all(holm([0.5, 0.9]) <= 1.0)


def test_friedman_detects_consistent_order():
    base = np.random.default_rng(0).random((20, 1))
    t = np.hstack([base, base + 1, base + 2])
    stat, p = friedman(t)
    assert p < 0.001 and stat > 0
    with pytest.raises(ValueError):
        friedman(t[:, :2])


def test_wilcoxon_control_vs_worse_algorithms():
    rng = np.random.default_rng(1)
    c = rng.random(29)
    t = np.column_stack([c, c + 0.5 + rng.random(29) * 0.1, c + 0.2 + rng.random(29) * 0.05])
    rows = wilcoxon_vs_control(t, control=0)
    assert len(rows) == 2 and all(r["p_holm"] < 0.01 and r["control_better"] == 29 for r in rows)


def test_wilcoxon_identical_columns_gives_p_one():
    t = np.column_stack([np.arange(10.0), np.arange(10.0)])
    assert wilcoxon_vs_control(t, 0)[0]["p"] == 1.0


def test_ranksum_win_tie_loss():
    a = np.random.default_rng(2).normal(0, 1, 30)
    assert ranksum_outcome(a, a + 10) == "win"
    assert ranksum_outcome(a + 10, a) == "loss"
    assert ranksum_outcome(a, a + 0.01) == "tie"
    assert ranksum_outcome(np.zeros(30), np.zeros(30)) == "tie"
    assert ranksum_counts([a, a], [a + 10, a]) == {"win": 1, "tie": 1, "loss": 0}

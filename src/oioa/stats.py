"""Statistical helpers used to compare optimizers.

* ``mean_ranks``: average rank of each algorithm across functions (lower error = better rank, ties averaged).
* ``friedman``: Friedman test across functions (scipy).
* ``wilcoxon_vs_control``: paired Wilcoxon signed-rank test of every algorithm against a control over
  functions, with Holm step-down correction.
* ``ranksum_counts``: per-function Mann-Whitney U test (two-sided, alpha=0.05) of an algorithm against a
  control over independent runs, returned as win/tie/loss counts.
"""
from __future__ import annotations

import numpy as np
from scipy import stats


def mean_ranks(table: np.ndarray) -> np.ndarray:
    """``table[f, a]`` = a score (lower is better). Returns mean rank of each algorithm."""
    table = np.asarray(table, dtype=float)
    ranks = np.apply_along_axis(stats.rankdata, 1, table)
    return ranks.mean(axis=0)


def friedman(table: np.ndarray) -> tuple[float, float]:
    """Friedman chi-square statistic and p-value (rows = functions, columns = algorithms)."""
    table = np.asarray(table, dtype=float)
    if table.shape[1] < 3:
        raise ValueError("the Friedman test needs at least 3 algorithms")
    res = stats.friedmanchisquare(*[table[:, j] for j in range(table.shape[1])])
    return float(res.statistic), float(res.pvalue)


def holm(pvalues) -> np.ndarray:
    """Holm step-down adjusted p-values (monotone, capped at 1)."""
    p = np.asarray(pvalues, dtype=float)
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    running = 0.0
    for k, idx in enumerate(order):
        running = max(running, (m - k) * p[idx])
        adj[idx] = min(1.0, running)
    return adj


def wilcoxon_vs_control(table: np.ndarray, control: int) -> list[dict]:
    """Paired Wilcoxon signed-rank test of each algorithm vs ``control`` across functions."""
    table = np.asarray(table, dtype=float)
    rows, raw = [], []
    for j in range(table.shape[1]):
        if j == control:
            continue
        diff = table[:, j] - table[:, control]
        if np.allclose(diff, 0):
            p, w = 1.0, 0.0
        else:
            res = stats.wilcoxon(table[:, j], table[:, control], zero_method="wilcox")
            p, w = float(res.pvalue), float(res.statistic)
        raw.append(p)
        rows.append({"algo_index": j, "p": p, "W": w,
                     "control_better": int(np.sum(table[:, control] < table[:, j])),
                     "control_worse": int(np.sum(table[:, control] > table[:, j]))})
    for r, a in zip(rows, holm(raw)):
        r["p_holm"] = float(a)
    return rows


def ranksum_outcome(control_runs, other_runs, alpha: float = 0.05) -> str:
    """'win' if the control is significantly better (lower), 'loss' if worse, else 'tie'."""
    a, b = np.asarray(control_runs, float), np.asarray(other_runs, float)
    if np.allclose(a, b) and np.std(a) == 0 and np.std(b) == 0:
        return "tie"
    try:
        p = stats.mannwhitneyu(a, b, alternative="two-sided").pvalue
    except ValueError:
        return "tie"
    if p >= alpha:
        return "tie"
    return "win" if np.median(a) < np.median(b) else "loss"


def ranksum_counts(control_by_func: list, other_by_func: list, alpha: float = 0.05) -> dict:
    out = {"win": 0, "tie": 0, "loss": 0}
    for a, b in zip(control_by_func, other_by_func):
        out[ranksum_outcome(a, b, alpha)] += 1
    return out

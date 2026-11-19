"""Budgeted objective wrapper shared by every optimizer.

All algorithms (OIOA and the baselines) evaluate candidates only through
``Problem.evaluate``. That guarantees they all obey the same function-evaluation
budget, and it records the best-so-far curve used for convergence plots.
"""
from __future__ import annotations

from typing import Callable

import numpy as np


class Problem:
    """A bounded minimization problem with an evaluation budget.

    Parameters
    ----------
    fn : callable
        Maps a 1-D vector to a float (lower is better).
    lb, ub : array-like
        Lower and upper bounds (same length = problem dimension).
    max_fe : int
        Maximum number of function evaluations. Rows beyond the budget are not
        evaluated and receive ``inf`` so that algorithms never exceed it.
    n_checkpoints : int
        Number of points stored in ``history`` (best-so-far every max_fe/n evals).
    f_offset : float
        Value subtracted from the objective when recording history and
        ``error`` (CEC functions have a known optimum equal to their bias).
    """

    def __init__(self, fn: Callable[[np.ndarray], float], lb, ub, max_fe: int,
                 n_checkpoints: int = 100, f_offset: float = 0.0, name: str = ""):
        self.fn = fn
        self.lb = np.asarray(lb, dtype=float).copy()
        self.ub = np.asarray(ub, dtype=float).copy()
        if self.lb.shape != self.ub.shape or self.lb.ndim != 1:
            raise ValueError("lb and ub must be 1-D arrays of equal length")
        if np.any(self.ub <= self.lb):
            raise ValueError("every upper bound must exceed its lower bound")
        if max_fe < 1:
            raise ValueError("max_fe must be positive")
        self.dim = int(self.lb.size)
        self.max_fe = int(max_fe)
        self.f_offset = float(f_offset)
        self.name = name
        self.fe = 0
        self.best_f = np.inf
        self.best_x: np.ndarray | None = None
        self._step = max(1, self.max_fe // int(n_checkpoints))
        self._next_cp = self._step
        self.history: list[float] = []   # best-so-far minus f_offset
        self.info: dict = {}             # free-form diagnostics written by algorithms

    # ------------------------------------------------------------------ budget
    @property
    def done(self) -> bool:
        return self.fe >= self.max_fe

    @property
    def remaining(self) -> int:
        return self.max_fe - self.fe

    @property
    def best_error(self) -> float:
        return self.best_f - self.f_offset

    # -------------------------------------------------------------- evaluation
    def evaluate(self, X) -> np.ndarray:
        """Evaluate the rows of ``X`` (stops at the budget; unevaluated rows get inf)."""
        X = np.atleast_2d(np.asarray(X, dtype=float))
        if X.shape[1] != self.dim:
            raise ValueError(f"expected {self.dim} columns, got {X.shape[1]}")
        out = np.full(len(X), np.inf)
        for i in range(len(X)):
            if self.fe >= self.max_fe:
                break
            v = float(self.fn(X[i]))
            if not np.isfinite(v):
                v = np.inf
            self.fe += 1
            out[i] = v
            if v < self.best_f:
                self.best_f = v
                self.best_x = X[i].copy()
            while self.fe >= self._next_cp and len(self.history) < 10_000:
                self.history.append(self.best_f - self.f_offset)
                self._next_cp += self._step
        return out

    def random_population(self, rng: np.random.Generator, n: int) -> np.ndarray:
        """Uniform random population inside the bounds."""
        return self.lb + rng.random((n, self.dim)) * (self.ub - self.lb)

    def clip(self, X: np.ndarray) -> np.ndarray:
        return np.clip(X, self.lb, self.ub)


def prepare_population(problem: Problem, rng: np.random.Generator, init_pop, n: int) -> np.ndarray:
    """Return an ``n x dim`` starting population inside the bounds.

    ``init_pop`` may be None (random), have more rows than ``n`` (first rows are used)
    or fewer rows (the rest is filled randomly).
    """
    if init_pop is None:
        return problem.random_population(rng, n)
    pop = np.asarray(init_pop, dtype=float)[:n]
    if pop.ndim != 2 or pop.shape[1] != problem.dim:
        raise ValueError("init_pop has the wrong shape for this problem")
    if len(pop) < n:
        pop = np.vstack([pop, problem.random_population(rng, n - len(pop))])
    return problem.clip(pop).copy()

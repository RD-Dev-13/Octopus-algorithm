"""Workload and environment scenarios for the dynamic cloud case study.

A scenario is a list of one or two *phases*. Each phase is a ``CloudInstance`` that the optimizer must
solve with half of the evaluation budget. At the change point the environment changes (a burst of
extra tasks, VM degradation, or both) and the optimizer continues from its current population.

All numbers are modelling assumptions chosen for this study; they are not taken from a real provider.
"""
from __future__ import annotations

import numpy as np

from .simulator import CloudInstance

SCENARIOS = ("stable", "burst", "degradation", "combined")

# 8 heterogeneous VMs (MIPS). Faster VMs draw more power and cost more per busy second.
VM_MIPS = np.array([1000, 1000, 1500, 1500, 2000, 2000, 2500, 2500], dtype=float)
P_MAX = 60.0 + 0.06 * VM_MIPS                  # W   -> 120 ... 210
P_IDLE = 0.6 * P_MAX                           # W
PRICE = 1.39e-5 * (VM_MIPS / 1000.0)           # currency units per busy second


def _tasks(rng: np.random.Generator, n: int, mean_gap: float, t0: float = 0.0):
    length = np.clip(rng.lognormal(mean=np.log(6000.0), sigma=0.6, size=n), 500.0, 30000.0)
    arrival = t0 + np.cumsum(rng.exponential(mean_gap, size=n))
    return length, arrival


def _instance(length, arrival, mips) -> CloudInstance:
    order = np.argsort(arrival, kind="stable")
    return CloudInstance(length=np.asarray(length)[order], arrival=np.asarray(arrival)[order],
                         mips=mips.copy(), p_idle=P_IDLE.copy(), p_max=P_MAX.copy(), price=PRICE.copy())


def build_scenario(name: str, seed: int, n_tasks: int = 100) -> list[CloudInstance]:
    """Return the phase instances of a scenario (1 phase for 'stable', 2 otherwise).

    The first ``n_tasks - n_burst`` tasks are always the same; a burst appends ``n_burst`` tasks that
    arrive close together just after the last regular arrival.
    """
    if name not in SCENARIOS:
        raise ValueError(f"unknown scenario '{name}'. Choose from {SCENARIOS}")
    rng = np.random.default_rng([seed, 4242])
    n_burst = 40
    n_regular = n_tasks - n_burst if name in ("burst", "combined") else n_tasks
    length, arrival = _tasks(rng, n_regular, mean_gap=0.4)
    base = _instance(length, arrival, VM_MIPS)
    if name == "stable":
        return [base]
    if name == "degradation":
        slow = VM_MIPS.copy()
        slow[-2:] *= 0.5                                   # the two fastest VMs lose half of their speed
        return [base, _instance(length, arrival, slow)]
    b_len, b_arr = _tasks(rng, n_burst, mean_gap=0.02, t0=float(arrival[-1]))
    burst_len, burst_arr = np.concatenate([length, b_len]), np.concatenate([arrival, b_arr])
    if name == "burst":
        return [base, _instance(burst_len, burst_arr, VM_MIPS)]
    slow = VM_MIPS.copy()
    slow[-2:] *= 0.5
    return [base, _instance(burst_len, burst_arr, slow)]       # combined


def adapt_population(pop: np.ndarray, new_dim: int, rng: np.random.Generator, lb: float, ub: float) -> np.ndarray:
    """Carry a population over to a problem with ``new_dim`` tasks (new tasks get random VMs)."""
    n, d = pop.shape
    if new_dim == d:
        return pop.copy()
    if new_dim < d:
        return pop[:, :new_dim].copy()
    extra = lb + rng.random((n, new_dim - d)) * (ub - lb)
    return np.hstack([pop, extra])

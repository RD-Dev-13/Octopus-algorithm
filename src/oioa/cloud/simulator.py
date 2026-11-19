"""Small, deterministic cloud task-scheduling simulator.

Model (all values are modelling assumptions, not measurements of a real data centre):

* ``n`` independent tasks with a length in million instructions (MI) and an arrival time.
* ``m`` heterogeneous virtual machines with a speed in MIPS.
* Each VM runs its assigned tasks first-in-first-out without pre-emption; a task starts at
  ``max(arrival, time the VM becomes free)`` and runs for ``length / MIPS`` seconds.
* Makespan M: time the last task finishes.
* Energy E: two-state linear power model per VM, ``P_idle`` while idle and ``P_max`` while busy,
  integrated over the makespan: ``E = sum_j [P_idle_j (M - B_j) + P_max_j B_j]`` (joules).
* Cost C: ``sum_j price_j * B_j`` where ``B_j`` is the busy time of VM j.
* Objective: ``f(x) = w1 M/M_ref + w2 E/E_ref + w3 C/C_ref`` with ``w1 + w2 + w3 = 1``. The reference
  values come from the Minimum-Completion-Time heuristic on the same instance, which makes the
  three terms dimensionless and comparable. f = 1 means "as good as MCT".

A continuous search vector ``x`` (one entry per task) is decoded to VM indices by rounding.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class CloudInstance:
    length: np.ndarray            # MI per task, sorted by arrival
    arrival: np.ndarray           # seconds, non-decreasing
    mips: np.ndarray              # VM speeds
    p_idle: np.ndarray            # W
    p_max: np.ndarray             # W
    price: np.ndarray             # currency units per busy second
    weights: tuple = (0.5, 0.3, 0.2)
    _lists: tuple = field(default=None, repr=False)
    _ref: tuple = field(default=None, repr=False)

    def __post_init__(self):
        if not np.isclose(sum(self.weights), 1.0):
            raise ValueError("weights must sum to 1")
        if np.any(np.diff(self.arrival) < 0):
            raise ValueError("tasks must be sorted by arrival time")
        if len(self.length) != len(self.arrival):
            raise ValueError("length and arrival must have the same size")
        self._lists = (self.length.tolist(), self.arrival.tolist(), self.mips.tolist())

    @property
    def n_tasks(self) -> int:
        return len(self.length)

    @property
    def n_vms(self) -> int:
        return len(self.mips)


def decode(x: np.ndarray, n_vms: int) -> np.ndarray:
    """Round a continuous vector to valid VM indices."""
    return np.clip(np.rint(x), 0, n_vms - 1).astype(int)


def simulate(inst: CloudInstance, assign) -> tuple[float, float, float]:
    """Return (makespan, energy, cost) for an assignment (sequence of VM indices)."""
    length, arrival, mips = inst._lists
    m = inst.n_vms
    if len(assign) != inst.n_tasks:
        raise ValueError("assignment must contain one VM index per task")
    ready = [0.0] * m
    busy = [0.0] * m
    for i, j in enumerate(assign):
        if not 0 <= j < m:
            raise ValueError(f"task {i} assigned to invalid VM {j}")
        start = arrival[i] if arrival[i] > ready[j] else ready[j]
        run = length[i] / mips[j]
        ready[j] = start + run
        busy[j] += run
    makespan = max(ready)
    busy_a = np.asarray(busy)
    energy = float(np.sum(inst.p_idle * (makespan - busy_a) + inst.p_max * busy_a))
    cost = float(np.sum(inst.price * busy_a))
    return makespan, energy, cost


def heuristic_assignment(inst: CloudInstance, kind: str) -> np.ndarray:
    """FCFS (earliest-free VM), RR (round robin) or MCT (minimum completion time)."""
    length, arrival, mips = inst._lists
    m = inst.n_vms
    ready = [0.0] * m
    out = np.zeros(inst.n_tasks, dtype=int)
    for i in range(inst.n_tasks):
        if kind == "RR":
            j = i % m
        elif kind == "FCFS":
            j = min(range(m), key=lambda k: ready[k])
        elif kind == "MCT":
            j = min(range(m), key=lambda k: max(arrival[i], ready[k]) + length[i] / mips[k])
        else:
            raise ValueError(f"unknown heuristic '{kind}'")
        out[i] = j
        ready[j] = max(arrival[i], ready[j]) + length[i] / mips[j]
    return out


def reference_values(inst: CloudInstance) -> tuple[float, float, float]:
    if inst._ref is None:
        inst._ref = simulate(inst, heuristic_assignment(inst, "MCT"))
    return inst._ref


def objective(inst: CloudInstance, x: np.ndarray) -> float:
    """Normalised weighted objective for a continuous search vector."""
    M, E, C = simulate(inst, decode(x, inst.n_vms))
    Mr, Er, Cr = reference_values(inst)
    w1, w2, w3 = inst.weights
    return w1 * M / Mr + w2 * E / Er + w3 * C / Cr


def metrics(inst: CloudInstance, x: np.ndarray) -> dict:
    M, E, C = simulate(inst, decode(x, inst.n_vms))
    Mr, Er, Cr = reference_values(inst)
    w1, w2, w3 = inst.weights
    return {"makespan": M, "energy": E, "cost": C, "objective": w1 * M / Mr + w2 * E / Er + w3 * C / Cr}


def make_problem(inst: CloudInstance, max_fe: int):
    """Wrap an instance as a budgeted ``Problem`` (bounds chosen so rounding gives equal-width bins)."""
    from ..problem import Problem
    n = inst.n_tasks
    return Problem(lambda x: objective(inst, x), np.full(n, -0.5), np.full(n, inst.n_vms - 0.5), max_fe,
                   name=f"cloud-n{n}-m{inst.n_vms}")

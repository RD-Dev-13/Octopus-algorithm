"""Quick end-to-end demo (about a minute): OIOA vs two baselines on a sample cloud workload.

    python -m oioa.demo
    python -m oioa.demo --data data/sample --max-fe 5000 --algos OIOA,PSO,DE

It loads data/sample/tasks.csv and vms.csv, runs each optimizer with the same evaluation budget and the
same starting population, and prints makespan, energy, cost and the combined objective (MCT = 1.0).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from .cloud.io import load_instance
from .cloud.simulator import heuristic_assignment, make_problem, metrics
from .registry import get_algorithm


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default="data/sample", help="folder containing tasks.csv and vms.csv")
    ap.add_argument("--max-fe", type=int, default=10_000)
    ap.add_argument("--algos", default="OIOA,PSO,DE")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    folder = Path(args.data)
    if not (folder / "tasks.csv").exists():
        raise SystemExit(f"cannot find {folder / 'tasks.csv'}. Run this command from the repository root, "
                         f"or pass --data <folder>.")
    inst = load_instance(folder)
    print(f"{inst.n_tasks} tasks, {inst.n_vms} VMs, budget {args.max_fe} evaluations\n")
    print(f"{'method':8s} {'makespan(s)':>12s} {'energy(J)':>12s} {'cost':>9s} {'objective':>10s}")
    for h in ("RR", "FCFS", "MCT"):
        m = metrics(inst, np.asarray(heuristic_assignment(inst, h), float))
        print(f"{h:8s} {m['makespan']:12.2f} {m['energy']:12.0f} {m['cost']:9.4f} {m['objective']:10.4f}")
    for name in [a.strip() for a in args.algos.split(",")]:
        problem = make_problem(inst, args.max_fe)
        init = problem.random_population(np.random.default_rng([args.seed, 0]), 50)
        get_algorithm(name)(problem, np.random.default_rng([args.seed, 1]), init)
        m = metrics(inst, problem.best_x)
        print(f"{name:8s} {m['makespan']:12.2f} {m['energy']:12.0f} {m['cost']:9.4f} {m['objective']:10.4f}")
    print("\nobjective < 1.0 means better than the minimum-completion-time heuristic.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

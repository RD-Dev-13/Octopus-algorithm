"""Quick sanity check of all optimizers on simple, un-shifted textbook functions.

These functions are NOT part of CEC 2017. They are used only to confirm that every
implementation converges and respects the budget, and to choose OIOA's constants once
before the benchmark is run (so nothing is tuned on the CEC 2017 functions).

    python -m oioa.experiments.sanity_check --runs 5
"""
from __future__ import annotations

import argparse
import time

import numpy as np

from ..problem import Problem
from ..registry import MAIN_ALGORITHMS, get_algorithm

FUNCS = {
    "sphere": (lambda x: float(np.sum(x ** 2)), -100, 100),
    "rosenbrock": (lambda x: float(np.sum(100 * (x[1:] - x[:-1] ** 2) ** 2 + (1 - x[:-1]) ** 2)), -30, 30),
    "rastrigin": (lambda x: float(10 * len(x) + np.sum(x ** 2 - 10 * np.cos(2 * np.pi * x))), -5.12, 5.12),
    "ackley": (lambda x: float(-20 * np.exp(-0.2 * np.sqrt(np.mean(x ** 2))) - np.exp(np.mean(np.cos(2 * np.pi * x)))
                               + 20 + np.e), -32, 32),
}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dim", type=int, default=10)
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--max-fe", type=int, default=50_000)
    ap.add_argument("--algos", default=",".join(MAIN_ALGORITHMS))
    args = ap.parse_args(argv)
    algos = [a.strip() for a in args.algos.split(",")]
    print(f"{'function':<11}" + "".join(f"{a:>12}" for a in algos) + "   (mean final value over runs)")
    for fname, (fn, lo, hi) in FUNCS.items():
        row = []
        for a in algos:
            vals = []
            for r in range(args.runs):
                p = Problem(fn, np.full(args.dim, lo, float), np.full(args.dim, hi, float), args.max_fe)
                init = p.random_population(np.random.default_rng([r, 7]), 50)
                get_algorithm(a)(p, np.random.default_rng([r, 9]), init)
                assert p.fe <= p.max_fe, f"{a} exceeded the budget"
                vals.append(p.best_f)
            row.append(np.mean(vals))
        print(f"{fname:<11}" + "".join(f"{v:12.3g}" for v in row), flush=True)


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"done in {time.time() - t0:.0f}s")

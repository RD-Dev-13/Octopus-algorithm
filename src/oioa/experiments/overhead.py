"""Measure the optimizer's own run-time cost, separate from the cost of the objective.

Every algorithm runs 100,000 evaluations of a cheap objective (the sphere function, D = 10) and the
wall-clock time is recorded. The time of the same number of raw objective calls is subtracted, so the result
is the bookkeeping overhead per function evaluation. Run it on an otherwise idle machine; timings from a
busy machine are not meaningful.

    python -m oioa.experiments.overhead --repeats 5
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from ..problem import Problem
from ..registry import MAIN_ALGORITHMS, get_algorithm


def sphere(x):
    return float(np.dot(x, x))


def run_once(name: str, seed: int, dim: int, max_fe: int) -> float:
    problem = Problem(sphere, np.full(dim, -100.0), np.full(dim, 100.0), max_fe)
    rng = np.random.default_rng(seed)
    init = problem.random_population(np.random.default_rng([seed, 0]), 50)
    t0 = time.perf_counter()
    get_algorithm(name)(problem, rng, init)
    return time.perf_counter() - t0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--dim", type=int, default=10)
    ap.add_argument("--max-fe", type=int, default=100_000)
    ap.add_argument("--out", default="results/summary/overhead.json")
    args = ap.parse_args(argv)

    pts = np.random.default_rng(1).uniform(-100, 100, (args.max_fe, args.dim))
    base = Problem(sphere, np.full(args.dim, -100.0), np.full(args.dim, 100.0), args.max_fe)
    t0 = time.perf_counter()
    base.evaluate(pts)                                    # cost of the wrapper + objective alone
    raw = time.perf_counter() - t0

    res = {"max_fe": args.max_fe, "dim": args.dim, "repeats": args.repeats, "raw_evaluation_seconds": raw, "algorithms": {}}
    for a in MAIN_ALGORITHMS:
        t = [run_once(a, s, args.dim, args.max_fe) for s in range(args.repeats)]
        res["algorithms"][a] = {"mean_seconds": float(np.mean(t)), "std_seconds": float(np.std(t, ddof=1)),
                                "overhead_us_per_eval": float((np.mean(t) - raw) / args.max_fe * 1e6)}
        print(f"{a:6s} {np.mean(t):7.2f} s  (+{res['algorithms'][a]['overhead_us_per_eval']:.1f} us/eval)", flush=True)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1))
    print("raw evaluation time:", round(raw, 2), "s; wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

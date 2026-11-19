"""Dynamic cloud task-scheduling case study (own Python simulator, not CloudSim).

Each job = (scenario, algorithm, run). Scenarios with a change point have two phases that each get half of
the evaluation budget; phase 2 starts from the phase-1 population (warm start). Reference heuristics
(FCFS, round robin, MCT) are evaluated once per scenario/run on the final phase instance.

    python -m oioa.experiments.run_cloud --runs 30 --workers 8
    python -m oioa.experiments.run_cloud --runs 2 --max-fe 3000 --out results/cloud_smoke
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import zlib
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

from ..cloud.scenarios import SCENARIOS, adapt_population, build_scenario
from ..cloud.simulator import heuristic_assignment, make_problem, metrics
from ..registry import MAIN_ALGORITHMS, get_algorithm

HEURISTICS = ("FCFS", "RR", "MCT")
SCHEMA = 1


def job_path(out: Path, scenario: str, algo: str, run: int) -> Path:
    return out / scenario / f"{algo}_run{run:02d}.json"


def run_job(args):
    scenario, algo, run, max_fe, out = args
    out = Path(out)
    path = job_path(out, scenario, algo, run)
    if path.exists():
        return "skip"
    phases = build_scenario(scenario, seed=run)
    rng = np.random.default_rng([run, 77, 1 + zlib.crc32(algo.encode()) % 100_000])
    init_rng = np.random.default_rng([run, 77, 0])
    per_phase = max_fe // len(phases)
    pop, curves, phase_metrics = None, [], []
    t0 = time.perf_counter()
    for k, inst in enumerate(phases):
        prob = make_problem(inst, per_phase)
        if pop is None:
            start = prob.random_population(init_rng, 50)
        else:
            start = adapt_population(pop, inst.n_tasks, init_rng, prob.lb[0], prob.ub[0])
        pop = get_algorithm(algo)(prob, rng, start)
        curves.append([float(h) for h in prob.history])
        phase_metrics.append(metrics(inst, prob.best_x))
    rec = {"schema": SCHEMA, "scenario": scenario, "algo": algo, "run": run, "max_fe": max_fe,
           "phases": len(phases), "curves": curves, "final": phase_metrics[-1], "phase_metrics": phase_metrics,
           "seconds": time.perf_counter() - t0}
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(rec))
    tmp.replace(path)
    return "done"


def run_heuristics(scenario: str, run: int, out: Path):
    path = job_path(out, scenario, "HEURISTICS", run)
    if path.exists():
        return
    phases = build_scenario(scenario, seed=run)
    rec = {"schema": SCHEMA, "scenario": scenario, "run": run,
           "heuristics": {h: metrics(phases[-1], np.asarray(heuristic_assignment(phases[-1], h), float))
                          for h in HEURISTICS}}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rec))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", type=int, default=30)
    ap.add_argument("--scenarios", default=",".join(SCENARIOS))
    ap.add_argument("--algos", default=",".join(MAIN_ALGORITHMS))
    ap.add_argument("--max-fe", type=int, default=30_000, help="total evaluations per run (split over phases)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", default="results/cloud")
    args = ap.parse_args(argv)

    scenarios = [s.strip() for s in args.scenarios.split(",")]
    algos = [a.strip() for a in args.algos.split(",")]
    for s in scenarios:
        if s not in SCENARIOS:
            raise SystemExit(f"unknown scenario '{s}'; choose from {SCENARIOS}")
    for a in algos:
        get_algorithm(a)
    out = Path(args.out)
    for s in scenarios:
        for r in range(args.runs):
            run_heuristics(s, r, out)
    jobs = [(s, a, r, args.max_fe, str(out)) for s in scenarios for a in algos for r in range(args.runs)]
    todo = [j for j in jobs if not job_path(out, j[0], j[1], j[2]).exists()]
    print(f"{len(jobs)} jobs, {len(todo)} to run on {args.workers} workers", flush=True)
    failed, t0 = 0, time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(run_job, j): j for j in todo}
        for i, fut in enumerate(as_completed(futs), 1):
            try:
                fut.result()
            except Exception as exc:
                failed += 1
                print(f"FAILED {futs[fut][:3]}: {exc!r}", file=sys.stderr, flush=True)
            if i % 50 == 0:
                print(f"[{i}/{len(todo)}] {(time.time() - t0) / 60:.1f} min", flush=True)
    print(f"finished, {failed} failed, {(time.time() - t0) / 60:.1f} min", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

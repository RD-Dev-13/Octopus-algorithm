"""Run optimizers on the CEC 2017 suite. Resumable: finished (algorithm, function, run) jobs are skipped.

Examples
--------
Standard study (D=10, 29 functions, 7 algorithms, 30 runs, 100000 evaluations per run):
    python -m oioa.experiments.run_cec2017 --runs 30 --workers 12

Quick smoke test:
    python -m oioa.experiments.run_cec2017 --funcs 1,4 --runs 2 --max-fe 5000 --out results/smoke

Ablation variants (first 10 runs):
    python -m oioa.experiments.run_cec2017 --algos OIOA-noImitate,OIOA-noMimic,OIOA-noCamouflage,OIOA-noEscape,OIOA-uniform --runs 10
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

from ..benchmark import FUNCTION_IDS, make_cec2017
from ..registry import MAIN_ALGORITHMS, get_algorithm

SCHEMA = 1


def job_path(out: Path, algo: str, func: int, run: int) -> Path:
    return out / algo / f"F{func:02d}_run{run:02d}.json"


def rngs(func: int, run: int, algo: str):
    """Common initial population for all algorithms; separate stream per algorithm."""
    init_rng = np.random.default_rng([func, run, 0])
    algo_rng = np.random.default_rng([func, run, 1 + zlib.crc32(algo.encode()) % 100_000])
    return init_rng, algo_rng


def run_job(args):
    algo, func, run, dim, max_fe, out = args
    out = Path(out)
    path = job_path(out, algo, func, run)
    if path.exists():
        return ("skip", algo, func, run, 0.0)
    t0 = time.perf_counter()
    problem = make_cec2017(func, dim, max_fe)
    init_rng, algo_rng = rngs(func, run, algo)
    init_pop = problem.random_population(init_rng, 50)
    get_algorithm(algo)(problem, algo_rng, init_pop)
    rec = {
        "schema": SCHEMA, "algo": algo, "func": func, "run": run, "dim": dim, "max_fe": max_fe,
        "fe_used": problem.fe, "final_error": problem.best_error, "history": [float(h) for h in problem.history],
        "seconds": time.perf_counter() - t0, "info": problem.info,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(rec))
    tmp.replace(path)
    return ("done", algo, func, run, rec["seconds"])


def parse_funcs(text: str):
    if text == "all":
        return list(FUNCTION_IDS)
    ids = [int(t) for t in text.split(",")]
    bad = [i for i in ids if i not in FUNCTION_IDS]
    if bad:
        raise SystemExit(f"invalid function ids {bad}; valid ids are 1..29")
    return ids


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dim", type=int, default=10)
    ap.add_argument("--runs", type=int, default=30)
    ap.add_argument("--funcs", default="all")
    ap.add_argument("--algos", default=",".join(MAIN_ALGORITHMS))
    ap.add_argument("--max-fe", type=int, default=None, help="default: 10000 * dim")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", default="results/cec2017_D10")
    args = ap.parse_args(argv)

    funcs = parse_funcs(args.funcs)
    algos = [a.strip() for a in args.algos.split(",")]
    for a in algos:
        get_algorithm(a)                                   # fail early on a typo
    max_fe = args.max_fe or 10_000 * args.dim
    out = Path(args.out)
    jobs = [(a, f, r, args.dim, max_fe, str(out)) for r in range(args.runs) for f in funcs for a in algos]
    todo = [j for j in jobs if not job_path(out, j[0], j[1], j[2]).exists()]
    print(f"{len(jobs)} jobs, {len(jobs) - len(todo)} already finished, {len(todo)} to run "
          f"on {args.workers} workers (D={args.dim}, max_fe={max_fe})", flush=True)
    if not todo:
        return 0
    t0, done, failed = time.time(), 0, 0
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_job, j): j for j in todo}
        for fut in as_completed(futures):
            j = futures[fut]
            try:
                fut.result()
                done += 1
            except Exception as exc:                        # keep going; report at the end
                failed += 1
                print(f"FAILED {j[:3]}: {exc!r}", file=sys.stderr, flush=True)
            if (done + failed) % 50 == 0:
                el = time.time() - t0
                rate = (done + failed) / el
                print(f"[{done + failed}/{len(todo)}] {el / 60:.1f} min elapsed, "
                      f"~{(len(todo) - done - failed) / rate / 60:.0f} min left", flush=True)
    print(f"finished: {done} done, {failed} failed, {(time.time() - t0) / 60:.1f} min", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

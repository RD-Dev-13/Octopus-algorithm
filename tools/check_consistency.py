"""Check that the code does what the paper says.

Three kinds of check, each printed as PASS / FAIL:

1. Equations: the paper's formulas are re-implemented here from scratch (straight from the text of Section V)
   and compared with the library on random states.
2. Parameters: the values printed in the paper's tables are compared with the defaults in the code.
3. Experiment and cloud settings stated in Section VI (budget, runs, population, VM list, weights, ...).

    python tools/check_consistency.py            (writes docs/consistency_check.json)
"""
from __future__ import annotations

import inspect
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "paper"))

from oioa import baselines                                           # noqa: E402
from oioa.cloud import scenarios                                     # noqa: E402
from oioa.cloud.simulator import CloudInstance, simulate             # noqa: E402
from oioa.experiments import run_cec2017, run_cloud                  # noqa: E402
from oioa.oioa import (OIOAConfig, behavior_probabilities, behavior_scores, population_diversity,   # noqa: E402
                       progress_rate)
import content_static as S                                           # noqa: E402

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append({"check": name, "pass": bool(ok), "detail": detail})
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not ok else ""))


def table_rows(title_start):
    for b in S.METHOD + S.EXPERIMENT:
        if b[0] == "table" and b[1].startswith(title_start):
            return {r[0]: r[1] for r in b[3]}
    raise KeyError(title_start)


# ----------------------------------------------------------------- 1. equations, re-implemented from the paper
def paper_scores(delta, rho, kappa, cfg):
    u_prog = min(1.0, rho / cfg.rho_ref)
    u_low = 1.0 - delta
    u_stag = min(1.0, kappa / cfg.kappa_max)
    z = [1 + 1.5 * u_prog + (1 - u_low), 0.5 + 2 * u_low, 0.5 + 2 * u_prog,
         (0.5 + 1.5 * u_low + u_stag) if kappa >= cfg.kappa_min else -math.inf]
    return z


def paper_softmax(z, tau=1.0):
    e = [math.exp(v / tau) if math.isfinite(v) else 0.0 for v in z]
    s = sum(e)
    return [v / s for v in e]


def check_equations():
    cfg = OIOAConfig()
    rng = np.random.default_rng(0)
    worst_z = worst_p = 0.0
    for _ in range(500):
        delta, rho, kappa = rng.random(), rng.random() * 0.1, int(rng.integers(0, 20))
        z_code = behavior_scores(delta, rho, np.array([kappa]), cfg)[0]
        z_ref = np.array(paper_scores(delta, rho, kappa, cfg))
        fin = np.isfinite(z_ref)
        worst_z = max(worst_z, float(np.max(np.abs(z_code[fin] - z_ref[fin]))))
        assert np.array_equal(np.isfinite(z_code), fin)
        p_code = behavior_probabilities(delta, rho, np.array([kappa]), cfg)[0]
        worst_p = max(worst_p, float(np.max(np.abs(p_code - np.array(paper_softmax(list(z_ref)))))))
    check("behavior scores equal the paper's four score equations (500 random states)", worst_z < 1e-12, f"{worst_z:.2e}")
    check("softmax probabilities equal exp(z/tau)/sum (500 random states)", worst_p < 1e-12, f"{worst_p:.2e}")

    pop = rng.random((20, 6)) * 10
    diag = 7.3
    ref = np.mean([np.linalg.norm(x - pop.mean(axis=0)) for x in pop]) / diag
    check("diversity = mean distance to centroid / diagonal", abs(population_diversity(pop, diag) - ref) < 1e-12)
    best, worst = [10.0, 8.0, 7.0, 6.5, 6.0, 5.0], [20.0, 19.0, 18.0, 17.0, 16.0, 15.0]
    k = 5
    ref_rho = float(np.clip((best[-1 - k] - best[-1]) / (worst[-1 - k] - best[-1 - k]), 0, 1))
    check("progress = (f_best(t-k) - f_best(t)) / (f_worst(t-k) - f_best(t-k))",
          abs(progress_rate(best, worst, 5) - ref_rho) < 1e-12, f"{progress_rate(best, worst, 5)} vs {ref_rho}")
    check("escape probability is exactly zero below kappa_min and positive from kappa_min",
          behavior_probabilities(0.5, 0.0, np.array([4, 5]), cfg)[:, 3].tolist()[0] == 0
          and behavior_probabilities(0.5, 0.0, np.array([4, 5]), cfg)[1, 3] > 0)


# ---------------------------------------------------------------------------------- 2. parameter tables
def check_parameters():
    cfg = OIOAConfig()
    t = table_rows("TABLE I.")
    pairs = {
        "Population size N": str(cfg.pop_size),
        "Progress window W / reference ρ_ref": f"{cfg.window} generations / {cfg.rho_ref}",
        "Escape thresholds κ_min / κ_max": f"{cfg.kappa_min} / {cfg.kappa_max}",
        "Elite fraction (n_e = 10)": f"{cfg.elite_frac}",
        "Mimic copy probability p_m": f"{cfg.p_mimic}",
        "Camouflage σ_0 / σ_min": f"{cfg.sigma0} / {cfg.sigma_min}",
        "Opposition probability p_opp / Levy β": f"{cfg.p_opposition} / {cfg.levy_beta}",
        "Softmax temperature τ": f"{cfg.temperature:g}",
    }
    for key, expect in pairs.items():
        check(f"Table I '{key}' = code default", t.get(key) == expect, f"paper '{t.get(key)}' vs code '{expect}'")
    n_e = max(2, int(round(cfg.elite_frac * cfg.pop_size)))
    check("elite count n_e = 10 for N = 50", n_e == 10, str(n_e))
    check("camouflage floor spans 1e-2 to 1e-10 of the range",
          cfg.floor_start == -2.0 and cfg.floor_end == -10.0 and "10^{-2} to 10^{-10}" in t["Camouflage floor φ (fraction of range)"])

    sig = lambda f: {k: v.default for k, v in inspect.signature(f).parameters.items() if v.default is not inspect._empty}
    pso = sig(baselines.pso)
    check("PSO: w 0.9 to 0.4, c1 = c2 = 2", (pso["w_max"], pso["w_min"], pso["c1"], pso["c2"]) == (0.9, 0.4, 2.0, 2.0))
    check("DE: F = 0.5, CR = 0.9", (sig(baselines.de)["F"], sig(baselines.de)["CR"]) == (0.5, 0.9))
    check("WOA: b = 1", sig(baselines.woa)["b"] == 1.0)
    check("all baselines use population size 50", baselines.POP_SIZE == 50 and all(
        sig(f)["n"] == 50 for f in (baselines.pso, baselines.gwo, baselines.woa, baselines.hho, baselines.abc, baselines.de)))
    check("PSO maximum velocity is 20% of the range (source check)", "0.2 * span" in inspect.getsource(baselines.pso))
    check("ABC: 25 food sources and limit 25 D (source check)", "n // 2" in inspect.getsource(baselines.abc)
          and "limit = sn * D" in inspect.getsource(baselines.abc))


# ------------------------------------------------------------------ 3. experiment and cloud settings
def check_settings():
    import argparse
    from oioa.registry import MAIN_ALGORITHMS
    ap = inspect.getsource(run_cec2017.main)
    check("CEC study default: 30 runs, D = 10", "--runs\", type=int, default=30" in ap and "--dim\", type=int, default=10" in ap)
    check("CEC budget default is 10,000 x D = 100,000 at D = 10", "10_000 * args.dim" in ap)
    check("seven algorithms in the main study, OIOA first", MAIN_ALGORITHMS == ("OIOA", "PSO", "GWO", "ABC", "WOA", "HHO", "DE"))
    check("same initial population for every algorithm (seed [f, r, 0])", "default_rng([func, run, 0])" in inspect.getsource(run_cec2017.rngs))
    check("CEC floor: errors below 1e-8 treated as zero", "CEC_FLOOR = 1e-8" in Path(ROOT / "src/oioa/experiments/aggregate.py").read_text())

    check("8 VMs with the stated speeds", scenarios.VM_MIPS.tolist() == [1000, 1000, 1500, 1500, 2000, 2000, 2500, 2500])
    check("busy power 60 + 0.06 s, idle 60% of busy",
          np.allclose(scenarios.P_MAX, 60 + 0.06 * scenarios.VM_MIPS) and np.allclose(scenarios.P_IDLE, 0.6 * scenarios.P_MAX))
    check("price proportional to speed", np.allclose(scenarios.PRICE / scenarios.VM_MIPS, scenarios.PRICE[0] / scenarios.VM_MIPS[0]))
    stable, burst = scenarios.build_scenario("stable", 0), scenarios.build_scenario("burst", 0)
    deg, comb = scenarios.build_scenario("degradation", 0), scenarios.build_scenario("combined", 0)
    check("stable: one phase of 100 tasks", len(stable) == 1 and stable[0].n_tasks == 100)
    check("burst: 60 tasks then 100 tasks", [i.n_tasks for i in burst] == [60, 100])
    check("degradation: two fastest VMs at half speed, same tasks",
          np.allclose(deg[1].mips[-2:], deg[0].mips[-2:] / 2) and deg[1].n_tasks == deg[0].n_tasks == 100)
    check("combined: burst plus degradation", [i.n_tasks for i in comb] == [60, 100] and np.allclose(comb[1].mips[-2:], comb[0].mips[-2:] / 2))
    check("objective weights (0.5, 0.3, 0.2)", CloudInstance.__dataclass_fields__["weights"].default == (0.5, 0.3, 0.2))
    check("cloud study default: 30,000 evaluations, 30 runs",
          "default=30_000" in inspect.getsource(run_cloud.main) and "--runs\", type=int, default=30" in inspect.getsource(run_cloud.main))
    lengths = np.concatenate([i.length for i in (scenarios.build_scenario("stable", s)[0] for s in range(40))])
    check("task lengths clipped to 500..30000 MI, median near 6000", lengths.min() >= 500 and lengths.max() <= 30000
          and 5500 < np.median(lengths) < 6500, f"median {np.median(lengths):.0f}")
    inst = CloudInstance(length=np.array([2000.0, 2000.0, 4000.0]), arrival=np.zeros(3), mips=np.array([1000.0, 2000.0]),
                         p_idle=np.array([10.0, 20.0]), p_max=np.array([50.0, 100.0]), price=np.array([1.0, 3.0]))
    M, E, C = simulate(inst, [0, 1, 1])
    check("energy = sum_j [P_idle (M - B_j) + P_max B_j]; cost = sum_j price_j B_j (hand-computed toy case)",
          abs(M - 3) < 1e-12 and abs(E - (10 * 1 + 50 * 2 + 20 * 0 + 100 * 3)) < 1e-9 and abs(C - (1 * 2 + 3 * 3)) < 1e-9)


def main():
    check_equations()
    check_parameters()
    check_settings()
    n_fail = sum(not r["pass"] for r in RESULTS)
    out = ROOT / "docs" / "consistency_check.json"
    out.write_text(json.dumps(RESULTS, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\n{len(RESULTS) - n_fail} of {len(RESULTS)} checks passed; wrote {out}")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())

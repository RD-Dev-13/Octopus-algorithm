"""Turn raw result files into the tables used in the paper (CSV + JSON; no plotting here).

    python -m oioa.experiments.aggregate --cec results/cec2017_D10 --ablation results/ablation --cloud results/cloud

Outputs go to ``results/summary``:
    cec_mean_std.csv        mean and std of the final error per function and algorithm
    cec_summary.json        mean ranks, Friedman, Wilcoxon (Holm) vs OIOA, rank-sum win/tie/loss, counts
    ablation_summary.json   same style for the ablation variants (runs shared with the main OIOA runs)
    cloud_summary.csv       mean objective / makespan / energy / cost per scenario and algorithm
    behavior_usage.csv      share of each behaviour in OIOA (from info.behavior_counts)
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from ..registry import MAIN_ALGORITHMS
from ..stats import friedman, mean_ranks, ranksum_counts, wilcoxon_vs_control

CEC_FLOOR = 1e-8          # CEC convention: errors below 1e-8 are treated as zero


def load_cec(root: Path, algos, max_runs: int | None = None):
    """Return {algo: {func: [final_error per run, ordered by run]}} and OIOA behaviour counts."""
    data = {a: defaultdict(dict) for a in algos}
    usage = defaultdict(lambda: defaultdict(list))
    for a in algos:
        for f in sorted((root / a).glob("F*_run*.json")) if (root / a).exists() else []:
            r = json.loads(f.read_text())
            if max_runs is not None and r["run"] >= max_runs:
                continue
            err = r["final_error"]
            data[a][r["func"]][r["run"]] = 0.0 if err < CEC_FLOOR else err
            if "behavior_counts" in r.get("info", {}):
                usage[a][r["func"]].append(r["info"]["behavior_counts"])
    out = {a: {fn: [runs[k] for k in sorted(runs)] for fn, runs in data[a].items()} for a in algos}
    return out, usage


def complete_functions(data, algos, n_runs):
    return [f for f in range(1, 30) if all(len(data[a].get(f, [])) >= n_runs for a in algos)]


def compare(data, algos, control, n_runs):
    funcs = complete_functions(data, algos, n_runs)
    if not funcs:
        return None
    means = np.array([[np.mean(data[a][f][:n_runs]) for a in algos] for f in funcs])
    res = {"functions": funcs, "n_runs": n_runs, "algorithms": list(algos),
           "mean_rank": dict(zip(algos, mean_ranks(means).round(3).tolist()))}
    if len(algos) >= 3:
        stat, p = friedman(means)
        res["friedman"] = {"chi2": stat, "p": p}
    ci = list(algos).index(control)
    wil = wilcoxon_vs_control(means, ci)
    res["wilcoxon_vs_control"] = {algos[w["algo_index"]]: {k: w[k] for k in ("p", "p_holm", "control_better", "control_worse")}
                                  for w in wil}
    res["ranksum_control_vs"] = {
        a: ranksum_counts([data[control][f][:n_runs] for f in funcs], [data[a][f][:n_runs] for f in funcs])
        for a in algos if a != control}
    return res


def cloud_tables(root: Path):
    rows = []
    for f in root.glob("*/*_run*.json"):
        if f.name.startswith("HEURISTICS"):
            continue
        r = json.loads(f.read_text())
        rows.append({"scenario": r["scenario"], "algo": r["algo"], "run": r["run"], **r["final"]})
    heur = []
    for f in root.glob("*/HEURISTICS_run*.json"):
        r = json.loads(f.read_text())
        for h, m in r["heuristics"].items():
            heur.append({"scenario": r["scenario"], "algo": h, "run": r["run"], **m})
    return pd.DataFrame(rows), pd.DataFrame(heur)


def cloud_stats(both: pd.DataFrame) -> dict:
    """Per scenario: OIOA vs every other method, paired by run (all methods see the same workload in run r).

    Paired Wilcoxon signed-rank test on the objective with Holm correction over the comparisons of a scenario,
    plus how many of the 30 runs OIOA is strictly better / worse, and the mean objective relative to MCT.
    """
    from scipy import stats as sps
    from ..stats import holm
    out = {}
    for sc, g in both.groupby("scenario"):
        piv = g.pivot(index="run", columns="algo", values="objective")
        rows, raw = {}, []
        for a in piv.columns:
            if a == "OIOA":
                continue
            d = piv["OIOA"] - piv[a]
            p = 1.0 if np.allclose(d, 0) else float(sps.wilcoxon(piv["OIOA"], piv[a]).pvalue)
            raw.append(p)
            rows[a] = {"p": p, "oioa_better_runs": int((d < 0).sum()), "oioa_worse_runs": int((d > 0).sum()),
                       "mean_diff": float(d.mean())}
        for a, adj in zip(rows, holm(raw)):
            rows[a]["p_holm"] = float(adj)
        out[sc] = {"n_runs": int(len(piv)), "mean_rank_of_methods": dict(zip(
            piv.columns, np.apply_along_axis(sps.rankdata, 1, piv.to_numpy()).mean(axis=0).round(3).tolist())),
            "oioa_vs": rows}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cec", default="results/cec2017_D10")
    ap.add_argument("--ablation", default="results/ablation")
    ap.add_argument("--cloud", default="results/cloud")
    ap.add_argument("--out", default="results/summary")
    ap.add_argument("--runs", type=int, default=30)
    ap.add_argument("--ablation-runs", type=int, default=10)
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    algos = list(MAIN_ALGORITHMS)

    data, usage = load_cec(Path(args.cec), algos)
    rows = []
    for f in range(1, 30):
        row = {"func": f}
        for a in algos:
            v = data[a].get(f, [])
            row[f"{a}_n"] = len(v)
            row[f"{a}_mean"] = float(np.mean(v)) if v else np.nan
            row[f"{a}_std"] = float(np.std(v, ddof=1)) if len(v) > 1 else np.nan
            row[f"{a}_median"] = float(np.median(v)) if v else np.nan
        rows.append(row)
    pd.DataFrame(rows).to_csv(out / "cec_mean_std.csv", index=False)
    summary = compare(data, algos, "OIOA", args.runs)
    if summary is None:                                   # fall back to the largest complete run count
        for n in range(args.runs - 1, 0, -1):
            summary = compare(data, algos, "OIOA", n)
            if summary and len(summary["functions"]) == 29:
                break
    (out / "cec_summary.json").write_text(json.dumps(summary, indent=1))

    ab = Path(args.ablation)
    if ab.exists():
        variants = sorted(p.name for p in ab.iterdir() if p.is_dir())
        adata, _ = load_cec(ab, variants)
        merged = {"OIOA": {f: v[:args.ablation_runs] for f, v in data["OIOA"].items()}, **adata}
        names = ["OIOA"] + variants
        res = compare(merged, names, "OIOA", args.ablation_runs)
        (out / "ablation_summary.json").write_text(json.dumps(res, indent=1))

    cl = Path(args.cloud)
    if cl.exists():
        df, hdf = cloud_tables(cl)
        both = pd.concat([df, hdf])
        agg = both.groupby(["scenario", "algo"])[["objective", "makespan", "energy", "cost"]].agg(["mean", "std"])
        agg.columns = ["_".join(c) for c in agg.columns]
        agg.reset_index().to_csv(out / "cloud_summary.csv", index=False)
        (out / "cloud_stats.json").write_text(json.dumps(cloud_stats(both), indent=1))

    rows = []
    for fn, lst in usage["OIOA"].items():
        tot = np.sum([[c[k] for k in ("imitate", "mimic", "camouflage", "escape")] for c in lst], axis=0)
        rows.append({"func": fn, **dict(zip(("imitate", "mimic", "camouflage", "escape"), (tot / tot.sum()).round(4)))})
    pd.DataFrame(rows).sort_values("func").to_csv(out / "behavior_usage.csv", index=False)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

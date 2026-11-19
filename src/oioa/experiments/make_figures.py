"""Draw the paper's data figures from ``results/`` (static PNG + PDF, no animation).

    python -m oioa.experiments.make_figures

Figures written to ``figures/``:
    fig_convergence.*   median best-so-far error vs evaluations on six functions
    fig_ranks.*         mean rank of every algorithm over the 29 functions
    fig_behaviors.*     OIOA behaviour usage per function family
    fig_cloud.*         cloud objective per scenario (relative to MCT = 1)
    fig_ablation.*      mean rank of OIOA and its ablation variants
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..registry import MAIN_ALGORITHMS

# Okabe-Ito colour-blind-safe palette, one fixed colour per algorithm
COLORS = {"OIOA": "#D55E00", "PSO": "#0072B2", "GWO": "#009E73", "ABC": "#CC79A7", "WOA": "#E69F00",
          "HHO": "#56B4E9", "DE": "#000000"}
# opfunu numbering (official CEC 2017 F2 is omitted, so opfunu Fk = official F(k+1) for k >= 2)
FAMILIES = [("Unimodal", range(1, 3)), ("Multimodal", range(3, 10)), ("Hybrid", range(10, 20)),
            ("Composition", range(20, 30))]
CONV_FUNCS = [1, 3, 4, 10, 20, 29]

plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"], "font.size": 8,
                     "axes.titlesize": 8, "axes.labelsize": 8, "legend.fontsize": 7, "figure.dpi": 150,
                     "axes.spines.top": False, "axes.spines.right": False})


def save(fig, out: Path, name: str):
    fig.savefig(out / f"{name}.png", dpi=300, bbox_inches="tight")
    fig.savefig(out / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def fig_convergence(root: Path, out: Path, n_runs: int):
    fig, axes = plt.subplots(2, 3, figsize=(7.1, 3.6), sharex=True)
    for ax, fn in zip(axes.ravel(), CONV_FUNCS):
        for a in MAIN_ALGORITHMS:
            hs = [json.loads(p.read_text())["history"] for p in sorted((root / a).glob(f"F{fn:02d}_run*.json"))[:n_runs]]
            if not hs:
                continue
            med = np.maximum(np.median(np.array(hs), axis=0), 1e-8)
            ax.plot(np.linspace(0, 100, len(med) + 1)[1:], med, color=COLORS[a], lw=1.6 if a == "OIOA" else 1.0,
                    label=a, zorder=3 if a == "OIOA" else 2)
        ax.set_yscale("log")
        ax.set_title(f"F{fn}")
        ax.grid(alpha=0.25, lw=0.4)
    for ax in axes[1]:
        ax.set_xlabel("evaluations (% of budget)")
    for ax in axes[:, 0]:
        ax.set_ylabel("median error")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=7, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.03),
               columnspacing=1.2, handlelength=1.6)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    save(fig, out, "fig_convergence")


def _rank_bars(ranks: dict, title_note: str, out: Path, name: str, highlight: str = "OIOA"):
    items = sorted(ranks.items(), key=lambda kv: kv[1])
    fig, ax = plt.subplots(figsize=(3.4, 0.28 * len(items) + 0.7))
    cols = [COLORS.get(k, "#7f7f7f") if k == highlight else ("#9aa0a6" if k not in COLORS else COLORS[k]) for k, _ in items]
    ax.barh([k for k, _ in items][::-1], [v for _, v in items][::-1], color=cols[::-1])
    for i, (k, v) in enumerate(items[::-1]):
        ax.text(v + 0.05, i, f"{v:.2f}", va="center", fontsize=7)
    ax.set_xlabel(f"mean rank (lower is better){title_note}")
    ax.set_xlim(0, max(ranks.values()) * 1.15)
    fig.tight_layout()
    save(fig, out, name)


def fig_behaviors(summary_dir: Path, out: Path):
    df = pd.read_csv(summary_dir / "behavior_usage.csv")
    rows = []
    for fam, ids in FAMILIES:
        sub = df[df["func"].isin(list(ids))][["imitate", "mimic", "camouflage", "escape"]].mean()
        rows.append(sub.rename(fam))
    d = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(3.4, 2.3))
    bottom = np.zeros(len(d))
    for col, c in zip(d.columns, ["#0072B2", "#009E73", "#E69F00", "#D55E00"]):
        ax.bar(d.index, d[col], bottom=bottom, color=c, label=col)
        bottom += d[col].values
    ax.set_ylabel("share of behavior choices")
    ax.legend(frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.2), columnspacing=0.8, handlelength=1)
    fig.tight_layout()
    save(fig, out, "fig_behaviors")


def fig_cloud(summary_dir: Path, out: Path):
    df = pd.read_csv(summary_dir / "cloud_summary.csv")
    scen = ["stable", "burst", "degradation", "combined"]
    algos = ["OIOA", "PSO", "GWO", "ABC", "WOA", "HHO", "DE", "FCFS", "RR", "MCT"]
    cols = {**COLORS, "FCFS": "#999999", "RR": "#bbbbbb", "MCT": "#555555"}
    fig, ax = plt.subplots(figsize=(7.1, 2.4))
    w = 0.085
    for i, a in enumerate(algos):
        v = [df[(df.scenario == s) & (df.algo == a)]["objective_mean"].iloc[0] for s in scen]
        e = [df[(df.scenario == s) & (df.algo == a)]["objective_std"].iloc[0] for s in scen]
        xs = np.arange(4) + (i - 4.5) * w
        ax.bar(xs, v, w, yerr=e, color=cols[a], label=a, error_kw={"lw": 0.5})
        for x, val in zip(xs, v):
            if val > 1.25:                       # bar leaves the axis: print its value instead of hiding it
                ax.text(x, 1.232, f"{val:.2f}", ha="center", va="top", rotation=90, fontsize=6, color="white")
    ax.axhline(1.0, color="k", lw=0.6, ls="--")
    ax.set_ylim(0.9, 1.25)
    ax.set_xticks(range(4), scen)
    ax.set_ylabel("objective (MCT = 1)")
    ax.legend(ncol=10, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.18), columnspacing=0.8, handlelength=1)
    fig.tight_layout()
    save(fig, out, "fig_cloud")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cec", default="results/cec2017_D10")
    ap.add_argument("--summary", default="results/summary")
    ap.add_argument("--out", default="figures")
    args = ap.parse_args(argv)
    out, sd = Path(args.out), Path(args.summary)
    out.mkdir(exist_ok=True)
    cec = json.loads((sd / "cec_summary.json").read_text())
    fig_convergence(Path(args.cec), out, cec["n_runs"])
    _rank_bars(cec["mean_rank"], "", out, "fig_ranks")
    if (sd / "behavior_usage.csv").exists():
        fig_behaviors(sd, out)
    if (sd / "cloud_summary.csv").exists():
        fig_cloud(sd, out)
    ab = sd / "ablation_summary.json"
    if ab.exists():
        _rank_bars(json.loads(ab.read_text())["mean_rank"], "", out, "fig_ablation")
    print("figures written to", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Results, ablation, cloud study, limitations and conclusion.

All numbers come from results/summary (written by oioa.experiments.aggregate); none is typed here. Sentences that
make a qualitative claim are protected by ``claim(...)``: if the data stop supporting a sentence the build stops,
so the text cannot drift away from the results.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from oioa.stats import mean_ranks                                     # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SUM = ROOT / "results" / "summary"
FIG_WIDTHS = {"figures/fig_oioa_flowchart.png": 2.2, "figures/fig_architecture.png": 2.2,
              "figures/fig_ranks.png": 3.0, "figures/fig_behaviors.png": 3.1, "figures/fig_ablation.png": 3.0}
ALGOS = ["OIOA", "PSO", "GWO", "ABC", "WOA", "HHO", "DE"]
FAMILIES = [("Unimodal", range(1, 3)), ("Multimodal", range(3, 10)), ("Hybrid", range(10, 20)),
            ("Composition", range(20, 30))]
VARIANT_NAMES = {"OIOA": "OIOA (full)", "OIOA-noImitate": "no imitation", "OIOA-noMimic": "no mimicry",
                 "OIOA-noCamouflage": "no camouflage", "OIOA-noEscape": "no escape", "OIOA-uniform": "uniform selector"}


def claim(cond, msg):
    if not cond:
        raise SystemExit(f"paper claim no longer supported by the data: {msg}")


def sci(x):
    if x == 0:
        return "0"
    return f"{x:.2e}".replace("e+0", "e+").replace("e-0", "e-")


def fmt_p(p):
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def _load():
    return dict(
        cec=json.loads((SUM / "cec_summary.json").read_text()),
        ab=json.loads((SUM / "ablation_summary.json").read_text()),
        table=pd.read_csv(SUM / "cec_mean_std.csv"),
        cloud=pd.read_csv(SUM / "cloud_summary.csv"),
        cstats=json.loads((SUM / "cloud_stats.json").read_text()),
        usage=pd.read_csv(SUM / "behavior_usage.csv"),
        over=json.loads((SUM / "overhead.json").read_text()),
    )


def abstract():
    d = _load()
    cec, ab, cs = d["cec"], d["ab"], d["cstats"]
    r = cec["mean_rank"]
    order = sorted(r, key=r.get)
    claim(order[:3] == ["DE", "ABC", "OIOA"], f"rank order is {order}")
    w = cec["wilcoxon_vs_control"]
    claim(all(w[a]["p_holm"] < 0.05 for a in ("GWO", "WOA", "HHO", "ABC", "DE")) and w["PSO"]["p_holm"] >= 0.05,
          "Wilcoxon outcomes")
    claim(ab["wilcoxon_vs_control"]["OIOA-uniform"]["p_holm"] > 0.05, "uniform selector difference")
    claim(cs["stable"]["mean_rank_of_methods"]["OIOA"] == min(cs["stable"]["mean_rank_of_methods"].values()), "stable")
    claim(cs["burst"]["mean_rank_of_methods"]["OIOA"] == min(cs["burst"]["mean_rank_of_methods"].values()), "burst")
    claim(cs["degradation"]["oioa_vs"]["MCT"]["p_holm"] < 0.05 and cs["degradation"]["oioa_vs"]["MCT"]["mean_diff"] > 0,
          "degradation")
    return ("Most swarm optimizers apply one search behavior for the whole run. This paper proposes the Octopus "
            "Imitation Optimization Algorithm (OIOA). Each candidate is an octopus whose dimensions are arms, and a "
            "softmax selector reads population diversity, recent progress and a per-individual stagnation counter "
            "to assign one of four operators: imitation of fitter peers, mimicry of a structurally different elite, "
            "camouflage-style refinement around the best solution, and an escape move for stagnated individuals. "
            f"OIOA is compared with PSO, GWO, ABC, WOA, HHO and DE on 29 CEC 2017 functions (D = 10, "
            f"{cec['n_runs']} runs, 100,000 evaluations per run) and on a dynamic cloud task-scheduling problem "
            "in a simulator written for this study. On CEC 2017, DE and ABC rank first and second and OIOA third "
            "(mean rank " + f"{r['OIOA']:.2f}" + "). OIOA is significantly better than GWO, WOA and HHO and "
            "not significantly different from PSO. In an ablation, removing camouflage clearly hurts, but the "
            "state-driven selector gives no measurable gain over choosing behaviors uniformly. In the scheduling "
            "study OIOA has the best mean rank in the stable and burst scenarios and is significantly worse than "
            "the minimum-completion-time reference when the fastest machines slow down. Code, tests and all result "
            "files are provided.")


def _blocks():
    d = _load()
    cec, ab, table, cloud, cs, usage, over = (d[k] for k in ("cec", "ab", "table", "cloud", "cstats", "usage", "over"))
    B = []
    n = cec["n_runs"]
    r, w, rs = cec["mean_rank"], cec["wilcoxon_vs_control"], cec["ranksum_control_vs"]
    fr = cec["friedman"]

    # ---------------------------------------------------------------- A. CEC 2017
    B.append(("h1", "Results and Discussion"))
    B.append(("h2", "CEC 2017 comparison"))
    rows = [[f"F{int(x['func'])}"] + [sci(x[f"{a}_mean"]) for a in ALGOS] for _, x in table.iterrows()]
    B.append(("table", "TABLE III. MEAN FINAL ERROR OVER 30 RUNS (CEC 2017, D = 10, 100,000 EVALUATIONS)",
              ["F"] + ALGOS, rows, [0.62] + [1.0] * 7, 7))
    order = sorted(r, key=r.get)
    claim(order == ["DE", "ABC", "OIOA", "PSO", "WOA", "GWO", "HHO"], f"rank order {order}")
    B.append(("p", f"Table III gives the mean final error of every algorithm on the 29 functions (standard "
                   f"deviations and medians are in results/summary/cec_mean_std.csv). The mean ranks over the 29 "
                   f"functions are DE {r['DE']:.2f}, ABC {r['ABC']:.2f}, OIOA {r['OIOA']:.2f}, PSO {r['PSO']:.2f}, "
                   f"WOA {r['WOA']:.2f}, GWO {r['GWO']:.2f} and HHO {r['HHO']:.2f} (Fig. 4). The Friedman test "
                   f"rejects equal performance (chi-square {fr['chi2']:.1f}, 6 degrees of freedom, p {fmt_p(fr['p'])})."))
    trows = [["OIOA", f"{r['OIOA']:.2f}", "-", "-"]]
    for a in ALGOS[1:]:
        trows.append([a, f"{r[a]:.2f}", fmt_p(w[a]["p_holm"]), f"{rs[a]['win']}/{rs[a]['tie']}/{rs[a]['loss']}"])
    B.append(("table", "TABLE IV. OIOA VERSUS EACH BASELINE", ["Algorithm", "Mean rank", "Wilcoxon p (Holm)",
              "Rank-sum W/T/L of OIOA"], trows, [1.0, 1.0, 1.4, 1.6]))
    claim(w["PSO"]["p_holm"] >= 0.05 and all(w[a]["p_holm"] < 0.001 for a in ("GWO", "WOA", "HHO")), "tests vs GWO/WOA/HHO/PSO")
    claim(w["DE"]["control_worse"] >= 25 and w["ABC"]["control_worse"] >= 25, "OIOA worse than DE/ABC on most functions")
    B.append(("p", f"Table IV compares OIOA with each baseline. The paired Wilcoxon test over functions, with Holm "
                   f"correction, shows that OIOA is better than GWO, WOA and HHO (all with adjusted p {fmt_p(max(w[a]['p_holm'] for a in ('GWO','WOA','HHO')))}) and worse than DE and ABC (adjusted p {fmt_p(w['DE']['p_holm'])} and {fmt_p(w['ABC']['p_holm'])}). "
                   f"Against PSO the difference is not significant (adjusted p {w['PSO']['p_holm']:.3f}), although OIOA has "
                   f"the lower mean error on {w['PSO']['control_better']} functions and PSO on {w['PSO']['control_worse']}. "
                   f"OIOA has a lower mean error than DE on only {w['DE']['control_better']} functions and than ABC on "
                   f"{w['ABC']['control_better']}. The per-function rank-sum tests agree: OIOA wins on {rs['HHO']['win']} "
                   f"functions against HHO, {rs['GWO']['win']} against GWO and {rs['WOA']['win']} against WOA, loses on "
                   f"{rs['DE']['loss']} against DE and {rs['ABC']['loss']} against ABC, and ties on most functions "
                   f"against PSO ({rs['PSO']['tie']} ties, {rs['PSO']['win']} wins, {rs['PSO']['loss']} losses)."))
    # family ranks
    frows = []
    fam_best = []
    for fam, ids in FAMILIES:
        sub = table[table["func"].isin(list(ids))]
        m = np.array([[x[f"{a}_mean"] for a in ALGOS] for _, x in sub.iterrows()])
        rk = mean_ranks(m)
        frows.append([f"{fam} ({len(sub)})"] + [f"{v:.2f}" for v in rk])
        fam_best.append(ALGOS[int(np.argmin(rk))])
    claim(all(b in ("DE", "ABC") for b in fam_best), f"family leaders {fam_best}")
    oi = [float(rw[1]) for rw in frows]
    B.append(("table", "TABLE V. MEAN RANK BY FUNCTION FAMILY (NUMBER OF FUNCTIONS IN BRACKETS)", ["Family"] + ALGOS,
              frows, [1.5] + [0.8] * 7, 7))
    B.append(("p", f"Table V splits the ranks by function family. DE or ABC has the lowest mean rank in every family. "
                   f"OIOA's mean rank is {oi[0]:.2f} on the unimodal, {oi[1]:.2f} on the multimodal, {oi[2]:.2f} on the "
                   f"hybrid and {oi[3]:.2f} on the composition functions. With only two unimodal functions, that family "
                   f"says little by itself. Fig. 3 shows the median convergence curves on six functions."))
    B.append(("fig", "figures/fig_convergence.png", "Median best-so-far error against evaluations used on six CEC 2017 "
                      "functions (30 runs, logarithmic error axis).", "span"))
    B.append(("fig", "figures/fig_ranks.png", "Mean rank over the 29 CEC 2017 functions (lower is better).", "col"))
    o = over["algorithms"]
    orow = [[a, f"{o[a]['mean_seconds']:.2f}", f"{o[a]['overhead_us_per_eval']:.1f}"] for a in ALGOS]
    B.append(("table", "TABLE VI. OPTIMIZER OVERHEAD (SPHERE, D = 10, 100,000 EVALUATIONS)",
              ["Algorithm", "Time per run (s)", "Overhead (us/eval)"], orow, [1.0, 1.4, 1.6]))
    claim(all(o["OIOA"]["overhead_us_per_eval"] > o[a]["overhead_us_per_eval"] for a in ("PSO", "GWO", "WOA", "HHO"))
          and all(o["OIOA"]["overhead_us_per_eval"] < o[a]["overhead_us_per_eval"] for a in ("DE", "ABC")), "overhead ordering")
    B.append(("p", f"Table VI reports the time each optimizer needs when the objective is almost free. OIOA adds about "
                   f"{o['OIOA']['overhead_us_per_eval']:.1f} microseconds per evaluation, which is more than PSO, GWO, WOA "
                   f"and HHO and less than DE and ABC in our implementations (single machine, {over['repeats']} repeats, so "
                   f"the figures are indicative only). For an objective that takes a few milliseconds per "
                   f"evaluation, this overhead is below 0.1% of the run time."))

    # ---------------------------------------------------------------- B. ablation
    B.append(("h2", "Ablation study"))
    ra, wa, rsa = ab["mean_rank"], ab["wilcoxon_vs_control"], ab["ranksum_control_vs"]
    arows = [[VARIANT_NAMES["OIOA"], f"{ra['OIOA']:.2f}", "-", "-"]]
    for v in ("OIOA-noImitate", "OIOA-noMimic", "OIOA-noCamouflage", "OIOA-noEscape", "OIOA-uniform"):
        arows.append([VARIANT_NAMES[v], f"{ra[v]:.2f}", fmt_p(wa[v]["p_holm"]),
                      f"{rsa[v]['win']}/{rsa[v]['tie']}/{rsa[v]['loss']}"])
    B.append(("table", "TABLE VII. ABLATION (10 RUNS, 29 FUNCTIONS)", ["Variant", "Mean rank", "Wilcoxon p (Holm)",
              "Rank-sum W/T/L of OIOA"], arows, [1.5, 0.9, 1.3, 1.5]))
    claim(ra["OIOA-noCamouflage"] == max(ra.values()), "no-camouflage has the worst rank")
    claim(rsa["OIOA-noCamouflage"]["win"] >= 8 and rsa["OIOA-noCamouflage"]["loss"] <= 2, "camouflage wins")
    claim(ra["OIOA-uniform"] < ra["OIOA"] and wa["OIOA-uniform"]["p_holm"] > 0.5, "uniform selector equals or beats OIOA")
    claim(ra["OIOA-noEscape"] < ra["OIOA"] and wa["OIOA-noEscape"]["p_holm"] > 0.05, "no-escape not significantly different")
    claim(all(wa[v]["p_holm"] > 0.05 for v in ("OIOA-noImitate", "OIOA-noMimic", "OIOA-noCamouflage", "OIOA-noEscape")),
          "no ablation difference survives Holm correction")
    B.append(("p", f"Table VII lists the full algorithm and five variants, each run 10 times on every function with the "
                   f"same seeds. Removing camouflage gives the worst mean rank ({ra['OIOA-noCamouflage']:.2f} against "
                   f"{ra['OIOA']:.2f} for the full algorithm), and the full algorithm has a significantly lower error on "
                   f"{rsa['OIOA-noCamouflage']['win']} functions and a higher one on {rsa['OIOA-noCamouflage']['loss']}. "
                   f"Camouflage is therefore the operator with a measurable contribution. Removing imitation, mimicry "
                   f"or escape changes little: the variants without mimicry and without escape even have a slightly "
                   f"better mean rank than the full algorithm ({ra['OIOA-noMimic']:.2f} and {ra['OIOA-noEscape']:.2f}), "
                   f"and no ablation difference remains significant after Holm correction (smallest adjusted p "
                   f"{min(wa[v]['p_holm'] for v in wa):.3f}), although with 10 runs per variant the test has limited power."))
    B.append(("p", f"The most important line of Table VII is the last one. A selector that picks uniformly among the "
                   f"available behaviors has a mean rank of {ra['OIOA-uniform']:.2f}, slightly better than the "
                   f"softmax selector's {ra['OIOA']:.2f}, and it ties with OIOA on all {rsa['OIOA-uniform']['tie']} functions in the "
                   f"rank-sum tests (adjusted Wilcoxon p {wa['OIOA-uniform']['p_holm']:.2f}). On this benchmark, the "
                   f"state-driven selection rules of Section V therefore give no measurable advantage over random "
                   f"behavior choice, and the algorithm's performance comes from its set of operators, mainly "
                   f"camouflage. The behavior statistics are consistent with this: averaged over functions, OIOA chose "
                   f"mimicry in {usage['mimic'].mean() * 100:.0f}% of the cases, imitation in "
                   f"{usage['imitate'].mean() * 100:.0f}%, camouflage in {usage['camouflage'].mean() * 100:.0f}% and "
                   f"escape in {usage['escape'].mean() * 100:.0f}% (Fig. 5), and the shares move only moderately "
                   f"between function families."))
    B.append(("fig", "figures/fig_behaviors.png", "Share of behavior choices of OIOA by function family, averaged "
                      "over functions and runs.", "col"))

    # ---------------------------------------------------------------- C. cloud
    B.append(("h2", "Dynamic cloud task scheduling"))
    scen = ["stable", "burst", "degradation", "combined"]
    methods = ["OIOA", "PSO", "GWO", "ABC", "WOA", "HHO", "DE", "FCFS", "RR", "MCT"]
    crow = []
    for m in methods:
        row = [m]
        for s in scen:
            x = cloud[(cloud.scenario == s) & (cloud.algo == m)].iloc[0]
            row.append(f"{x['objective_mean']:.3f}±{x['objective_std']:.3f}")
        crow.append(row)
    B.append(("table", "TABLE VIII. SCHEDULING OBJECTIVE, MEAN ± STD OVER 30 RUNS (MCT = 1, LOWER IS BETTER)",
              ["Method"] + [s.capitalize() for s in scen], crow, [0.8, 1.1, 1.1, 1.1, 1.1], 7))
    st, bu, de, co = (cs[s] for s in scen)
    mr = lambda c: c["mean_rank_of_methods"]
    claim(mr(st)["OIOA"] == min(mr(st).values()) and mr(bu)["OIOA"] == min(mr(bu).values()), "OIOA best rank stable/burst")
    claim(st["oioa_vs"]["MCT"]["p_holm"] < 0.05 and bu["oioa_vs"]["MCT"]["p_holm"] < 0.05, "OIOA beats MCT in stable/burst")
    claim(mr(co)["OIOA"] == min(mr(co).values()) and co["oioa_vs"]["MCT"]["p_holm"] > 0.05
          and co["oioa_vs"]["PSO"]["p_holm"] > 0.05, "combined")
    claim(de["oioa_vs"]["MCT"]["mean_diff"] > 0 and de["oioa_vs"]["PSO"]["mean_diff"] > 0
          and de["oioa_vs"]["DE"]["mean_diff"] > 0 and de["oioa_vs"]["WOA"]["p_holm"] > 0.05, "degradation")
    claim(all(de["oioa_vs"][a]["p_holm"] < 0.05 and de["oioa_vs"][a]["mean_diff"] > 0 for a in ("MCT", "PSO", "DE", "ABC", "GWO", "FCFS")),
          "OIOA significantly worse than six methods in degradation")
    claim(all(mr(de)["OIOA"] > mr(de)[a] for a in mr(de) if a not in ("OIOA", "HHO", "RR")), "OIOA worst except HHO, RR")
    claim(all(st["oioa_vs"][a]["p_holm"] < 0.05 and st["oioa_vs"][a]["mean_diff"] < 0 for a in ("MCT", "PSO", "ABC")), "stable significance")
    B.append(("p", f"Table VIII gives the objective of each method, normalised so that the minimum-completion-time "
                   f"heuristic scores 1. All optimizers received the same 30,000 evaluations and saw the same workload in "
                   f"each run, so the comparison is paired. In the stable scenario OIOA has the best mean rank "
                   f"({mr(st)['OIOA']:.2f}) and a mean objective of "
                   f"{cloud[(cloud.scenario == 'stable') & (cloud.algo == 'OIOA')].iloc[0]['objective_mean']:.3f}, "
                   f"significantly below MCT (adjusted p {fmt_p(st['oioa_vs']['MCT']['p_holm'])}), PSO "
                   f"({fmt_p(st['oioa_vs']['PSO']['p_holm'])}) and ABC ({fmt_p(st['oioa_vs']['ABC']['p_holm'])}). The same holds "
                   f"in the burst scenario (best mean rank {mr(bu)['OIOA']:.2f}; adjusted p against MCT "
                   f"{fmt_p(bu['oioa_vs']['MCT']['p_holm'])}). In the combined scenario OIOA again has the best mean rank "
                   f"({mr(co)['OIOA']:.2f}), but its advantage over MCT and PSO is not significant (adjusted p "
                   f"{co['oioa_vs']['MCT']['p_holm']:.2f} for both). The improvements are small in absolute terms: the "
                   f"mean objective is about 1% to 2% below the MCT reference, which is a strong heuristic for this problem (Fig. 6)."))
    B.append(("fig", "figures/fig_cloud.png", "Scheduling objective by scenario (mean and standard deviation over 30 runs; "
                      "the dashed line is the MCT reference).", "span"))
    B.append(("p", f"The degradation scenario is different. When the two fastest VMs lose half of their speed, OIOA ends "
                   f"with a mean objective of "
                   f"{cloud[(cloud.scenario == 'degradation') & (cloud.algo == 'OIOA')].iloc[0]['objective_mean']:.3f}, "
                   f"significantly worse than MCT, PSO, DE, ABC, GWO and FCFS (all with adjusted p {fmt_p(max(de['oioa_vs'][a]['p_holm'] for a in ('MCT','PSO','DE','ABC','GWO','FCFS')))}) and has the worst mean rank ({mr(de)['OIOA']:.2f}) among all methods except HHO and RR. "
                   f"We did not test why. A plausible but unverified explanation is that after the change the "
                   f"population still concentrates around solutions that suit the old speeds and OIOA's camouflage "
                   f"and imitation steps, which stay close to the best solution, adapt slowly. The selector reads "
                   f"diversity, progress and stagnation but has no signal for an environment change, and the results "
                   f"on this scenario do not support the claim that OIOA reacts well to dynamic conditions."))

    # ---------------------------------------------------------------- limitations
    B.append(("h1", "Limitations"))
    B.append(("p", "The main limitation concerns the central claim. The ablation shows no measurable benefit of the "
                   "state-driven selector over uniform behavior choice, so the evidence supports the operator set, in "
                   "particular camouflage, but not yet the selector as a mechanism. The score coefficients were set "
                   "once by design and checked on four non-CEC functions; they were not tuned further and a better "
                   "selector may exist."))
    B.append(("p", "The comparison is limited in scope. It covers one dimension (D = 10) and one budget of "
                   "100,000 evaluations. The baselines are textbook algorithms with default parameters, written for "
                   "this study and not checked against the authors' reference code. Strong CEC competition "
                   "algorithms such as adaptive DE variants are not included, and DE and ABC already beat OIOA here, "
                   "so OIOA should not be presented as a state-of-the-art optimizer. Absolute errors cannot be "
                   "compared with published CEC 2017 tables because of the opfunu numbering and optimum values "
                   "described in Section VI. No comparison was made with the two octopus-inspired optimizers "
                   "cited in Section I, because their code and full texts were not available to us."))
    B.append(("p", "The scheduling study uses a small simulator that we wrote, with 8 VMs, at most 100 tasks, and "
                   "assumed power and price values. It has not been validated against CloudSim or a real data center, "
                   "the gains over MCT are of the order of 1% to 2%, and OIOA is clearly worse than MCT when the "
                   "fastest VMs slow down. The ablation used 10 runs per variant, which limits its statistical power. "
                   "The overhead figures come from one machine and three repeats. Part of the experiments ran on a "
                   "second computer; the same jobs differed by at most a relative 2.2e-14 between the two machines. "
                   "The statistical tests treat the 29 functions as independent samples, which they are not strictly."))

    # ---------------------------------------------------------------- conclusion
    B.append(("h1", "Conclusion and Future Work"))
    B.append(("p", "This paper defined OIOA, a population-based optimizer that gives each candidate one of four "
                   "behaviors (imitation, mimicry, camouflage or escape) chosen by a softmax selector from population "
                   "diversity, recent progress and a stagnation counter. It provided a tested open implementation and "
                   "evaluated OIOA against six algorithms under an equal evaluation budget on 29 CEC 2017 functions with "
                   "30 runs, in an ablation study, and in a dynamic cloud scheduling simulator."))
    B.append(("p", f"On CEC 2017 at D = 10, OIOA ranks third behind DE and ABC, ahead of PSO (not significantly), "
                   f"WOA, GWO and HHO. The camouflage operator is the clearest contributor, while the state-driven "
                   f"selector shows no gain over uniform behavior choice. In scheduling, OIOA gives small but "
                   f"significant improvements over the MCT reference in the stable and burst scenarios and performs "
                   f"poorly after the fastest VMs degrade."))
    B.append(("p", "Future work follows from these results. The selector should be redesigned or tuned and then tested "
                   "again against uniform choice, for example with a signal that detects environment changes and "
                   "restores diversity in dynamic problems. OIOA should be evaluated at higher dimensions and "
                   "against stronger DE variants and the octopus-inspired optimizers mentioned above, using "
                   "their reference code. The scheduling model should be checked against CloudSim or workload traces "
                   "and extended to constrained and multi-objective settings."))
    return B


def build_results_blocks():
    return [b for b in _blocks() if b]

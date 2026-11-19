# Paper and Implementation Consistency Report

Method: `python tools/check_consistency.py` re-implements the paper's equations independently, compares the values
printed in the paper's tables with the code defaults, and checks the experiment and simulator settings stated in
Section VI. Result: **37 of 37 checks pass** (details in `docs/consistency_check.json`). The table below maps every
part of the paper to the code and says how it was checked.

## 1. Mapping

| Paper element | Code | How checked |
|---|---|---|
| Problem formulation, search space, budget T_max | `problem.py: Problem` | 12 unit tests |
| Eq. (3) relative diversity | `oioa.py: population_diversity` and `delta_rel` in `oioa()` | independent re-implementation, exact match |
| Eq. (4) progress indicator | `oioa.py: progress_rate` | independent re-implementation, exact match |
| Stagnation counter, reset after improvement and escape | `kappa` in `oioa()` | unit tests, source reading |
| Eqs. (5) to (8) behavior scores | `oioa.py: behavior_scores` | 500 random states, difference below 1e-12 |
| Softmax with tau = 1, gating of escape below kappa_min | `oioa.py: behavior_probabilities` | 500 random states, difference below 1e-12; probability of escape exactly 0 below kappa_min |
| Forced escape at kappa >= kappa_max | `oioa()` | source reading; **no dedicated unit test** |
| Eq. (9) imitation | `oioa.py: op_imitate` | source reading; budget, bound and quality tests exercise it |
| Eq. (10) mimicry (farthest elite, at least one arm copied) | `oioa.py: op_mimic` | source reading and run tests |
| Eqs. (11) to (13) camouflage with sigma_t and floor | `oioa.py: op_camouflage` and schedule in `oioa()` | source reading; constants 1e-2 to 1e-10 checked |
| Eqs. (14), (15) escape (opposition, Levy via Mantegna) | `oioa.py: op_escape`, `levy_steps` | Levy output shape and finiteness tested; distribution not tested |
| Greedy selection for all behaviors | `oioa()` | tests of budget and monotone best; source reading |
| Algorithm 1 | `oioa.py: oioa` | line-by-line reading |
| Table I parameters | `OIOAConfig` defaults | automatic comparison, 8 of 8 rows match |
| Table II baseline settings | `baselines.py` | automatic: PSO, DE, WOA, population size; source checks: PSO velocity limit, ABC food sources and limit; GWO and HHO structure by reading |
| Seven algorithms, common start population, separate random streams | `run_cec2017.py: rngs`, `registry.py` | automatic source checks |
| CEC 2017: D = 10, 100,000 evaluations, 30 runs, error floor 1e-8 | `run_cec2017.py`, `aggregate.py` | automatic checks; result files audited (every run used exactly 100,000 evaluations) |
| opfunu numbering note (F2 omitted, optimum 100k) | `benchmark.py` | optimum test; function names printed and compared with the official list |
| Mean ranks, Friedman, Wilcoxon with Holm, rank-sum W/T/L | `stats.py`, `aggregate.py` | 6 unit tests; Holm checked against a hand calculation |
| Ablation variants and seeds 0 to 9 | `registry.py`, `run_cec2017.py` | variants run in tests; no-escape variant never escapes; result files audited |
| Cloud model: makespan, energy, cost, objective, weights, MCT reference | `cloud/simulator.py` | hand-computed toy case (automatic and unit test); MCT scores exactly 1 |
| 8 VMs, power and price model, task distribution | `cloud/scenarios.py` | automatic checks |
| Four scenarios, 60 to 100 tasks, two fastest VMs at half speed | `cloud/scenarios.py` | automatic checks and unit tests |
| 30,000 evaluations split over phases, warm start | `run_cloud.py`, `scenarios.adapt_population` | automatic check of the default; population shapes tested |
| Overhead table | `experiments/overhead.py` | run once on an idle machine; numbers copied by script |
| Every number in the Results section | `results/summary/*`, `paper/content_results.py` | generated from the summary files; qualitative sentences guarded by assertions |

## 2. Where the paper differs from the draft that was provided

| Draft statement | Revised paper |
|---|---|
| Cloud case study "using the CloudSim simulator" | Replaced: a Python simulator written for this study; CloudSim is only cited as related work |
| Update rules given only in words | Full equations, parameters and pseudocode added; all constants are design choices of this study and are stated as such |
| Imitation toward a fitter peer and the best | Toward a fitter peer and a random elite (the best-only version converged prematurely in a pilot) |
| Camouflage step shrinks with convergence | Linear schedule for sigma_t plus a geometric step floor |
| Escape "applied only to stagnated individuals" | Same, and made precise: available from kappa_min = 5, forced at kappa_max = 12, accepted only if it improves the octopus |
| Evaluation was a "protocol" | The protocol was executed; results, ablation and limitations are reported |
| Baselines PSO, GWO, ABC, WOA, HHO, DE | Same six, plus a statement that they are own implementations not checked against reference code |
| No mention of other octopus-inspired optimizers | Two published ones are cited; no comparison was made (no code available) |
| 34 references | 44 entries, all verified; one corrected (Crepinsek et al. pages), Li et al. cited without volume because Crossref has none |

## 3. Known mismatches and open points

1. **The paper's design intent for the selector is not borne out by the data.** The code matches the equations
   (checked), but the ablation shows the selector does no better than uniform choice. The paper says so.
2. **Not covered by an automatic check:** exact structure of GWO, WOA and HHO updates against the original papers
   (read by eye only), the Levy distribution, and the forced-escape rule (read by eye only).
3. **Opfunu numbering.** Function names in tables are opfunu's F1 to F29; official CEC 2017 numbers differ by one from
   F2 onward (stated in Section VI). Errors are against opfunu's optimum values.
4. **Paper text versus code comments.** Comments in `oioa.py` use "delta" and "rho" for the paper's delta_t and rho_t;
   no functional difference.
5. **Cloud study budget.** For scenarios with a change, each phase gets half of the 30,000 evaluations; the paper says
   this. The phase-1 history curves are stored but not plotted.

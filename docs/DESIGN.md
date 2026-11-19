# Design notes

This file records what the code does and which parts are design choices of this study. The draft paper
defined the idea of OIOA (four behaviors, a state-driven selector) but not its formulas or constants. The
formulas below were written for this implementation and are described in Sections V and VI of the paper.

## Package layout

| Path | Purpose |
|---|---|
| `src/oioa/problem.py` | `Problem`: budgeted objective wrapper shared by every optimizer (counts evaluations, stops at the budget, records best-so-far) |
| `src/oioa/oioa.py` | OIOA: state indicators, behavior selector, four operators, main loop, ablation variants |
| `src/oioa/baselines.py` | PSO, GWO, ABC, WOA, HHO, DE (own NumPy implementations of the original update rules) |
| `src/oioa/registry.py` | name to optimizer lookup used by all scripts |
| `src/oioa/benchmark.py` | CEC 2017 functions through `opfunu` |
| `src/oioa/cloud/` | cloud scheduling simulator, scenarios, CSV loader |
| `src/oioa/stats.py` | mean ranks, Friedman, Wilcoxon with Holm, rank-sum win/tie/loss |
| `src/oioa/experiments/` | experiment drivers: CEC study, cloud study, aggregation, figures, overhead timing |
| `src/oioa/demo.py` | one-minute demo on `data/sample` |
| `tests/` | pytest suite |
| `paper/` | scripts that build the DOCX and PDF |
| `tools/verify_references.py` | Crossref check of the bibliography |

## OIOA

One generation:

1. Rank the octopuses; remember the best.
2. Compute relative diversity `delta` (mean distance to centroid / search-space diagonal, divided by its value at
   generation 0, capped at 1) and progress `rho` (best-fitness gain over the last 5 generations divided by the
   fitness spread 5 generations earlier, clipped to [0, 1]).
3. For each octopus compute scores for the four behaviors, apply a softmax (temperature 1) and sample a behavior.
   Escape needs `kappa >= 5` (otherwise its score is minus infinity) and is forced when `kappa >= 12`.
4. Build one trial vector per octopus with its behavior's operator, clip to the bounds, evaluate.
5. Greedy selection per octopus. `kappa` resets on improvement and after an escape move.

Scores (`u_prog = min(1, rho / 0.02)`, `u_low = 1 - delta`, `u_stag = min(1, kappa / 12)`):

```
imitate    = 1 + 1.5 u_prog + (1 - u_low)
mimic      = 0.5 + 2 u_low
camouflage = 0.5 + 2 u_prog
escape     = 0.5 + 1.5 u_low + u_stag      (only if kappa >= 5)
```

Operators: see Section V of the paper. Details that are easy to miss:

* Imitation picks the peer uniformly among strictly better ranks. The best octopus has no better peer and uses
  itself, so for it the peer term is zero and only the elite term acts.
* The elite set is the best `max(2, round(0.2 N))` octopuses (10 for N = 50).
* Mimicry copies from the farthest elite, and at least one arm is always copied.
* Camouflage samples around the best solution of the current generation. Its step has a geometric floor
  (`1e-2` of the range at the start, `1e-10` at the end) so refinement does not freeze.
* Escape (opposition or Levy jump) also goes through greedy selection.

### Why these choices

* The first version of the algorithm had imitation pull only toward the single best octopus and camouflage had no
  step floor. On a pilot of four non-CEC functions it converged prematurely (sphere error 1.6 to 4.2 after the
  full budget). Pulling toward a random elite and adding the step floor fixed that. No tuning was done on CEC 2017.
* The score coefficients are simple monotone rules (high diversity and progress favor imitation, progress favors
  camouflage, low diversity favors mimicry and escape). They are not claimed to be optimal.

## Baselines

All baselines follow the original update rules with textbook parameters (Table II of the paper) and population
size 50 (ABC: 25 food sources). They were written for this study and were **not** checked against the authors'
reference code. GWO, WOA and HHO keep the original non-elitist population update, so their final population can be
worse than their best-so-far; the reported error is always the best value found, tracked by `Problem`.

## Fairness controls

* One `Problem` wrapper counts evaluations for every algorithm. Rows beyond the budget are not evaluated.
* Run `r` of function `f` gives all algorithms the same initial population (`default_rng([f, r, 0])`).
* Each algorithm has its own random stream (`default_rng([f, r, 1 + crc32(name) % 100000])`).

## CEC 2017 numbering

`opfunu` numbers the suite F1 to F29 and omits official F2. Its `Fk` is the official `F(k+1)` for `k >= 2`, and its
optimum value is `100 k`. Errors are measured against the package's own optimum, so absolute numbers differ from
published CEC 2017 tables.

## Cloud simulator

See Section IV of the paper. All task, VM, power and price values are modeling assumptions for this study. The
simulator is not CloudSim and has not been validated against a real data center or against CloudSim.

## Reproducibility notes

* Results are deterministic per seed on one machine. Across two different processors the same job differed by at
  most a relative 2.2e-14 (floating-point summation order).
* Part of the work (the ablation) was run on a second Windows machine with the same Python and package versions.

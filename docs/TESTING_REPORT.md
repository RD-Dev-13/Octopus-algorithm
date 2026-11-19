# Testing and Verification Report

Date of the final run: 19 November 2026. Environment: Windows 11, Python 3.10.11, NumPy 1.26.4, SciPy 1.15.3,
opfunu 1.0.4, pytest 8.4.2. Everything below was actually run; items that were not run are listed in the last section.

## 1. Status summary

| Component | Status | Evidence |
|---|---|---|
| `Problem` budget wrapper, CEC 2017 loader | Implemented and tested | 12 tests |
| OIOA (indicators, selector, operators, main loop, ablation variants) | Implemented and tested | 21 tests |
| Six baselines and registry | Implemented and tested (behavior: budget, improvement over random search, shared start population) | 16 tests |
| Cloud simulator, scenarios, heuristics | Implemented and tested (hand-computed toy case, reproducibility, scenario shapes) | 14 tests |
| CSV loader and demo | Implemented and tested | 7 tests |
| Statistics helpers | Implemented and tested | 6 tests |
| Experiment drivers (`run_cec2017`, `run_cloud`) | Implemented, run in full; **no unit tests** (checked by smoke runs, exact budget and zero-failure audits below) | section 3 |
| `aggregate.py`, `make_figures.py`, `overhead.py` | Implemented, run on real data; **no unit tests** | section 3 |
| Paper build scripts | Implemented, run; output inspected page by page | section 5 |
| Baselines equal the authors' reference code | **Not verified** | section 6 |
| Cloud simulator against CloudSim / real data | **Not verified** | section 6 |

## 2. Unit tests

Command: `python -m pytest tests -v`. Result: **76 passed, 0 failed** (full output in `docs/pytest_output.txt`).

| File | Tests | What it checks |
|---|---|---|
| `test_problem_benchmark.py` | 12 | evaluation budget never exceeded; unevaluated rows get inf; history length and monotonicity; bad bounds and wrong dimension rejected; clipping; optimum value of five CEC functions equals opfunu's bias; 29 functions available |
| `test_oioa.py` | 21 | probabilities form valid distributions; escape gated by kappa_min; low diversity raises mimic and lowers imitate; progress raises camouflage; disabled behavior has probability 0; uniform selector is uniform; configuration validation; diversity and progress formulas; Levy steps finite; budget and bounds respected; same seed gives same result; beats random search; solves sphere (D = 5) below 1e-6; behavior counts recorded; warm start used; ablation variants run; no-escape variant never escapes |
| `test_baselines.py` | 16 | each of the 7 algorithms respects the budget and beats random search; accepts a common initial population; registry error message; ablation names resolve |
| `test_cloud.py` | 14 | hand-computed makespan, energy and cost on a 2-VM toy case; tasks wait for arrival; invalid assignments raise; decoding; MCT scores exactly 1; heuristics valid; weights must sum to 1; scenarios reproducible and sorted; burst and degradation change what the paper says; population adaptation shapes; OIOA beats round robin |
| `test_stats.py` | 6 | mean ranks with ties; Holm against a hand calculation; Friedman; Wilcoxon vs control; rank-sum win/tie/loss |
| `test_io_demo.py` | 7 | CSV round trip; missing column and non-positive values rejected; unsorted tasks sorted; shipped sample data loads; demo runs; demo error message |

A bug found while testing: pytest 9.2.0 crashed at start-up (`'NodeId' object has no attribute '_str_cache'`)
before running any test. `requirements-dev.txt` now pins `pytest>=8.0,<9`.

## 3. Experiment runs (main workflow)

| Run | Planned | Completed | Failures | Budget audit |
|---|---|---|---|---|
| CEC 2017 main study: 7 algorithms x 29 functions x 30 runs, D = 10 | 6,090 jobs | 6,090 | 0 | every job used exactly 100,000 evaluations; no negative errors |
| Ablation: 5 variants x 29 functions x 10 runs | 1,450 | 1,450 | 0 | every job used exactly 100,000 evaluations |
| Cloud study: 4 scenarios x 7 algorithms x 30 runs (+ 120 heuristic records) | 840 + 120 | 840 + 120 | 0 | evaluations split over phases by the driver |

Notes: the main run was interrupted once (the machine or app restarted after 3,968 jobs); the runner is resumable and
the remaining 2,122 jobs were run with the same command. No partial files were left. The ablation ran on a second
Windows machine (see section 4). Timing: the laptop slept for part of the long runs, so their logged wall-clock times (main study 248 min before
the interruption plus 45 min after it; cloud study 170 min) are not reliable measures of compute cost. The ablation
ran in about 11 minutes of its final session on 28 workers.

`aggregate.py` was first run on partial data to find bugs, then on the final data. `make_figures.py` output was
inspected visually; two defects were found and fixed (legend over curves, clipped bars without labels).

## 4. Cross-checks

* **Two-machine reproducibility.** Four identical jobs (OIOA and DE, F4 and F17, 5,000 evaluations) were run on this
  laptop and on a second Windows PC with identical package versions. Final errors agree to about 13 digits; the largest
  relative difference over the history curves is 2.2e-14 (floating-point summation order).
* **Fresh install.** The repository was copied to an empty folder, a new virtual environment was created, and
  `pip install -r requirements-dev.txt` was followed by the test suite and the demo: 76 passed, demo ran.
  This found nothing to fix but led to pinning `setuptools<81` (opfunu imports `pkg_resources`).
* **Paper versus code.** `tools/check_consistency.py`: 37 of 37 checks pass (see `CONSISTENCY_REPORT.md`).
* **References.** `tools/verify_references.py`: all 44 entries resolve in Crossref (or OpenAlex for Holm 1979); output in
  `docs/reference_check.json`. One draft entry (Crepinsek et al.) first matched the wrong paper in a text search and was
  then verified by DOI.

## 5. Paper build

`python paper/build_paper.py --pdf` produced the DOCX and, through Microsoft Word, the PDF (10 pages, US Letter, two
columns). Every page was rendered and inspected. Problems found and fixed during inspection: raw underscores in inline
math, over-long equations, wrapping table cells, file names turned into subscripts, italic technical-report title.
Remaining cosmetic issue: page 6 ends with unused space before the full-width convergence figure.
Sentences that state qualitative results are guarded by assertions in `paper/content_results.py`, so the build stops if
the data stop supporting a sentence.

## 6. Not done / not verified

* No code-coverage measurement was made.
* No unit tests for the experiment drivers, aggregation, figure and overhead scripts (they were run on real data).
* The baselines were not compared with the authors' reference code. The strong results of DE and ABC may depend on
  implementation details.
* The cloud simulator was not validated against CloudSim, real traces or a real data center.
* Only Python 3.10.11 on Windows 11 was tested.
* Dimensions other than D = 10, other budgets and other benchmark suites were not run.
* The comparison with the two published octopus-inspired optimizers was not made (no code or full text available).
* Overhead timing used one machine and three repeats.

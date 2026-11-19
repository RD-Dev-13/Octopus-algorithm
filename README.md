# OIOA: Octopus Imitation Optimization Algorithm

Python code that accompanies the paper *Octopus Imitation Optimization Algorithm (OIOA): A Behavior-Aware
Bio-Inspired Metaheuristic with Observational Learning, Mimicry and Camouflage Operators*
(Pavankalyan K, Santosh Kumar, R. Rajmohan, SRM Institute of Science and Technology).

OIOA treats each candidate solution as an octopus. Every generation a small selector reads the population
diversity, the recent progress of the best fitness and a per-individual stagnation counter, and gives each
octopus one of four behaviors: **imitate** (move toward a fitter peer and an elite), **mimic** (copy arms from a
structurally different elite), **camouflage** (small steps around the best) or **escape** (opposition or Levy jump
for stagnated individuals).

The repository contains OIOA, six baselines (PSO, GWO, ABC, WOA, HHO, DE), a CEC 2017 experiment driver, a small
cloud task-scheduling simulator with four dynamic scenarios, the statistics used in the paper, tests, and the
scripts that build the paper.

## What is and is not verified

| Item | Status |
|---|---|
| OIOA, baselines, `Problem` budget wrapper, cloud simulator, statistics, CSV loader, demo | Implemented and covered by `pytest` (see `docs/TESTING_REPORT.md`) |
| CEC 2017 study (29 functions, D = 10, 30 runs, 100,000 evaluations, 7 algorithms) | Run in full; results in `results/summary/` and in the paper |
| Ablation (5 variants, 10 runs) and cloud study (4 scenarios, 30 runs) | Run in full |
| Aggregation and figure scripts | Run on the real results; no unit tests |
| Baselines match the authors' original reference code | **Not checked** (own implementations of the published update rules) |
| Cloud simulator against CloudSim or a real data center | **Not validated**; all VM, power and price values are modeling assumptions |
| Other dimensions (30, 50, 100), other benchmarks, constrained problems | **Not run** (future work) |
| Python versions other than 3.10, operating systems other than Windows 10/11 | **Not tested** |

The algorithm's formulas and constants were designed for this study (the draft paper described the idea but not
the equations). See `docs/DESIGN.md`.

## Results in short

CEC 2017 (29 functions, D = 10, 30 runs, 100,000 evaluations), mean rank over functions, lower is better:
DE 1.60, ABC 1.66, **OIOA 3.45**, PSO 4.26, WOA 5.00, GWO 5.07, HHO 6.97. OIOA is significantly better than GWO,
WOA and HHO and significantly worse than DE and ABC; the difference from PSO is not significant (Holm-adjusted
p = 0.053). In the ablation (10 runs per variant), removing the camouflage operator clearly hurts, but the softmax
selector is no better than choosing behaviors uniformly. In the cloud simulator OIOA has the best mean rank in the
stable, burst and combined scenarios (by 1% to 2% of the objective, significant against the MCT reference in stable
and burst only) and is significantly worse than MCT when the two fastest VMs slow down. Full tables are in the paper
and in `results/summary/`. These are the honest results of the runs; they do not show OIOA to be a state-of-the-art
optimizer, and the limitations are listed in the paper.

## Quick start on Windows (no prior setup)

These steps assume nothing is installed. Commands go in **PowerShell** (press the Windows key, type
`PowerShell`, press Enter).

1. **Install Python 3.10.** Download the 64-bit installer from <https://www.python.org/downloads/windows/>
   (choose a 3.10.x release). On the first screen tick **Add python.exe to PATH**, then click *Install Now*.
   Check it worked (close and reopen PowerShell first):

   ```powershell
   python --version
   ```

   It should print `Python 3.10.x`.

2. **Get the code.** Either `git clone <your-repository-url>` or download the ZIP from GitHub and unzip it.
   Then go into the folder (adjust the path):

   ```powershell
   cd C:\Users\you\Downloads\OIOA_project
   ```

3. **Create an isolated environment and install the packages.**

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   python -m pip install -r requirements-dev.txt
   ```

   The prompt now starts with `(.venv)`. Do step 3's `Activate.ps1` line again whenever you open a new PowerShell
   window.

4. **Make the package importable** (once per PowerShell window):

   ```powershell
   $env:PYTHONPATH = "src"
   ```

5. **Run the tests** (about 10 to 30 seconds):

   ```powershell
   python -m pytest tests -q
   ```

   Expected ending: `76 passed`.

6. **Run the one-minute demo** (OIOA, PSO and DE schedule 100 sample tasks onto 8 VMs):

   ```powershell
   python -m oioa.demo
   ```

## Reproducing the experiments

All commands are resumable: if a run is interrupted, start the same command again and finished jobs are skipped.
`--workers` is the number of CPU cores to use; a good value is the number of cores minus 2.

| What | Command | Time we observed |
|---|---|---|
| Sanity check on 4 simple functions | `python -m oioa.experiments.sanity_check --runs 5` | not timed (short) |
| Small CEC test (2 functions, 2 runs) | `python -m oioa.experiments.run_cec2017 --funcs 1,4 --runs 2 --max-fe 5000 --out results\smoke` | under 1 minute |
| **Full CEC 2017 study** | `python -m oioa.experiments.run_cec2017 --runs 30 --workers 14` | about 5 hours on 12 to 14 workers (the laptop slept during part of our run, so this is approximate) |
| Ablation | `python -m oioa.experiments.run_cec2017 --algos OIOA-noImitate,OIOA-noMimic,OIOA-noCamouflage,OIOA-noEscape,OIOA-uniform --runs 10 --workers 14 --out results\ablation` | about 11 minutes on 28 cores of a second PC; expect roughly 1 to 1.5 hours on 14 cores (not measured) |
| Cloud study | `python -m oioa.experiments.run_cloud --runs 30 --workers 8` | 170 min with 3 workers on a busy laptop; expect much less on an idle PC (not measured) |
| Tables and statistics | `python -m oioa.experiments.aggregate` | a few seconds |
| Figures | `python -m oioa.experiments.make_figures` | a few seconds |
| Overhead timing (use an idle machine) | `python -m oioa.experiments.overhead` | about 1 minute |

Output goes to `results/`. The summary files in `results/summary/` are small and are tracked in git; the raw
per-run files are not.

### Build the paper (optional)

```powershell
python -m pip install -r requirements-paper.txt
python paper\build_paper.py --pdf
```

The PDF step needs Microsoft Word installed (Windows). Without Word, build only the DOCX (leave out `--pdf`).

### Use OIOA on your own function

```python
import numpy as np
from oioa.problem import Problem
from oioa.oioa import oioa

f = lambda x: float(np.sum((x - 1.0) ** 2))              # minimize this
problem = Problem(f, lb=[-10] * 5, ub=[10] * 5, max_fe=20_000)
oioa(problem, np.random.default_rng(0))
print(problem.best_f, problem.best_x)
```

### Use your own cloud workload

Create a folder with `tasks.csv` (`task_id,length_mi,arrival_s`) and `vms.csv`
(`vm_id,mips,p_idle_w,p_max_w,price_per_s`) like the ones in `data/sample/`, then:

```powershell
python -m oioa.demo --data path\to\folder
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `python` is not recognized | Python was installed without "Add to PATH". Re-run the installer, choose *Modify*, tick the PATH option, then reopen PowerShell. |
| `Activate.ps1 cannot be loaded because running scripts is disabled` | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, answer `Y`, and try again. |
| `ModuleNotFoundError: No module named 'oioa'` | You forgot `$env:PYTHONPATH = "src"` in this window, or you are not in the repository folder. |
| `ModuleNotFoundError: No module named 'pkg_resources'` | A newer setuptools was installed. Run `python -m pip install "setuptools<81"`. |
| `ImportError: opfunu is required ...` | Run `python -m pip install -r requirements.txt` inside the activated environment. |
| NumPy errors mentioning version 2 | Run `python -m pip install "numpy<2"`; the code was tested with NumPy 1.26. |
| Pytest crashes with `'NodeId' object has no attribute '_str_cache'` | pytest 9.2.0 has that bug. Run `python -m pip install "pytest>=8,<9"`. |
| The full run seems stuck or the laptop sleeps | The runner is resumable. Change Windows power settings so the PC never sleeps while plugged in, and restart the same command. |
| PDF export fails | `docx2pdf` needs Microsoft Word. Open the `.docx` in Word and use *Save As > PDF*. |
| `UserWarning: pkg_resources is deprecated` | Harmless; opfunu still works. It disappears if you keep `setuptools<81`. |
| `The system cannot find the path specified` | Check you are in the repository folder (`pwd`) and that folders such as `results` exist. |

## Repository layout

See `docs/DESIGN.md`. Reports: `docs/TESTING_REPORT.md` and `docs/CONSISTENCY_REPORT.md`.

## License

MIT (see `LICENSE`). The CEC 2017 functions come from the separate `opfunu` package (GPLv3), which is installed
from PyPI and is not distributed here.

## Citing

Please cite the paper. The CEC 2017 benchmark definitions are in Awad et al., "Problem definitions and evaluation
criteria for the CEC 2017 special session and competition on single objective bound constrained real-parameter
numerical optimization," Nanyang Technological University, Singapore, Tech. Rep., 2016.

"""Octopus Imitation Optimization Algorithm (OIOA).

Every candidate solution is an "octopus" whose D dimensions are its "arms".
At every generation a light-weight behaviour selector reads three run-time
indicators and gives each octopus one of four behaviours:

    imitate      move toward a fitter peer and toward the best octopus
    mimic        copy arms from a structurally different elite
    camouflage   small, well-hidden steps around the best octopus
    escape       "ink-jet" relocation (opposition or Levy jump), only for stagnated octopuses

State indicators (see paper Section IV and the design notes in docs/DESIGN.md):

    delta  population diversity: mean distance to the centroid / search-space diagonal,
           divided by its value at generation 0 (so 1.0 = as diverse as the start)
    rho    progress: improvement of the best fitness over the last W generations,
           divided by the fitness spread of the population W generations ago
    kappa  stagnation counter of each octopus (consecutive generations without improvement)

Behaviour probabilities come from a softmax of state-dependent scores. The scores
and every constant below are design choices made for this implementation; they are
all exposed in ``OIOAConfig`` and reported in the paper.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace

import numpy as np

from .problem import Problem, prepare_population

IMITATE, MIMIC, CAMOUFLAGE, ESCAPE = range(4)
BEHAVIORS = ("imitate", "mimic", "camouflage", "escape")


@dataclass(frozen=True)
class OIOAConfig:
    pop_size: int = 50
    window: int = 5               # W: generations used to measure progress
    rho_ref: float = 0.02         # progress that counts as "full" progress
    kappa_min: int = 5            # an octopus may escape only after this many failed generations
    kappa_max: int = 12           # ... and is forced to escape after this many
    elite_frac: float = 0.2       # share of the population treated as elite for mimicry
    p_mimic: float = 0.5          # probability that an arm copies the elite's value
    sigma0: float = 0.5           # camouflage step size at the start of the run
    sigma_min: float = 0.005      # ... and at the end of the run (linear in evaluations used)
    floor_start: float = -2.0     # camouflage minimum step, as log10 of the search range, at the start
    floor_end: float = -10.0      # ... and at the end of the run (geometric decay)
    p_opposition: float = 0.3     # escape: probability of the opposition move (else Levy jump)
    levy_beta: float = 1.5
    temperature: float = 1.0      # softmax temperature
    behaviors: tuple = BEHAVIORS  # enabled behaviours (used by the ablation study)
    selector: str = "softmax"     # "softmax" (OIOA) or "uniform" (ablation: no state awareness)

    def __post_init__(self):
        if self.selector not in ("softmax", "uniform"):
            raise ValueError("selector must be 'softmax' or 'uniform'")
        unknown = set(self.behaviors) - set(BEHAVIORS)
        if unknown or not self.behaviors:
            raise ValueError(f"behaviors must be a non-empty subset of {BEHAVIORS}")
        if self.pop_size < 4:
            raise ValueError("pop_size must be at least 4")
        if not 0 < self.p_mimic <= 1:
            raise ValueError("p_mimic must be in (0, 1]")
        if self.kappa_min > self.kappa_max:
            raise ValueError("kappa_min must not exceed kappa_max")


# --------------------------------------------------------------------- helpers
def population_diversity(pop: np.ndarray, diagonal: float) -> float:
    """Mean distance to the centroid divided by the search-space diagonal."""
    return float(np.mean(np.linalg.norm(pop - pop.mean(axis=0), axis=1)) / diagonal)


def progress_rate(best_hist: list[float], worst_hist: list[float], window: int) -> float:
    """Best-fitness improvement over ``window`` generations / fitness spread at the window start."""
    if len(best_hist) <= 1:
        return 1.0
    k = min(window, len(best_hist) - 1)
    b0, w0, b1 = best_hist[-1 - k], worst_hist[-1 - k], best_hist[-1]
    spread = max(w0 - b0, 1e-12)
    return float(np.clip((b0 - b1) / spread, 0.0, 1.0))


def behavior_scores(delta_rel: float, rho: float, kappa: np.ndarray, cfg: OIOAConfig) -> np.ndarray:
    """Raw scores z[i, b] before the softmax (``-inf`` marks an unavailable behaviour)."""
    u_prog = min(1.0, rho / cfg.rho_ref)
    u_low = 1.0 - float(np.clip(delta_rel, 0.0, 1.0))
    u_stag = np.minimum(1.0, kappa / cfg.kappa_max)
    n = len(kappa)
    z = np.empty((n, 4))
    z[:, IMITATE] = 1.0 + 1.5 * u_prog + 1.0 * (1.0 - u_low)   # progress and diversity favour imitation
    z[:, MIMIC] = 0.5 + 2.0 * u_low                             # low diversity favours mimicry
    z[:, CAMOUFLAGE] = 0.5 + 2.0 * u_prog                       # progress favours local refinement
    z[:, ESCAPE] = np.where(kappa >= cfg.kappa_min, 0.5 + 1.5 * u_low + 1.0 * u_stag, -np.inf)
    for b, name in enumerate(BEHAVIORS):
        if name not in cfg.behaviors:
            z[:, b] = -np.inf
    return z


def behavior_probabilities(delta_rel: float, rho: float, kappa: np.ndarray, cfg: OIOAConfig) -> np.ndarray:
    """P(b | state) for each octopus; rows sum to 1."""
    z = behavior_scores(delta_rel, rho, kappa, cfg)
    if cfg.selector == "uniform":
        p = np.isfinite(z).astype(float)
    else:
        zt = z / cfg.temperature
        zt = zt - np.nanmax(np.where(np.isfinite(zt), zt, -1e300), axis=1, keepdims=True)
        p = np.where(np.isfinite(z), np.exp(zt), 0.0)
    total = p.sum(axis=1, keepdims=True)
    bad = total[:, 0] <= 0
    if np.any(bad):  # cannot happen with >=1 non-escape behaviour enabled; keep a safe fallback
        fallback = np.array([1.0 if n in cfg.behaviors else 0.0 for n in BEHAVIORS])
        p[bad] = fallback
        total = p.sum(axis=1, keepdims=True)
    return p / total


def levy_steps(rng: np.random.Generator, shape: tuple, beta: float) -> np.ndarray:
    """Levy-stable steps with Mantegna's algorithm."""
    sigma_u = (math.gamma(1 + beta) * math.sin(math.pi * beta / 2)
               / (math.gamma((1 + beta) / 2) * beta * 2 ** ((beta - 1) / 2))) ** (1 / beta)
    u = rng.normal(0.0, sigma_u, shape)
    v = rng.normal(0.0, 1.0, shape)
    return u / np.abs(v) ** (1 / beta)


# ----------------------------------------------------------------- the operators
def op_imitate(pop, order, rank, idx, rng, elite_frac):
    g, D = len(idx), pop.shape[1]
    n_elite = max(2, int(round(elite_frac * len(pop))))
    peer_rank = np.floor(rng.random(g) * rank[idx]).astype(int)       # a strictly fitter rank (0 -> itself)
    peers = pop[order[peer_rank]]
    elites = pop[order[rng.integers(n_elite, size=g)]]                # a random elite, not only the best
    x = pop[idx]
    return x + rng.random((g, D)) * (peers - x) + rng.random((g, D)) * (elites - x)


def op_mimic(pop, order, idx, rng, elite_frac, p_mimic):
    g, D = len(idx), pop.shape[1]
    n_elite = max(2, int(round(elite_frac * len(pop))))
    elites = pop[order[:n_elite]]
    x = pop[idx]
    dist = np.linalg.norm(x[:, None, :] - elites[None, :, :], axis=2)     # (g, n_elite)
    chosen = elites[np.argmax(dist, axis=1)]                              # structurally most different elite
    copy = rng.random((g, D)) < p_mimic
    none = ~copy.any(axis=1)
    if np.any(none):
        copy[np.where(none)[0], rng.integers(D, size=int(none.sum()))] = True
    return np.where(copy, chosen, x)


def op_camouflage(pop, idx, best, rng, sigma, floor):
    g, D = len(idx), pop.shape[1]
    n = len(pop)
    r1 = rng.integers(n, size=g)
    r2 = (r1 + rng.integers(1, n, size=g)) % n                             # distinct from r1
    scale = sigma * np.abs(pop[r1] - pop[r2]) + floor                      # floor keeps refinement alive
    return best + rng.standard_normal((g, D)) * scale


def op_escape(pop, idx, best, lb, ub, rng, p_opposition, beta):
    g, D = len(idx), pop.shape[1]
    x = pop[idx]
    opposition = lb + ub - x
    step = np.maximum(np.abs(x - best), 0.01 * (ub - lb))
    jump = x + levy_steps(rng, (g, D), beta) * step
    use_opp = rng.random(g) < p_opposition
    return np.where(use_opp[:, None], opposition, jump)


# ------------------------------------------------------------------- main loop
def oioa(problem: Problem, rng: np.random.Generator, init_pop=None,
         cfg: OIOAConfig | None = None) -> np.ndarray:
    """Run OIOA until the evaluation budget is exhausted; returns the final population."""
    cfg = cfg or OIOAConfig()
    lb, ub = problem.lb, problem.ub
    diagonal = float(np.linalg.norm(ub - lb))
    pop = prepare_population(problem, rng, init_pop, cfg.pop_size)
    n = len(pop)
    fit = problem.evaluate(pop)
    kappa = np.zeros(n, dtype=int)
    delta0 = max(population_diversity(pop, diagonal), 1e-12)
    best_hist, worst_hist = [float(fit.min())], [float(fit[np.isfinite(fit)].max()) if np.isfinite(fit).any() else 0.0]
    counts = np.zeros(4, dtype=int)
    escape_enabled = "escape" in cfg.behaviors

    while not problem.done:
        order = np.argsort(fit)
        rank = np.empty(n, dtype=int)
        rank[order] = np.arange(n)
        best = pop[order[0]].copy()

        delta_rel = min(1.0, population_diversity(pop, diagonal) / delta0)
        rho = progress_rate(best_hist, worst_hist, cfg.window)
        probs = behavior_probabilities(delta_rel, rho, kappa, cfg)
        cum = np.cumsum(probs, axis=1)
        beh = (rng.random((n, 1)) > cum).sum(axis=1).clip(0, 3)
        if escape_enabled:
            beh[kappa >= cfg.kappa_max] = ESCAPE                           # long stagnation forces an escape

        progress = problem.fe / problem.max_fe
        sigma = cfg.sigma_min + (cfg.sigma0 - cfg.sigma_min) * (1.0 - progress)
        floor = (ub - lb) * 10.0 ** (cfg.floor_start - (cfg.floor_start - cfg.floor_end) * progress)

        trial = np.empty_like(pop)
        for b in range(4):
            idx = np.where(beh == b)[0]
            if len(idx) == 0:
                continue
            if b == IMITATE:
                trial[idx] = op_imitate(pop, order, rank, idx, rng, cfg.elite_frac)
            elif b == MIMIC:
                trial[idx] = op_mimic(pop, order, idx, rng, cfg.elite_frac, cfg.p_mimic)
            elif b == CAMOUFLAGE:
                trial[idx] = op_camouflage(pop, idx, best, rng, sigma, floor)
            else:
                trial[idx] = op_escape(pop, idx, best, lb, ub, rng, cfg.p_opposition, cfg.levy_beta)
        trial = np.clip(trial, lb, ub)

        new_fit = problem.evaluate(trial)
        improved = new_fit < fit                                           # greedy selection
        pop[improved] = trial[improved]
        fit[improved] = new_fit[improved]
        kappa = np.where(improved, 0, kappa + 1)
        kappa[beh == ESCAPE] = 0
        counts += np.bincount(beh, minlength=4)
        best_hist.append(float(fit.min()))
        worst_hist.append(float(fit[np.isfinite(fit)].max()))

    problem.info["behavior_counts"] = {name: int(c) for name, c in zip(BEHAVIORS, counts)}
    return pop


def make_variant(**changes):
    """Return an OIOA callable with a modified configuration (used for the ablation study)."""
    cfg = replace(OIOAConfig(), **changes)

    def run(problem, rng, init_pop=None):
        return oioa(problem, rng, init_pop, cfg)

    run.__name__ = "oioa_variant"
    return run

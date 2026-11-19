"""Compact NumPy implementations of the six baseline metaheuristics.

PSO  : Kennedy & Eberhart (1995), linearly decreasing inertia weight
GWO  : Mirjalili et al. (2014)
ABC  : Karaboga & Basturk (2007)
WOA  : Mirjalili & Lewis (2016)
HHO  : Heidari et al. (2019)
DE   : Storn & Price (1997), DE/rand/1/bin

All of them share the signature ``algorithm(problem, rng, init_pop=None) -> final_population``
and obey the evaluation budget of the ``Problem``. Parameters are the common textbook
defaults and are listed in docs/DESIGN.md.
"""
from __future__ import annotations

import math

import numpy as np

from .problem import Problem, prepare_population

POP_SIZE = 50


# ------------------------------------------------------------------------- PSO
def pso(problem: Problem, rng, init_pop=None, n=POP_SIZE, c1=2.0, c2=2.0, w_max=0.9, w_min=0.4):
    span = problem.ub - problem.lb
    vmax = 0.2 * span
    X = prepare_population(problem, rng, init_pop, n)
    V = rng.uniform(-0.1, 0.1, X.shape) * span
    f = problem.evaluate(X)
    pbest, pf = X.copy(), f.copy()
    g = int(np.argmin(pf))
    gbest = pbest[g].copy()
    while not problem.done:
        w = w_max - (w_max - w_min) * problem.fe / problem.max_fe
        r1, r2 = rng.random(X.shape), rng.random(X.shape)
        V = np.clip(w * V + c1 * r1 * (pbest - X) + c2 * r2 * (gbest - X), -vmax, vmax)
        X = problem.clip(X + V)
        f = problem.evaluate(X)
        better = f < pf
        pbest[better], pf[better] = X[better], f[better]
        g = int(np.argmin(pf))
        gbest = pbest[g].copy()
    return X


# ------------------------------------------------------------------------- GWO
def gwo(problem: Problem, rng, init_pop=None, n=POP_SIZE):
    X = prepare_population(problem, rng, init_pop, n)
    f = problem.evaluate(X)
    leaders = X[np.argsort(f)[:3]].copy()
    leader_f = np.sort(f)[:3].copy()
    while not problem.done:
        a = 2.0 * (1.0 - problem.fe / problem.max_fe)
        new = np.zeros_like(X)
        for k in range(3):
            A = 2 * a * rng.random(X.shape) - a
            C = 2 * rng.random(X.shape)
            new += leaders[k] - A * np.abs(C * leaders[k] - X)
        X = problem.clip(new / 3.0)
        f = problem.evaluate(X)
        allx = np.vstack([leaders, X])
        allf = np.concatenate([leader_f, f])
        top = np.argsort(allf)[:3]                      # leaders persist unless beaten
        leaders, leader_f = allx[top].copy(), allf[top].copy()
    return X


# ------------------------------------------------------------------------- WOA
def woa(problem: Problem, rng, init_pop=None, n=POP_SIZE, b=1.0):
    X = prepare_population(problem, rng, init_pop, n)
    f = problem.evaluate(X)
    best = X[int(np.argmin(f))].copy()
    D = X.shape[1]
    while not problem.done:
        a = 2.0 * (1.0 - problem.fe / problem.max_fe)
        A = 2 * a * rng.random(X.shape) - a
        C = 2 * rng.random(X.shape)
        p = rng.random((n, 1))
        l = rng.uniform(-1, 1, (n, 1))
        rand_whale = X[rng.integers(n, size=n)]
        encircle = best - A * np.abs(C * best - X)
        explore = rand_whale - A * np.abs(C * rand_whale - X)
        spiral = np.abs(best - X) * np.exp(b * l) * np.cos(2 * np.pi * l) + best
        use_explore = (np.abs(A).mean(axis=1, keepdims=True) >= 1.0)
        bubble = np.where(use_explore, explore, encircle)
        X = problem.clip(np.where(p < 0.5, bubble, spiral))
        f = problem.evaluate(X)
        if problem.best_x is not None:              # the leader is the best whale found so far
            best = problem.best_x.copy()
    return X


# ------------------------------------------------------------------------- HHO
def _levy_hho(rng, shape, beta=1.5):
    sigma = (math.gamma(1 + beta) * math.sin(math.pi * beta / 2)
             / (math.gamma((1 + beta) / 2) * beta * 2 ** ((beta - 1) / 2))) ** (1 / beta)
    u, v = rng.normal(0, 1, shape) * sigma, rng.normal(0, 1, shape)
    return 0.01 * u / np.abs(v) ** (1 / beta)


def hho(problem: Problem, rng, init_pop=None, n=POP_SIZE):
    lb, ub = problem.lb, problem.ub
    X = prepare_population(problem, rng, init_pop, n)
    f = problem.evaluate(X)
    D = X.shape[1]
    while not problem.done:
        rabbit = X[int(np.argmin(f))].copy()
        t = problem.fe / problem.max_fe
        E = 2 * (2 * rng.random(n) - 1) * (1 - t)
        q, r = rng.random(n), rng.random(n)
        r1, r2, r3, r4, r5 = (rng.random((n, 1)) for _ in range(5))
        Em = E[:, None]
        absE = np.abs(E)
        Xmean = X.mean(axis=0)
        Xrand = X[rng.integers(n, size=n)]
        J = 2 * (1 - r5)

        explore_a = Xrand - r1 * np.abs(Xrand - 2 * r2 * X)
        explore_b = (rabbit - Xmean) - r3 * (lb + r4 * (ub - lb))
        explore = np.where((q >= 0.5)[:, None], explore_a, explore_b)
        soft = (rabbit - X) - Em * np.abs(J * rabbit - X)
        hard = rabbit - Em * np.abs(rabbit - X)

        cand = np.where((absE >= 1)[:, None], explore, X)
        cand = np.where(((r >= 0.5) & (absE < 1) & (absE >= 0.5))[:, None], soft, cand)
        cand = np.where(((r >= 0.5) & (absE < 0.5))[:, None], hard, cand)
        dive_soft = (r < 0.5) & (absE < 1) & (absE >= 0.5)
        dive_hard = (r < 0.5) & (absE < 0.5)
        dive = dive_soft | dive_hard
        Y = np.where(dive_soft[:, None], rabbit - Em * np.abs(J * rabbit - X),
                     rabbit - Em * np.abs(J * rabbit - Xmean))
        Z = Y + rng.random((n, D)) * _levy_hho(rng, (n, D))

        nd = ~dive
        newX, newf = X.copy(), f.copy()
        if nd.any():
            Xn = problem.clip(cand[nd])
            newX[nd], newf[nd] = Xn, problem.evaluate(Xn)
        di = np.where(dive)[0]
        if len(di):
            Yc, Zc = problem.clip(Y[di]), problem.clip(Z[di])
            fy = problem.evaluate(Yc)
            fz = problem.evaluate(Zc)
            take_y = fy < f[di]
            take_z = (~take_y) & (fz < f[di])
            newX[di[take_y]], newf[di[take_y]] = Yc[take_y], fy[take_y]
            newX[di[take_z]], newf[di[take_z]] = Zc[take_z], fz[take_z]
        X, f = newX, newf
    return X


# ------------------------------------------------------------------------- ABC
def abc(problem: Problem, rng, init_pop=None, n=POP_SIZE):
    sn = n // 2                                  # food sources; colony size = 2 * sn = n
    D = problem.dim
    limit = sn * D
    S = prepare_population(problem, rng, init_pop, sn)
    f = problem.evaluate(S)
    trials = np.zeros(sn, dtype=int)

    def neighbour(i):
        k = int(rng.integers(sn - 1))
        k = k + 1 if k >= i else k
        j = int(rng.integers(D))
        v = S[i].copy()
        v[j] = np.clip(S[i, j] + rng.uniform(-1, 1) * (S[i, j] - S[k, j]), problem.lb[j], problem.ub[j])
        return v

    def try_improve(i):
        if problem.done:
            return
        v = neighbour(i)
        fv = problem.evaluate(v)[0]
        if fv < f[i]:
            S[i], f[i], trials[i] = v, fv, 0
        else:
            trials[i] += 1

    while not problem.done:
        for i in range(sn):                                          # employed bees
            try_improve(i)
        fmin = f[np.isfinite(f)].min()
        quality = np.where(f >= 0, 1.0 / (1.0 + (f - min(fmin, 0.0))), 1.0 + np.abs(f))
        prob = quality / quality.sum()
        for _ in range(sn):                                          # onlooker bees
            try_improve(int(rng.choice(sn, p=prob)))
        worst = int(np.argmax(trials))                               # scout bee
        if trials[worst] > limit and not problem.done:
            S[worst] = problem.random_population(rng, 1)[0]
            f[worst] = problem.evaluate(S[worst])[0]
            trials[worst] = 0
    return S


# -------------------------------------------------------------------------- DE
def de(problem: Problem, rng, init_pop=None, n=POP_SIZE, F=0.5, CR=0.9):
    X = prepare_population(problem, rng, init_pop, n)
    f = problem.evaluate(X)
    D = X.shape[1]
    while not problem.done:
        idx = np.array([rng.choice(np.delete(np.arange(n), i), 3, replace=False) for i in range(n)])
        mutant = problem.clip(X[idx[:, 0]] + F * (X[idx[:, 1]] - X[idx[:, 2]]))
        cross = rng.random((n, D)) < CR
        cross[np.arange(n), rng.integers(D, size=n)] = True
        trial = np.where(cross, mutant, X)
        ft = problem.evaluate(trial)
        better = ft < f
        X[better], f[better] = trial[better], ft[better]
    return X

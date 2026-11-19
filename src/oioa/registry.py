"""Name -> optimizer registry used by every experiment script."""
from __future__ import annotations

from .baselines import abc, de, gwo, hho, pso, woa
from .oioa import make_variant, oioa

MAIN_ALGORITHMS = ("OIOA", "PSO", "GWO", "ABC", "WOA", "HHO", "DE")
ABLATION_VARIANTS = ("OIOA-noImitate", "OIOA-noMimic", "OIOA-noCamouflage", "OIOA-noEscape", "OIOA-uniform")

_ALL_BEHAVIORS = ("imitate", "mimic", "camouflage", "escape")


def _without(name: str):
    return make_variant(behaviors=tuple(b for b in _ALL_BEHAVIORS if b != name))


ALGORITHMS = {
    "OIOA": oioa,
    "PSO": pso, "GWO": gwo, "ABC": abc, "WOA": woa, "HHO": hho, "DE": de,
    "OIOA-noImitate": _without("imitate"),
    "OIOA-noMimic": _without("mimic"),
    "OIOA-noCamouflage": _without("camouflage"),
    "OIOA-noEscape": _without("escape"),
    "OIOA-uniform": make_variant(selector="uniform"),
}


def get_algorithm(name: str):
    try:
        return ALGORITHMS[name]
    except KeyError:
        raise ValueError(f"unknown algorithm '{name}'. Available: {', '.join(ALGORITHMS)}") from None

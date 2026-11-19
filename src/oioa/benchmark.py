"""CEC 2017 single-objective benchmark through the ``opfunu`` package.

``opfunu`` numbers the suite F1..F29 and omits the official F2 (it is known to be
unstable), so opfunu F1 = official F1 and opfunu F(k) = official F(k+1) for k >= 2.
In opfunu numbering the global optimum value of Fk is ``100 * k`` (so it differs from the official
table, where F(k+1) has 100*(k+1)); errors are always measured against opfunu's own optimum, which means
absolute values are not comparable with published CEC 2017 tables.
Families in this numbering: F1-2 unimodal, F3-9 simple multimodal, F10-19 hybrid, F20-29 composition.
"""
from __future__ import annotations

from .problem import Problem

FUNCTION_IDS = tuple(range(1, 30))


def _load(func_id: int, dim: int):
    if func_id not in FUNCTION_IDS:
        raise ValueError(f"CEC 2017 function id must be in 1..29, got {func_id}")
    try:
        from opfunu.cec_based import cec2017
    except ImportError as exc:  # pragma: no cover - environment problem
        raise ImportError("opfunu is required for the CEC 2017 suite: pip install opfunu==1.0.4") from exc
    cls = getattr(cec2017, f"F{func_id}2017")
    try:
        return cls(ndim=dim)
    except Exception as exc:
        raise ValueError(f"CEC 2017 F{func_id} is not available for dimension {dim}: {exc}") from exc


def make_cec2017(func_id: int, dim: int = 10, max_fe: int | None = None) -> Problem:
    """Build a budgeted CEC 2017 problem (default budget 10000 * dim evaluations)."""
    f = _load(func_id, dim)
    return Problem(f.evaluate, f.lb, f.ub, max_fe if max_fe else 10_000 * dim,
                   f_offset=float(f.f_bias), name=f"CEC2017-F{func_id}-D{dim}")


def function_name(func_id: int, dim: int = 10) -> str:
    return _load(func_id, dim).name

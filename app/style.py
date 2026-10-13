"""Paleta, orden de modos y utilidades de formato compartidas por las páginas."""

from __future__ import annotations

import math

PALETTE = {
    "B-": "#1f77b4",
    "EC_BP": "#d62728",
    "ALPHA": "#2ca02c",
    "STABLE": "#111111",
    "IT": "#9467bd",
    "OTHER": "#7f7f7f",
    "UNKNOWN": "#c7c7c7",
}

MODE_ORDER = ["B-", "EC_BP", "STABLE", "ALPHA", "IT", "OTHER", "UNKNOWN"]

MODE_LABELS = {
    "B-": "β⁻",
    "EC_BP": "EC / β⁺",
    "ALPHA": "α",
    "STABLE": "Estable",
    "IT": "IT",
    "OTHER": "Otro",
    "UNKNOWN": "Desconocido",
}

QUESTION = (
    "¿Cómo se relaciona la razón $N/Z$ con el modo de desintegración dominante "
    "($\\beta^-$ frente a $\\beta^+$/EC) en los estados base?"
)

_UNITS = [
    (365.25 * 24 * 3600, "a"),
    (24 * 3600, "d"),
    (3600, "h"),
    (60, "min"),
    (1, "s"),
    (1e-3, "ms"),
    (1e-6, "µs"),
    (1e-9, "ns"),
]


def format_half_life(seconds, is_stable=False) -> str:
    if is_stable:
        return "estable"
    if seconds is None or (isinstance(seconds, float) and math.isnan(seconds)):
        return "—"
    for factor, unit in _UNITS:
        if seconds >= factor:
            return f"{seconds / factor:.3g} {unit}"
    return f"{seconds:.3g} s"


def mode_label(mode: str) -> str:
    return MODE_LABELS.get(mode, mode)

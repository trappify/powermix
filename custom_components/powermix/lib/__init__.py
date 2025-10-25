"""Vendoring shim for powermix helpers."""

from __future__ import annotations

try:  # pragma: no cover - only hit when the package is installed
    from powermix.calculator import calculate_other, coerce_float  # type: ignore[import]
except Exception:  # pragma: no cover - fall back to bundled copy
    from ._vendor import calculate_other, coerce_float  # noqa: F401

__all__ = [
    "calculate_other",
    "coerce_float",
]

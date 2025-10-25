"""Numeric helpers used by the Powermix integration."""

from __future__ import annotations

from typing import Iterable, Sequence

NumberLike = float | int | str | None


def coerce_float(value: NumberLike) -> float | None:
    """Best-effort conversion of a state value to ``float``.

    ``None``, ``"unknown"`` or ``"unavailable"`` return ``None``. Strings are
    stripped before conversion and use ``float`` which handles standard decimal
    notation. Any parsing failure also yields ``None`` so callers can decide how
    to treat missing data.
    """

    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"unknown", "unavailable", "none", "nan"}:
            return None
        try:
            return float(text)
        except ValueError:
            return None
    return None


def calculate_other(main: NumberLike, parts: Sequence[NumberLike]) -> float | None:
    """Return the ``main`` value minus the sum of ``parts``.

    ``None`` or unparseable values in ``parts`` are ignored. If ``main`` cannot
    be parsed the function returns ``None``. The result never falls below zero to
    keep the derived sensor from showing negative power consumption when the
    individual sensors temporarily sum to more than the main sensor.
    """

    main_value = coerce_float(main)
    if main_value is None:
        return None

    total = 0.0
    for entry in parts:
        parsed = coerce_float(entry)
        if parsed is not None:
            total += parsed

    remaining = main_value - total
    return max(0.0, round(remaining, 3))

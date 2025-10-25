"""Bundled numeric helpers for Powermix."""

from __future__ import annotations

NumberLike = float | int | str | None


def coerce_float(value: NumberLike) -> float | None:
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


def calculate_other(main: NumberLike, parts: list[NumberLike]) -> float | None:
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

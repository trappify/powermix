from powermix.calculator import calculate_other, coerce_float


def test_coerce_float_handles_numbers_and_strings() -> None:
    assert coerce_float(10) == 10.0
    assert coerce_float(3.14) == 3.14
    assert coerce_float("42.5") == 42.5
    assert coerce_float(" unknown ") is None
    assert coerce_float("garbage") is None
    assert coerce_float(None) is None


def test_calculate_other_with_missing_values() -> None:
    assert calculate_other("100", ["25", "25"]) == 50.0
    assert calculate_other(50, [None, "unavailable"]) == 50.0
    assert calculate_other(None, [1, 2]) is None


def test_calculate_other_never_negative() -> None:
    assert calculate_other(10, [8, 5]) == 0.0


def test_calculate_other_allows_negative_when_requested() -> None:
    assert calculate_other(10, [15], allow_negative=True) == -5.0

from decimal import Decimal

from app.experiments.ztest import compute_z_test


def test_percent_values_can_be_significant():
    result = compute_z_test(Decimal("12"), Decimal("8"), 2000)
    assert result is not None
    assert result["significant"] is True
    assert result["p_value"] < 0.05


def test_missing_fields_yield_null():
    assert compute_z_test(Decimal("12"), None, 1000) is None
    assert compute_z_test(None, Decimal("8"), 1000) is None
    assert compute_z_test(Decimal("12"), Decimal("8"), None) is None


def test_values_outside_rate_range_are_not_tested():
    # 0..1 — доля, 0..100 — процент. 140 уже не ставка.
    assert compute_z_test(Decimal("14"), Decimal("140"), 80) is None


def test_small_n_flags_poor_approximation():
    result = compute_z_test(Decimal("60"), Decimal("50"), 8)
    assert result is not None
    assert result["approximation_poor"] is True

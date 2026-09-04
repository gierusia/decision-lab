from decimal import Decimal

from app.experiments.models import ExperimentVerdict, MetricDirection
from app.experiments.verdict import compute_verdict


def test_higher_success_at_and_above_target():
    assert (
        compute_verdict(
            MetricDirection.HIGHER_IS_BETTER,
            Decimal("100"),
            Decimal("100"),
            Decimal("5"),
        )
        == ExperimentVerdict.SUCCESS
    )
    assert (
        compute_verdict(
            MetricDirection.HIGHER_IS_BETTER,
            Decimal("100"),
            Decimal("101"),
            Decimal("5"),
        )
        == ExperimentVerdict.SUCCESS
    )


def test_higher_partial_band():
    assert (
        compute_verdict(
            MetricDirection.HIGHER_IS_BETTER,
            Decimal("100"),
            Decimal("95"),
            Decimal("5"),
        )
        == ExperimentVerdict.PARTIAL
    )
    assert (
        compute_verdict(
            MetricDirection.HIGHER_IS_BETTER,
            Decimal("100"),
            Decimal("99.9"),
            Decimal("5"),
        )
        == ExperimentVerdict.PARTIAL
    )


def test_higher_failed_below_band():
    assert (
        compute_verdict(
            MetricDirection.HIGHER_IS_BETTER,
            Decimal("100"),
            Decimal("94.9"),
            Decimal("5"),
        )
        == ExperimentVerdict.FAILED
    )


def test_higher_zero_tolerance_has_no_partial():
    assert (
        compute_verdict(
            MetricDirection.HIGHER_IS_BETTER,
            Decimal("100"),
            Decimal("99.9"),
            Decimal("0"),
        )
        == ExperimentVerdict.FAILED
    )


def test_lower_success_partial_failed():
    assert (
        compute_verdict(
            MetricDirection.LOWER_IS_BETTER,
            Decimal("200"),
            Decimal("200"),
            Decimal("10"),
        )
        == ExperimentVerdict.SUCCESS
    )
    assert (
        compute_verdict(
            MetricDirection.LOWER_IS_BETTER,
            Decimal("200"),
            Decimal("220"),
            Decimal("10"),
        )
        == ExperimentVerdict.PARTIAL
    )
    assert (
        compute_verdict(
            MetricDirection.LOWER_IS_BETTER,
            Decimal("200"),
            Decimal("221"),
            Decimal("10"),
        )
        == ExperimentVerdict.FAILED
    )


def test_lower_target_zero_any_error_is_failed():
    assert (
        compute_verdict(
            MetricDirection.LOWER_IS_BETTER,
            Decimal("0"),
            Decimal("0"),
            Decimal("10"),
        )
        == ExperimentVerdict.SUCCESS
    )
    assert (
        compute_verdict(
            MetricDirection.LOWER_IS_BETTER,
            Decimal("0"),
            Decimal("1"),
            Decimal("10"),
        )
        == ExperimentVerdict.FAILED
    )

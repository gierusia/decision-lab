"""Детерминированный вердикт по цели, факту, направлению и допуску промаха.

partial — это не «набрали большую часть цели», а лента промаха p%
вокруг цели. p=0 → ленты нет, только success/failed.
"""

from decimal import Decimal

from app.experiments.models import ExperimentVerdict, MetricDirection

_HUNDRED = Decimal("100")


def compute_verdict(
    direction: MetricDirection,
    target: Decimal,
    actual: Decimal,
    tolerance_percent: Decimal,
) -> ExperimentVerdict:
    if direction == MetricDirection.HIGHER_IS_BETTER:
        if actual >= target:
            return ExperimentVerdict.SUCCESS
        floor = target * (1 - tolerance_percent / _HUNDRED)
        if actual >= floor:
            return ExperimentVerdict.PARTIAL
        return ExperimentVerdict.FAILED

    if actual <= target:
        return ExperimentVerdict.SUCCESS
    ceiling = target * (1 + tolerance_percent / _HUNDRED)
    if actual <= ceiling:
        return ExperimentVerdict.PARTIAL
    return ExperimentVerdict.FAILED

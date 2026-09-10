"""Одновыборочный z-тест доли. Не заменяет вердикт.

Считаем только если есть actual, baseline и n, и оба значения —
либо доли 0..1, либо проценты 0..100. Иначе None.
"""

from __future__ import annotations

import math
from decimal import Decimal


def _pair_to_proportions(actual: Decimal, baseline: Decimal) -> tuple[float, float] | None:
    a = float(actual)
    b = float(baseline)
    if a < 0 or b < 0:
        return None
    if a <= 1 and b <= 1:
        return a, b
    if a <= 100 and b <= 100:
        return a / 100.0, b / 100.0
    return None


def compute_z_test(
    actual: Decimal | None,
    baseline: Decimal | None,
    sample_size: int | None,
) -> dict | None:
    if actual is None or baseline is None or sample_size is None:
        return None
    if sample_size < 1:
        return None
    pair = _pair_to_proportions(actual, baseline)
    if pair is None:
        return None
    p, p0 = pair
    variance = p0 * (1.0 - p0)
    if variance <= 0:
        return None
    se = math.sqrt(variance / sample_size)
    z = (p - p0) / se
    p_value = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(z) / math.sqrt(2.0))))
    return {
        "z": round(z, 4),
        "p_value": round(p_value, 4),
        "significant": p_value < 0.05,
        "approximation_poor": sample_size * p0 < 5 or sample_size * (1.0 - p0) < 5,
    }

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.dashboard.filters import DashboardFilters, as_utc
from app.dashboard.readiness import DecisionReadiness, get_decision_readiness
from app.dashboard.stale import is_stale, stale_after_at
from app.decisions.models import DecisionStatus


NOW = datetime(2026, 9, 4, 12, 0, tzinfo=timezone.utc)


def _decision(status: DecisionStatus, updated_at: datetime):
    return SimpleNamespace(status=status, updated_at=updated_at)


def test_naive_datetimes_are_interpreted_as_utc():
    naive = datetime(2026, 9, 4, 12, 0)

    assert as_utc(naive) == NOW
    assert DashboardFilters(date_from=naive).date_from == NOW


def test_filter_dates_are_normalized_and_bounds_are_inclusive():
    eastern = datetime(2026, 9, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    filters = DashboardFilters(date_from=eastern, date_to=NOW)

    assert filters.date_from == NOW
    assert filters.date_to == NOW


def test_filter_rejects_invalid_range_and_pagination():
    with pytest.raises(ValueError, match="date_from"):
        DashboardFilters(date_from=NOW, date_to=NOW - timedelta(seconds=1))
    with pytest.raises(ValueError, match="limit"):
        DashboardFilters(limit=101)
    with pytest.raises(ValueError, match="offset"):
        DashboardFilters(offset=-1)


def test_decision_at_stale_threshold_is_not_stale():
    decision = _decision(DecisionStatus.ACTIVE, NOW - timedelta(days=30))

    assert is_stale(decision, 30, NOW) is False
    assert stale_after_at(decision, 30) == NOW


def test_decision_older_than_stale_threshold_is_stale():
    decision = _decision(DecisionStatus.ACTIVE, NOW - timedelta(days=30, seconds=1))

    assert is_stale(decision, 30, NOW) is True


@pytest.mark.parametrize("status", [DecisionStatus.COMPLETED, DecisionStatus.CANCELLED])
def test_terminal_decisions_are_never_stale(status):
    decision = _decision(status, NOW - timedelta(days=365))

    assert stale_after_at(decision, 30) is None
    assert is_stale(decision, 30, NOW) is False


@pytest.mark.parametrize(
    ("status", "open_experiments", "expected"),
    [
        (DecisionStatus.COMPLETED, 1, DecisionReadiness.CLOSED),
        (DecisionStatus.CANCELLED, 0, DecisionReadiness.CLOSED),
        (DecisionStatus.ACTIVE, 1, DecisionReadiness.BLOCKED_BY_OPEN_EXPERIMENTS),
        (
            DecisionStatus.NEEDS_REVISION,
            1,
            DecisionReadiness.BLOCKED_BY_OPEN_EXPERIMENTS,
        ),
        (DecisionStatus.DRAFT, 0, DecisionReadiness.DRAFT),
        (DecisionStatus.NEEDS_REVISION, 0, DecisionReadiness.NEEDS_REVISION),
        (DecisionStatus.ACTIVE, 0, DecisionReadiness.READY_TO_CLOSE),
    ],
)
def test_readiness_priority(status, open_experiments, expected):
    assert get_decision_readiness(status, open_experiments) == expected


def test_readiness_rejects_negative_open_experiment_count():
    with pytest.raises(ValueError, match="open_experiment_count"):
        get_decision_readiness(DecisionStatus.ACTIVE, -1)

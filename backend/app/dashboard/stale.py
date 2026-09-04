from datetime import datetime, timedelta

from app.dashboard.filters import as_utc
from app.decisions.models import Decision, DecisionStatus


def stale_after_at(decision: Decision, threshold_days: int) -> datetime | None:
    """Return the exclusive stale threshold, or None for terminal decisions."""
    if threshold_days < 1:
        raise ValueError("threshold_days must be at least 1")
    if decision.status in {DecisionStatus.COMPLETED, DecisionStatus.CANCELLED}:
        return None
    return as_utc(decision.updated_at) + timedelta(days=threshold_days)


def is_stale(decision: Decision, threshold_days: int, now: datetime) -> bool:
    """A decision becomes stale strictly after its workspace threshold in UTC."""
    stale_after = stale_after_at(decision, threshold_days)
    return stale_after is not None and as_utc(now) > stale_after

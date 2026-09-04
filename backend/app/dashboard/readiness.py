import enum

from app.decisions.models import DecisionStatus


class DecisionReadiness(str, enum.Enum):
    CLOSED = "closed"
    BLOCKED_BY_OPEN_EXPERIMENTS = "blocked_by_open_experiments"
    DRAFT = "draft"
    NEEDS_REVISION = "needs_revision"
    READY_TO_CLOSE = "ready_to_close"


def get_decision_readiness(
    status: DecisionStatus, open_experiment_count: int
) -> DecisionReadiness:
    """Classify a decision independently of the calling user's role."""
    if open_experiment_count < 0:
        raise ValueError("open_experiment_count must not be negative")
    if status in {DecisionStatus.COMPLETED, DecisionStatus.CANCELLED}:
        return DecisionReadiness.CLOSED
    if open_experiment_count > 0:
        return DecisionReadiness.BLOCKED_BY_OPEN_EXPERIMENTS
    if status == DecisionStatus.DRAFT:
        return DecisionReadiness.DRAFT
    if status == DecisionStatus.NEEDS_REVISION:
        return DecisionReadiness.NEEDS_REVISION
    return DecisionReadiness.READY_TO_CLOSE

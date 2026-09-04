import uuid
from datetime import datetime, timezone

from app.dashboard.readiness import DecisionReadiness
from app.dashboard.schemas import (
    DashboardAuthorOut,
    DashboardDecisionOut,
    DashboardFiltersEcho,
    DashboardOut,
    DashboardPaginationOut,
    DashboardTotalsOut,
    DecisionStatusCounts,
    DecisionSummaryOut,
    ExperimentStatusCounts,
    OpenExperimentOut,
    SummaryExperimentsOut,
    VerdictCounts,
)
from app.decisions.models import DecisionStatus
from app.experiments.models import ExperimentStatus

NOW = datetime(2026, 9, 4, 12, 0, tzinfo=timezone.utc)
AUTHOR_ID = uuid.uuid4()
DECISION_ID = uuid.uuid4()


def _author():
    return DashboardAuthorOut(id=AUTHOR_ID, full_name="Ada")


def test_dashboard_out_keeps_zero_count_keys():
    body = DashboardOut(
        filters=DashboardFiltersEcho(
            date_from=None,
            date_to=None,
            status=None,
            author_id=None,
            stale_only=False,
        ),
        pagination=DashboardPaginationOut(limit=50, offset=0, total=0),
        totals=DashboardTotalsOut(
            decisions=0,
            by_status=DecisionStatusCounts(),
            stale=0,
            experiments_open=0,
            experiments_completed=0,
            verdicts=VerdictCounts(),
        ),
        decisions=[],
    )

    dumped = body.model_dump()
    assert set(dumped["totals"]["by_status"]) == {
        "draft",
        "active",
        "needs_revision",
        "completed",
        "cancelled",
    }
    assert set(dumped["totals"]["verdicts"]) == {"success", "partial", "failed"}
    assert dumped["pagination"]["limit"] == 50


def test_dashboard_decision_and_summary_roundtrip():
    card = DashboardDecisionOut(
        id=DECISION_ID,
        title="Pricing",
        status=DecisionStatus.ACTIVE,
        tags=["growth"],
        author=_author(),
        created_at=NOW,
        updated_at=NOW,
        is_stale=False,
        readiness=DecisionReadiness.READY_TO_CLOSE,
        experiment_counts=ExperimentStatusCounts(),
        verdict_counts=VerdictCounts(),
    )
    summary = DecisionSummaryOut(
        id=DECISION_ID,
        title="Pricing",
        description=None,
        status=DecisionStatus.ACTIVE,
        tags=["growth"],
        author=_author(),
        created_by=AUTHOR_ID,
        created_at=NOW,
        updated_at=NOW,
        is_stale=False,
        stale_threshold_days=30,
        stale_after_at=NOW,
        age_seconds=0,
        readiness=DecisionReadiness.BLOCKED_BY_OPEN_EXPERIMENTS,
        experiments=SummaryExperimentsOut(
            total=1,
            by_status=ExperimentStatusCounts(planned=1),
            verdicts=VerdictCounts(),
            open=[
                OpenExperimentOut(
                    id=uuid.uuid4(),
                    metric_name="conversion",
                    status=ExperimentStatus.PLANNED,
                    created_by=AUTHOR_ID,
                )
            ],
        ),
    )

    assert card.model_dump()["readiness"] == "ready_to_close"
    assert summary.experiments.open[0].status == ExperimentStatus.PLANNED
    assert summary.stale_after_at == NOW

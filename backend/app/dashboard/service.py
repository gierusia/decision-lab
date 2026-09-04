from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.models import User
from app.dashboard.filters import DashboardFilters, as_utc
from app.dashboard.readiness import get_decision_readiness
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
from app.dashboard.stale import is_stale, stale_after_at
from app.decisions.models import Decision, DecisionStatus
from app.experiments.models import Experiment, ExperimentStatus, ExperimentVerdict
from app.workspaces.models import Workspace

_TERMINAL = (DecisionStatus.COMPLETED, DecisionStatus.CANCELLED)
_OPEN_STATUSES = (ExperimentStatus.PLANNED, ExperimentStatus.RUNNING)


def _cutoff(now: datetime, threshold_days: int) -> datetime:
    return as_utc(now) - timedelta(days=threshold_days)


def _decision_clauses(workspace: Workspace, filters: DashboardFilters, now: datetime):
    clauses = [Decision.workspace_id == workspace.id]
    if filters.date_from is not None:
        clauses.append(Decision.updated_at >= filters.date_from)
    if filters.date_to is not None:
        clauses.append(Decision.updated_at <= filters.date_to)
    if filters.status is not None:
        clauses.append(Decision.status == filters.status)
    if filters.author_id is not None:
        clauses.append(Decision.created_by == filters.author_id)
    if filters.stale_only:
        clauses.append(Decision.status.notin_(_TERMINAL))
        clauses.append(Decision.updated_at < _cutoff(now, workspace.stale_threshold_days))
    return clauses


def _empty_status_counts() -> dict[str, int]:
    return {status.value: 0 for status in ExperimentStatus}


def _empty_verdict_counts() -> dict[str, int]:
    return {verdict.value: 0 for verdict in ExperimentVerdict}


def _empty_decision_status_counts() -> dict[str, int]:
    return {status.value: 0 for status in DecisionStatus}


def get_dashboard(
    db: Session,
    workspace: Workspace,
    filters: DashboardFilters,
    now: datetime | None = None,
) -> DashboardOut:
    now = as_utc(now or datetime.now(timezone.utc))
    clauses = _decision_clauses(workspace, filters, now)
    base = db.query(Decision).filter(*clauses)

    total = base.count()
    by_status_rows = (
        db.query(Decision.status, func.count(Decision.id))
        .filter(*clauses)
        .group_by(Decision.status)
        .all()
    )
    by_status = _empty_decision_status_counts()
    for status, count in by_status_rows:
        by_status[status.value] = count

    stale_total = (
        db.query(func.count(Decision.id))
        .filter(
            *clauses,
            Decision.status.notin_(_TERMINAL),
            Decision.updated_at < _cutoff(now, workspace.stale_threshold_days),
        )
        .scalar()
        or 0
    )

    filtered_ids = db.query(Decision.id).filter(*clauses)
    exp_status_rows = (
        db.query(Experiment.status, func.count(Experiment.id))
        .filter(Experiment.decision_id.in_(filtered_ids))
        .group_by(Experiment.status)
        .all()
    )
    exp_verdict_rows = (
        db.query(Experiment.verdict, func.count(Experiment.id))
        .filter(
            Experiment.decision_id.in_(filtered_ids),
            Experiment.verdict.isnot(None),
        )
        .group_by(Experiment.verdict)
        .all()
    )
    experiments_open = 0
    experiments_completed = 0
    for status, count in exp_status_rows:
        if status in _OPEN_STATUSES:
            experiments_open += count
        elif status == ExperimentStatus.COMPLETED:
            experiments_completed += count
    verdicts = _empty_verdict_counts()
    for verdict, count in exp_verdict_rows:
        if verdict is not None:
            verdicts[verdict.value] = count

    page = (
        base.order_by(Decision.updated_at.desc(), Decision.id.desc())
        .offset(filters.offset)
        .limit(filters.limit)
        .all()
    )
    page_ids = [decision.id for decision in page]
    authors = {}
    if page:
        author_ids = {decision.created_by for decision in page}
        for user in db.query(User).filter(User.id.in_(author_ids)).all():
            authors[user.id] = user

    per_status: dict = defaultdict(_empty_status_counts)
    per_verdict: dict = defaultdict(_empty_verdict_counts)
    if page_ids:
        breakdown = (
            db.query(
                Experiment.decision_id,
                Experiment.status,
                Experiment.verdict,
                func.count(Experiment.id),
            )
            .filter(Experiment.decision_id.in_(page_ids))
            .group_by(Experiment.decision_id, Experiment.status, Experiment.verdict)
            .all()
        )
        for decision_id, status, verdict, count in breakdown:
            per_status[decision_id][status.value] += count
            if verdict is not None:
                per_verdict[decision_id][verdict.value] += count

    cards = []
    for decision in page:
        status_counts = per_status[decision.id]
        open_count = status_counts["planned"] + status_counts["running"]
        author = authors.get(decision.created_by)
        cards.append(
            DashboardDecisionOut(
                id=decision.id,
                title=decision.title,
                status=decision.status,
                tags=[tag.tag for tag in decision.tags],
                author=DashboardAuthorOut(
                    id=decision.created_by,
                    full_name=author.full_name if author is not None else None,
                ),
                created_at=decision.created_at,
                updated_at=decision.updated_at,
                is_stale=is_stale(decision, workspace.stale_threshold_days, now),
                readiness=get_decision_readiness(decision.status, open_count),
                experiment_counts=ExperimentStatusCounts(**status_counts),
                verdict_counts=VerdictCounts(**per_verdict[decision.id]),
            )
        )

    return DashboardOut(
        filters=DashboardFiltersEcho(
            date_from=filters.date_from,
            date_to=filters.date_to,
            status=filters.status,
            author_id=filters.author_id,
            stale_only=filters.stale_only,
        ),
        pagination=DashboardPaginationOut(
            limit=filters.limit, offset=filters.offset, total=total
        ),
        totals=DashboardTotalsOut(
            decisions=total,
            by_status=DecisionStatusCounts(**by_status),
            stale=stale_total,
            experiments_open=experiments_open,
            experiments_completed=experiments_completed,
            verdicts=VerdictCounts(**verdicts),
        ),
        decisions=cards,
    )


def get_summary(
    db: Session,
    workspace: Workspace,
    decision: Decision,
    now: datetime | None = None,
) -> DecisionSummaryOut:
    now = as_utc(now or datetime.now(timezone.utc))
    experiments = (
        db.query(Experiment)
        .filter(Experiment.decision_id == decision.id)
        .order_by(Experiment.created_at.asc())
        .all()
    )
    by_status = _empty_status_counts()
    verdicts = _empty_verdict_counts()
    open_items: list[OpenExperimentOut] = []
    for experiment in experiments:
        by_status[experiment.status.value] += 1
        if experiment.verdict is not None:
            verdicts[experiment.verdict.value] += 1
        if experiment.status in _OPEN_STATUSES:
            open_items.append(
                OpenExperimentOut(
                    id=experiment.id,
                    metric_name=experiment.metric_name,
                    status=experiment.status,
                    created_by=experiment.created_by,
                )
            )

    author = db.query(User).filter(User.id == decision.created_by).first()
    updated_at = as_utc(decision.updated_at)
    age_seconds = max(0, int((now - updated_at).total_seconds()))
    open_count = by_status["planned"] + by_status["running"]

    return DecisionSummaryOut(
        id=decision.id,
        title=decision.title,
        description=decision.description,
        status=decision.status,
        tags=[tag.tag for tag in decision.tags],
        author=DashboardAuthorOut(
            id=decision.created_by,
            full_name=author.full_name if author is not None else None,
        ),
        created_by=decision.created_by,
        created_at=decision.created_at,
        updated_at=decision.updated_at,
        is_stale=is_stale(decision, workspace.stale_threshold_days, now),
        stale_threshold_days=workspace.stale_threshold_days,
        stale_after_at=stale_after_at(decision, workspace.stale_threshold_days),
        age_seconds=age_seconds,
        readiness=get_decision_readiness(decision.status, open_count),
        experiments=SummaryExperimentsOut(
            total=len(experiments),
            by_status=ExperimentStatusCounts(**by_status),
            verdicts=VerdictCounts(**verdicts),
            open=open_items,
        ),
    )

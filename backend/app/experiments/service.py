import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.auth.models import User
from app.decisions.models import Decision, DecisionStatus
from app.experiments.models import (
    Experiment,
    ExperimentStatus,
    ExperimentVerdict,
    MetricDirection,
)
from app.experiments.transitions import is_transition_allowed
from app.experiments.verdict import compute_verdict
from app.workspaces.models import Workspace, WorkspaceRole

_METRIC_FIELDS = (
    "metric_name",
    "metric_direction",
    "target_value",
    "actual_value",
    "partial_tolerance_percent",
    "feature_flag_key",
)


class ExperimentError(ValueError):
    """Ошибки доменных правил. Router мапит в HTTP 400."""


def _to_decimal(value: Decimal | int | float | None) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def list_open_experiments(db: Session, decision: Decision) -> list[Experiment]:
    return (
        db.query(Experiment)
        .filter(
            Experiment.decision_id == decision.id,
            Experiment.status.in_(
                [ExperimentStatus.PLANNED, ExperimentStatus.RUNNING]
            ),
        )
        .all()
    )


def create_experiment(
    db: Session,
    decision: Decision,
    creator: User,
    metric_name: str,
    metric_direction: MetricDirection,
    target_value: Decimal,
    partial_tolerance_percent: Decimal,
    actual_value: Decimal | None,
    notes: str | None,
    feature_flag_key: str | None,
) -> Experiment:
    if decision.status != DecisionStatus.ACTIVE:
        raise ExperimentError(
            "Experiments can only be created on a decision in 'active' status"
        )

    experiment = Experiment(
        decision_id=decision.id,
        created_by=creator.id,
        status=ExperimentStatus.PLANNED,
        verdict=None,
        metric_name=metric_name,
        metric_direction=metric_direction,
        target_value=_to_decimal(target_value),
        actual_value=_to_decimal(actual_value),
        partial_tolerance_percent=_to_decimal(partial_tolerance_percent),
        notes=notes,
        feature_flag_key=feature_flag_key,
        is_frozen=False,
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return experiment


def get_experiment(
    db: Session, decision: Decision, experiment_id: uuid.UUID
) -> Experiment | None:
    return (
        db.query(Experiment)
        .filter(Experiment.id == experiment_id, Experiment.decision_id == decision.id)
        .first()
    )


def list_experiments(db: Session, decision: Decision) -> list[Experiment]:
    return (
        db.query(Experiment)
        .filter(Experiment.decision_id == decision.id)
        .order_by(Experiment.created_at.desc())
        .all()
    )


def _decision_allows_mutation(decision: Decision, actor_role: WorkspaceRole) -> None:
    if decision.status == DecisionStatus.CANCELLED:
        raise ExperimentError("Cannot change experiments on a cancelled decision")
    if decision.status == DecisionStatus.ACTIVE:
        return
    if decision.status == DecisionStatus.COMPLETED and actor_role == WorkspaceRole.OWNER:
        return
    raise ExperimentError(
        f"Cannot change experiments while the decision is '{decision.status.value}'"
    )


def update_experiment(
    db: Session,
    experiment: Experiment,
    decision: Decision,
    actor: User,
    actor_role: WorkspaceRole,
    metric_name: str | None,
    metric_direction: MetricDirection | None,
    target_value: Decimal | None,
    actual_value: Decimal | None,
    partial_tolerance_percent: Decimal | None,
    notes: str | None,
    feature_flag_key: str | None,
    status: ExperimentStatus | None,
    is_frozen: bool | None,
    *,
    notes_provided: bool,
    feature_flag_provided: bool,
    actual_provided: bool,
) -> Experiment:
    if is_frozen is not None:
        if actor_role != WorkspaceRole.OWNER:
            raise ExperimentError("Only an owner can change experiment freeze")
        if decision.status == DecisionStatus.CANCELLED:
            raise ExperimentError("Cannot unfreeze experiments on a cancelled decision")
        if is_frozen is False and experiment.status != ExperimentStatus.COMPLETED:
            raise ExperimentError("Only a completed experiment can be unfrozen")
        experiment.is_frozen = is_frozen

    metric_patch = {
        "metric_name": metric_name,
        "metric_direction": metric_direction,
        "target_value": _to_decimal(target_value) if target_value is not None else None,
        "partial_tolerance_percent": (
            _to_decimal(partial_tolerance_percent)
            if partial_tolerance_percent is not None
            else None
        ),
        "feature_flag_key": feature_flag_key if feature_flag_provided else None,
    }
    touching_metrics = any(
        v is not None
        for k, v in metric_patch.items()
        if k != "feature_flag_key"
    ) or actual_provided or (feature_flag_provided and feature_flag_key is not None)

    # notes можно править всегда, кроме cancelled decision
    if notes_provided or touching_metrics or status is not None:
        _decision_allows_mutation(decision, actor_role)

    if touching_metrics or (status is not None and status != experiment.status):
        if experiment.is_frozen:
            raise ExperimentError("Experiment is frozen; an owner must unfreeze it first")

    if metric_name is not None:
        experiment.metric_name = metric_name
    if metric_direction is not None:
        experiment.metric_direction = metric_direction
    if target_value is not None:
        experiment.target_value = _to_decimal(target_value)
    if actual_provided:
        experiment.actual_value = _to_decimal(actual_value)
    if partial_tolerance_percent is not None:
        experiment.partial_tolerance_percent = _to_decimal(partial_tolerance_percent)
    if notes_provided:
        experiment.notes = notes
    if feature_flag_provided:
        experiment.feature_flag_key = feature_flag_key

    if status is not None and status != experiment.status:
        if decision.status != DecisionStatus.ACTIVE:
            raise ExperimentError(
                "Experiment status can only change while the decision is 'active'"
            )
        if not is_transition_allowed(experiment.status, status):
            raise ExperimentError(
                f"Cannot move experiment from '{experiment.status.value}' to '{status.value}'"
            )
        if status == ExperimentStatus.COMPLETED:
            if experiment.actual_value is None:
                raise ExperimentError("actual_value is required to complete an experiment")
            experiment.verdict = compute_verdict(
                experiment.metric_direction,
                experiment.target_value,
                experiment.actual_value,
                experiment.partial_tolerance_percent,
            )
            experiment.is_frozen = True
        experiment.status = status

    if (
        experiment.status == ExperimentStatus.COMPLETED
        and not experiment.is_frozen
        and (touching_metrics or actual_provided)
    ):
        if experiment.actual_value is None:
            raise ExperimentError("actual_value is required on a completed experiment")
        experiment.verdict = compute_verdict(
            experiment.metric_direction,
            experiment.target_value,
            experiment.actual_value,
            experiment.partial_tolerance_percent,
        )

    db.commit()
    db.refresh(experiment)
    return experiment


def delete_experiment(
    db: Session,
    experiment: Experiment,
    actor: User,
    actor_role: WorkspaceRole,
) -> None:
    if actor_role != WorkspaceRole.OWNER:
        raise ExperimentError("Only an owner can delete an experiment")
    db.delete(experiment)
    db.commit()

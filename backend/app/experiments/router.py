from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.models import User
from app.core.database import get_db
from app.core.deps import get_current_user
from app.decisions.deps import get_decision_or_404
from app.decisions.models import Decision
from app.experiments import service
from app.experiments.deps import get_experiment_or_404
from app.experiments.models import Experiment
from app.experiments.schemas import (
    ExperimentCreateRequest,
    ExperimentOut,
    ExperimentUpdateRequest,
)
from app.workspaces import service as workspace_service
from app.workspaces.deps import require_role
from app.workspaces.models import Workspace, WorkspaceRole

router = APIRouter()


def _actor_role(db: Session, workspace: Workspace, user: User) -> WorkspaceRole:
    membership = workspace_service.get_membership(db, workspace, user)
    # require_role already guaranteed membership exists
    return membership.role


def _to_out(experiment: Experiment) -> ExperimentOut:
    return ExperimentOut(
        id=experiment.id,
        decision_id=experiment.decision_id,
        created_by=experiment.created_by,
        status=experiment.status,
        verdict=experiment.verdict,
        metric_name=experiment.metric_name,
        metric_direction=experiment.metric_direction,
        target_value=experiment.target_value,
        actual_value=experiment.actual_value,
        partial_tolerance_percent=experiment.partial_tolerance_percent,
        notes=experiment.notes,
        feature_flag_key=experiment.feature_flag_key,
        is_frozen=experiment.is_frozen,
        created_at=experiment.created_at,
        updated_at=experiment.updated_at,
    )


@router.post(
    "/{workspace_id}/decisions/{decision_id}/experiments",
    response_model=ExperimentOut,
    status_code=201,
)
def create_experiment(
    payload: ExperimentCreateRequest,
    decision: Decision = Depends(get_decision_or_404),
    workspace: Workspace = Depends(require_role(WorkspaceRole.MEMBER)),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        experiment = service.create_experiment(
            db,
            decision,
            current_user,
            payload.metric_name,
            payload.metric_direction,
            payload.target_value,
            payload.partial_tolerance_percent,
            payload.actual_value,
            payload.notes,
            payload.feature_flag_key,
        )
    except service.ExperimentError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return _to_out(experiment)


@router.get(
    "/{workspace_id}/decisions/{decision_id}/experiments",
    response_model=list[ExperimentOut],
)
def list_experiments(
    decision: Decision = Depends(get_decision_or_404),
    workspace: Workspace = Depends(require_role(WorkspaceRole.VIEWER)),
    db: Session = Depends(get_db),
):
    return [_to_out(item) for item in service.list_experiments(db, decision)]


@router.get(
    "/{workspace_id}/decisions/{decision_id}/experiments/{experiment_id}",
    response_model=ExperimentOut,
)
def get_experiment(experiment: Experiment = Depends(get_experiment_or_404)):
    return _to_out(experiment)


@router.patch(
    "/{workspace_id}/decisions/{decision_id}/experiments/{experiment_id}",
    response_model=ExperimentOut,
)
def update_experiment(
    payload: ExperimentUpdateRequest,
    experiment: Experiment = Depends(get_experiment_or_404),
    decision: Decision = Depends(get_decision_or_404),
    workspace: Workspace = Depends(require_role(WorkspaceRole.MEMBER)),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    fields_set = payload.model_fields_set
    try:
        updated = service.update_experiment(
            db,
            experiment,
            decision,
            current_user,
            _actor_role(db, workspace, current_user),
            payload.metric_name,
            payload.metric_direction,
            payload.target_value,
            payload.actual_value,
            payload.partial_tolerance_percent,
            payload.notes,
            payload.feature_flag_key,
            payload.status,
            payload.is_frozen,
            notes_provided="notes" in fields_set,
            feature_flag_provided="feature_flag_key" in fields_set,
            actual_provided="actual_value" in fields_set,
        )
    except service.ExperimentError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return _to_out(updated)


@router.delete(
    "/{workspace_id}/decisions/{decision_id}/experiments/{experiment_id}",
    status_code=204,
)
def delete_experiment(
    experiment: Experiment = Depends(get_experiment_or_404),
    workspace: Workspace = Depends(require_role(WorkspaceRole.MEMBER)),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        service.delete_experiment(
            db, experiment, current_user, _actor_role(db, workspace, current_user)
        )
    except service.ExperimentError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.models import User
from app.core.database import get_db
from app.core.deps import get_current_user
from app.decisions import service
from app.decisions.deps import get_decision_or_404
from app.decisions.models import Decision
from app.decisions.schemas import DecisionCreateRequest, DecisionOut, DecisionUpdateRequest
from app.workspaces.deps import require_role
from app.workspaces.models import Workspace, WorkspaceRole

router = APIRouter()


@router.post("/{workspace_id}/decisions", response_model=DecisionOut, status_code=201)
def create_decision(
    payload: DecisionCreateRequest,
    workspace: Workspace = Depends(require_role(WorkspaceRole.MEMBER)),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.create_decision(
        db, workspace, current_user, payload.title, payload.description
    )


@router.get("/{workspace_id}/decisions", response_model=list[DecisionOut])
def list_decisions(
    workspace: Workspace = Depends(require_role(WorkspaceRole.VIEWER)),
    db: Session = Depends(get_db),
):
    return service.list_decisions(db, workspace)


@router.get("/{workspace_id}/decisions/{decision_id}", response_model=DecisionOut)
def get_decision(decision: Decision = Depends(get_decision_or_404)):
    return decision


@router.patch("/{workspace_id}/decisions/{decision_id}", response_model=DecisionOut)
def update_decision(
    payload: DecisionUpdateRequest,
    decision: Decision = Depends(get_decision_or_404),
    workspace: Workspace = Depends(require_role(WorkspaceRole.MEMBER)),
    db: Session = Depends(get_db),
):
    return service.update_decision(
        db, decision, payload.title, payload.description, payload.status
    )


@router.delete("/{workspace_id}/decisions/{decision_id}", status_code=204)
def delete_decision(
    decision: Decision = Depends(get_decision_or_404),
    workspace: Workspace = Depends(require_role(WorkspaceRole.MEMBER)),
    db: Session = Depends(get_db),
):
    service.delete_decision(db, decision)

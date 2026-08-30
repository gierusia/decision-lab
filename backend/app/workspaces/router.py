from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.models import User
from app.core.database import get_db
from app.core.deps import get_current_user
from app.workspaces import service
from app.workspaces.deps import require_membership, require_owner
from app.workspaces.models import Workspace
from app.workspaces.schemas import WorkspaceCreateRequest, WorkspaceOut, WorkspaceUpdateRequest

router = APIRouter()


@router.post("", response_model=WorkspaceOut, status_code=201)
def create_workspace(
    payload: WorkspaceCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.create_workspace(
        db, current_user, payload.name, payload.stale_threshold_days
    )


@router.get("", response_model=list[WorkspaceOut])
def list_my_workspaces(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.list_workspaces_for_user(db, current_user)


@router.get("/{workspace_id}", response_model=WorkspaceOut)
def get_workspace(workspace: Workspace = Depends(require_membership)):
    return workspace


@router.patch("/{workspace_id}", response_model=WorkspaceOut)
def update_workspace(
    payload: WorkspaceUpdateRequest,
    workspace: Workspace = Depends(require_owner),
    db: Session = Depends(get_db),
):
    return service.update_workspace_settings(
        db, workspace, payload.name, payload.stale_threshold_days
    )

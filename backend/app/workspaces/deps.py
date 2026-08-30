import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.models import User
from app.core.database import get_db
from app.core.deps import get_current_user
from app.workspaces import service
from app.workspaces.models import Workspace
from app.workspaces.permissions import is_owner


def get_workspace_or_404(workspace_id: uuid.UUID, db: Session = Depends(get_db)) -> Workspace:
    workspace = service.get_workspace(db, workspace_id)
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return workspace


def require_membership(
    workspace: Workspace = Depends(get_workspace_or_404),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Workspace:

    if service.get_membership(db, workspace, current_user) is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this workspace",
        )
    return workspace


def require_owner(
    workspace: Workspace = Depends(get_workspace_or_404),
    current_user: User = Depends(get_current_user),
) -> Workspace:
    # Пока единственная проверка прав в проекте — есть только Owner.
    # Member/Viewer добавятся сюда же, когда появится приглашение участников.
    if not is_owner(workspace, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the workspace owner can do this",
        )
    return workspace

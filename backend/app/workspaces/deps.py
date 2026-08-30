import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.models import User
from app.core.database import get_db
from app.core.deps import get_current_user
from app.workspaces import service
from app.workspaces.models import Workspace, WorkspaceRole
from app.workspaces.permissions import has_role


def get_workspace_or_404(workspace_id: uuid.UUID, db: Session = Depends(get_db)) -> Workspace:
    workspace = service.get_workspace(db, workspace_id)
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return workspace


def require_role(min_role: WorkspaceRole):
    """Фабрика зависимостей: Depends(require_role(WorkspaceRole.MEMBER))
    пропускает Member и Owner, режет Viewer."""

    def dependency(
        workspace: Workspace = Depends(get_workspace_or_404),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Workspace:
        membership = service.get_membership(db, workspace, current_user)

        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this workspace",
            )

        if not has_role(membership.role, min_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires the '{min_role.value}' role or higher",
            )

        return workspace

    return dependency


require_membership = require_role(WorkspaceRole.VIEWER)
require_owner = require_role(WorkspaceRole.OWNER)

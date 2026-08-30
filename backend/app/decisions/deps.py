import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.decisions import service
from app.decisions.models import Decision
from app.workspaces.deps import require_role
from app.workspaces.models import Workspace, WorkspaceRole


def get_decision_or_404(
    decision_id: uuid.UUID,
    workspace: Workspace = Depends(require_role(WorkspaceRole.VIEWER)),
    db: Session = Depends(get_db),
) -> Decision:
    decision = service.get_decision(db, workspace, decision_id)
    if decision is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision not found")
    return decision

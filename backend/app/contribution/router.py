from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.contribution import service
from app.contribution.schemas import ContributionRow
from app.core.database import get_db
from app.workspaces.deps import require_role
from app.workspaces.models import Workspace, WorkspaceRole

router = APIRouter()


@router.get("/{workspace_id}/contribution", response_model=list[ContributionRow])
def list_contribution(
    workspace: Workspace = Depends(require_role(WorkspaceRole.VIEWER)),
    db: Session = Depends(get_db),
):
    return service.list_contribution(db, workspace)

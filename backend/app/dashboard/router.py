import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dashboard.filters import DashboardFilters
from app.dashboard.schemas import DashboardOut, DecisionSummaryOut
from app.dashboard import service
from app.decisions.deps import get_decision_or_404
from app.decisions.models import Decision, DecisionStatus
from app.workspaces.deps import require_role
from app.workspaces.models import Workspace, WorkspaceRole

router = APIRouter()


@router.get("/{workspace_id}/dashboard", response_model=DashboardOut)
def get_dashboard(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    status: DecisionStatus | None = None,
    author_id: uuid.UUID | None = None,
    stale_only: bool = False,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    workspace: Workspace = Depends(require_role(WorkspaceRole.VIEWER)),
    db: Session = Depends(get_db),
):
    try:
        filters = DashboardFilters(
            date_from=date_from,
            date_to=date_to,
            status=status,
            author_id=author_id,
            stale_only=stale_only,
            limit=limit,
            offset=offset,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return service.get_dashboard(db, workspace, filters, now=datetime.now(timezone.utc))


@router.get(
    "/{workspace_id}/decisions/{decision_id}/summary",
    response_model=DecisionSummaryOut,
)
def get_decision_summary(
    decision: Decision = Depends(get_decision_or_404),
    workspace: Workspace = Depends(require_role(WorkspaceRole.VIEWER)),
    db: Session = Depends(get_db),
):
    return service.get_summary(db, workspace, decision, now=datetime.now(timezone.utc))

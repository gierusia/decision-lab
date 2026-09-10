from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.activity import service
from app.activity.models import ActivityLog
from app.activity.schemas import ActivityLogOut
from app.core.database import get_db
from app.workspaces.deps import require_role
from app.workspaces.models import Workspace, WorkspaceRole

router = APIRouter()


def _to_out(entry: ActivityLog) -> ActivityLogOut:
    return ActivityLogOut(
        id=entry.id,
        action=entry.action,
        entity_type=entry.entity_type,
        entity_id=entry.entity_id,
        summary=entry.summary,
        actor_id=entry.actor_id,
        actor_email=entry.actor.email,
        actor_full_name=entry.actor.full_name,
        created_at=entry.created_at,
    )


@router.get("/{workspace_id}/activity", response_model=list[ActivityLogOut])
def list_activity(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    # Лента — read-only обзор происходящего в команде, поэтому доступ
    # такой же, как у GET /decisions: любой участник, включая Viewer.
    workspace: Workspace = Depends(require_role(WorkspaceRole.VIEWER)),
    db: Session = Depends(get_db),
):
    entries = service.list_activity(db, workspace.id, limit=limit, offset=offset)
    return [_to_out(e) for e in entries]

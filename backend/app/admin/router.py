from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.presenters import to_user_out
from app.core.admins import is_platform_admin
from app.core.database import get_db
from app.core.deps import get_current_user
from app.workspaces import service as workspace_service
from app.workspaces.models import Workspace, WorkspaceRole
from app.workspaces.schemas import WorkspaceOut

router = APIRouter()


class MembershipAssignRequest(BaseModel):
    workspace_id: str
    role: WorkspaceRole


class UserMembershipOut(BaseModel):
    workspace_id: str
    workspace_name: str
    role: WorkspaceRole


class AdminUserOut(BaseModel):
    user: object
    memberships: list[UserMembershipOut]


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not is_platform_admin(current_user.email):
        raise HTTPException(status_code=403, detail="Admin only")
    return current_user


@router.get("/users")
def list_users(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.asc()).all()
    rows = workspace_service.list_all_memberships(db)
    by_user: dict = {}
    for membership, workspace in rows:
        if workspace.owner_id != admin.id:
            continue
        by_user.setdefault(membership.user_id, []).append(
            {
                "workspace_id": str(membership.workspace_id),
                "workspace_name": workspace.name,
                "role": membership.role.value if hasattr(membership.role, "value") else membership.role,
            }
        )
    return [
        {
            "user": to_user_out(user),
            "memberships": by_user.get(user.id, []),
        }
        for user in users
    ]


@router.get("/workspaces", response_model=list[WorkspaceOut])
def list_all_workspaces(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return (
        db.query(Workspace)
        .filter(Workspace.owner_id == admin.id)
        .order_by(Workspace.created_at.asc())
        .all()
    )


@router.put("/users/{user_id}/memberships")
def assign_membership(
    user_id: str,
    payload: MembershipAssignRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if payload.role not in {WorkspaceRole.VIEWER, WorkspaceRole.MEMBER}:
        raise HTTPException(status_code=400, detail="Only viewer or member can be assigned")
    try:
        membership = workspace_service.assign_membership(
            db, user_id, payload.workspace_id, payload.role, actor=admin
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {
        "workspace_id": str(membership.workspace_id),
        "role": membership.role.value if hasattr(membership.role, "value") else membership.role,
    }

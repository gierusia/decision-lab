import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.workspaces import service
from app.workspaces.deps import get_workspace_or_404, require_membership, require_owner
from app.workspaces.models import Workspace, WorkspaceMember
from app.workspaces.schemas import MemberAddRequest, MemberOut, MemberRoleUpdateRequest

router = APIRouter()


def _to_member_out(membership: WorkspaceMember) -> MemberOut:

    return MemberOut(
        id=membership.id,
        user_id=membership.user_id,
        email=membership.user.email,
        full_name=membership.user.full_name,
        role=membership.role,
        created_at=membership.created_at,
    )


def get_member_or_404(
    member_id: uuid.UUID,
    workspace: Workspace = Depends(get_workspace_or_404),
    db: Session = Depends(get_db),
) -> WorkspaceMember:
    membership = service.get_membership_by_id(db, workspace, member_id)
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    return membership


@router.post("/{workspace_id}/members", response_model=MemberOut, status_code=201)
def add_member(
    payload: MemberAddRequest,
    workspace: Workspace = Depends(require_owner),
    db: Session = Depends(get_db),
):
    try:
        membership = service.add_member(db, workspace, payload.email, payload.role)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return _to_member_out(membership)


@router.get("/{workspace_id}/members", response_model=list[MemberOut])
def list_members(
    workspace: Workspace = Depends(require_membership),
    db: Session = Depends(get_db),
):
    return [_to_member_out(m) for m in service.list_members(db, workspace)]


@router.patch("/{workspace_id}/members/{member_id}", response_model=MemberOut)
def update_member_role(
    payload: MemberRoleUpdateRequest,
    membership: WorkspaceMember = Depends(get_member_or_404),
    workspace: Workspace = Depends(require_owner),
    db: Session = Depends(get_db),
):
    try:
        updated = service.update_member_role(db, membership, payload.role)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return _to_member_out(updated)


@router.delete("/{workspace_id}/members/{member_id}", status_code=204)
def remove_member(
    membership: WorkspaceMember = Depends(get_member_or_404),
    workspace: Workspace = Depends(require_owner),
    db: Session = Depends(get_db),
):
    try:
        service.remove_member(db, membership)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

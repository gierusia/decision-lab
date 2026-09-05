import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import service as auth_service
from app.auth.models import User
from app.workspaces.models import Workspace, WorkspaceMember, WorkspaceRole


def create_workspace(db: Session, owner: User, name: str, stale_threshold_days: int) -> Workspace:
    workspace = Workspace(
        name=name,
        owner_id=owner.id,
        stale_threshold_days=stale_threshold_days,
    )
    db.add(workspace)
    db.flush()  

    membership = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=owner.id,
        role=WorkspaceRole.OWNER,
    )
    db.add(membership)

    db.commit()
    db.refresh(workspace)
    return workspace


def get_workspace(db: Session, workspace_id: uuid.UUID) -> Workspace | None:
    return db.query(Workspace).filter(Workspace.id == workspace_id).first()


def get_membership(db: Session, workspace: Workspace, user: User) -> WorkspaceMember | None:
    """Единственное место, которое умеет отвечать на вопрос "есть ли у
    этого юзера какая-то роль в этом workspace"."""
    return (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace.id,
            WorkspaceMember.user_id == user.id,
        )
        .first()
    )


def get_membership_by_id(
    db: Session, workspace: Workspace, member_id: uuid.UUID
) -> WorkspaceMember | None:
    return (
        db.query(WorkspaceMember)
        .filter(WorkspaceMember.id == member_id, WorkspaceMember.workspace_id == workspace.id)
        .first()
    )


def list_workspaces_for_user(db: Session, user: User) -> list[Workspace]:
    return (
        db.query(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .filter(WorkspaceMember.user_id == user.id)
        .all()
    )


def list_members(db: Session, workspace: Workspace) -> list[WorkspaceMember]:
    return (
        db.query(WorkspaceMember)
        .filter(WorkspaceMember.workspace_id == workspace.id)
        .all()
    )


def add_member(
    db: Session, workspace: Workspace, email: str, role: WorkspaceRole
) -> WorkspaceMember:
    user = auth_service.get_user_by_email(db, email)
    if user is None:
        raise ValueError("No user with this email is registered yet")

    if get_membership(db, workspace, user) is not None:
        raise ValueError("This user is already a member of the workspace")

    membership = WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=role)
    db.add(membership)
    try:
        db.commit()
    except IntegrityError:
        # Та же гонка, что чинили в auth.create_user: два одновременных
        # приглашения одного и того же email могут оба пройти проверку
        # get_membership выше раньше, чем долетит commit.
        db.rollback()
        raise ValueError("This user is already a member of the workspace") from None

    db.refresh(membership)
    return membership


def update_member_role(
    db: Session, membership: WorkspaceMember, new_role: WorkspaceRole
) -> WorkspaceMember:
    if membership.role == WorkspaceRole.OWNER:
        raise ValueError("Cannot change the owner's role")
    membership.role = new_role
    db.commit()
    db.refresh(membership)
    return membership


def remove_member(db: Session, membership: WorkspaceMember) -> None:
    if membership.role == WorkspaceRole.OWNER:
        raise ValueError("Cannot remove the workspace owner")
    db.delete(membership)
    db.commit()


def update_workspace_settings(
    db: Session,
    workspace: Workspace,
    name: str | None,
    stale_threshold_days: int | None,
) -> Workspace:
    if name is not None:
        workspace.name = name
    if stale_threshold_days is not None:
        workspace.stale_threshold_days = stale_threshold_days

    db.commit()
    db.refresh(workspace)
    return workspace


def list_all_memberships(db: Session) -> list[tuple[WorkspaceMember, Workspace]]:
    return (
        db.query(WorkspaceMember, Workspace)
        .join(Workspace, Workspace.id == WorkspaceMember.workspace_id)
        .all()
    )


def assign_membership(
    db: Session,
    user_id: str,
    workspace_id: str,
    role: WorkspaceRole,
    *,
    actor: User,
) -> WorkspaceMember:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise ValueError("User not found")
    workspace = get_workspace(db, workspace_id)
    if workspace is None:
        raise ValueError("Workspace not found")
    if workspace.owner_id != actor.id:
        raise ValueError("You can only assign people to your own workspaces")
    if role not in {WorkspaceRole.VIEWER, WorkspaceRole.MEMBER}:
        raise ValueError("Only viewer or member can be assigned")

    membership = get_membership(db, workspace, user)
    if membership is None:
        membership = WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=role)
        db.add(membership)
    else:
        if membership.role == WorkspaceRole.OWNER:
            raise ValueError("Cannot change the owner's role")
        membership.role = role
    db.commit()
    db.refresh(membership)
    return membership


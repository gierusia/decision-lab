import uuid

from sqlalchemy.orm import Session

from app.auth.models import User
from app.workspaces.models import Workspace, WorkspaceMember, WorkspaceRole


def create_workspace(db: Session, owner: User, name: str, stale_threshold_days: int) -> Workspace:
    workspace = Workspace(
        name=name,
        owner_id=owner.id,
        stale_threshold_days=stale_threshold_days,
    )
    db.add(workspace)
    db.flush()  # нужен id workspace до создания записи о членстве ниже

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
    этого юзера какая-то роль в этом workspace". """
    return (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace.id,
            WorkspaceMember.user_id == user.id,
        )
        .first()
    )


def list_workspaces_for_user(db: Session, user: User) -> list[Workspace]:
    return (
        db.query(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .filter(WorkspaceMember.user_id == user.id)
        .all()
    )


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

import uuid

from sqlalchemy.orm import Session

from app.auth.models import User
from app.decisions.models import Decision, DecisionStatus
from app.workspaces.models import Workspace


def create_decision(
    db: Session, workspace: Workspace, creator: User, title: str, description: str | None
) -> Decision:
    decision = Decision(
        workspace_id=workspace.id,
        title=title,
        description=description,
        status=DecisionStatus.DRAFT,
        created_by=creator.id,
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision


def get_decision(db: Session, workspace: Workspace, decision_id: uuid.UUID) -> Decision | None:
    # Фильтр по workspace_id — не только по id — важен: без него можно было
    # бы дёрнуть decision_id из чужого workspace, если случайно подобрать
    # верный uuid, зная только его. Так 404 гарантированно означает "нет
    # такого решения именно в ЭТОМ workspace".
    return (
        db.query(Decision)
        .filter(Decision.id == decision_id, Decision.workspace_id == workspace.id)
        .first()
    )


def list_decisions(db: Session, workspace: Workspace) -> list[Decision]:
    return (
        db.query(Decision)
        .filter(Decision.workspace_id == workspace.id)
        .order_by(Decision.created_at.desc())
        .all()
    )


def update_decision(
    db: Session,
    decision: Decision,
    title: str | None,
    description: str | None,
    status: DecisionStatus | None,
) -> Decision:
    if title is not None:
        decision.title = title
    if description is not None:
        decision.description = description
    if status is not None:
        decision.status = status

    db.commit()
    db.refresh(decision)
    return decision


def delete_decision(db: Session, decision: Decision) -> None:
    db.delete(decision)
    db.commit()

import uuid

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth.models import User
from app.decisions.models import Decision, DecisionStatus, DecisionTag
from app.decisions.transitions import is_transition_allowed
from app.workspaces.models import Workspace


def create_decision(
    db: Session,
    workspace: Workspace,
    creator: User,
    title: str,
    description: str | None,
    tags: list[str],
) -> Decision:
    decision = Decision(
        workspace_id=workspace.id,
        title=title,
        description=description,
        status=DecisionStatus.DRAFT,
        created_by=creator.id,
        tags=[DecisionTag(tag=t) for t in tags],
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision


def get_decision(db: Session, workspace: Workspace, decision_id: uuid.UUID) -> Decision | None:
    return (
        db.query(Decision)
        .filter(Decision.id == decision_id, Decision.workspace_id == workspace.id)
        .first()
    )


def list_decisions(
    db: Session,
    workspace: Workspace,
    q: str | None = None,
    tag: str | None = None,
    status: DecisionStatus | None = None,
) -> list[Decision]:
    query = db.query(Decision).filter(Decision.workspace_id == workspace.id)

    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(Decision.title.ilike(pattern), Decision.description.ilike(pattern))
        )

    if tag:
        query = query.join(DecisionTag).filter(DecisionTag.tag == tag)

    if status is not None:
        query = query.filter(Decision.status == status)

    return query.order_by(Decision.created_at.desc()).all()


def update_decision(
    db: Session,
    decision: Decision,
    title: str | None,
    description: str | None,
    status: DecisionStatus | None,
    tags: list[str] | None,
    *,
    actor_is_owner: bool = False,
) -> Decision:
    if title is not None:
        decision.title = title
    if description is not None:
        decision.description = description

    if status is not None:
        if not is_transition_allowed(decision.status, status):
            raise ValueError(
                f"Cannot move decision from '{decision.status.value}' to '{status.value}'"
            )
        if status in {DecisionStatus.COMPLETED, DecisionStatus.CANCELLED} and not actor_is_owner:
            from app.experiments.service import list_open_experiments

            if list_open_experiments(db, decision):
                raise ValueError(
                    "Cannot close a decision while experiments are still planned or running"
                )
        decision.status = status

    if tags is not None:
        decision.tags = [DecisionTag(tag=t) for t in tags]

    db.commit()
    db.refresh(decision)
    return decision


def delete_decision(db: Session, decision: Decision) -> None:
    db.delete(decision)
    db.commit()

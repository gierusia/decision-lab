import uuid

from sqlalchemy.orm import Session

from app.activity.models import ActivityAction, ActivityEntityType, ActivityLog
from app.auth.models import User


def record_activity(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    actor: User,
    action: ActivityAction,
    entity_type: ActivityEntityType,
    entity_id: uuid.UUID,
    summary: str,
) -> None:
    """Только db.add() — эта функция намеренно не коммитит сама.

    Запись лога всегда едет в той же транзакции, что и операция, которую
    она описывает (create_decision, update_decision и т.д. коммитят сами
    в конце своей функции). Если основная операция по какой-то причине
    откатится, запись в логе не должна остаться сиротой без события."""
    db.add(
        ActivityLog(
            workspace_id=workspace_id,
            actor_id=actor.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            summary=summary,
        )
    )


def list_activity(
    db: Session, workspace_id: uuid.UUID, *, limit: int = 50, offset: int = 0
) -> list[ActivityLog]:
    return (
        db.query(ActivityLog)
        .filter(ActivityLog.workspace_id == workspace_id)
        .order_by(ActivityLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

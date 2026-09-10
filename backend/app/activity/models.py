import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.auth.models import User
from app.core.database import Base
from app.core.types import GUID, pg_enum


class ActivityAction(str, enum.Enum):
    DECISION_CREATED = "decision.created"
    DECISION_STATUS_CHANGED = "decision.status_changed"
    EXPERIMENT_CREATED = "experiment.created"
    EXPERIMENT_STATUS_CHANGED = "experiment.status_changed"
    MEMBER_ADDED = "member.added"
    MEMBER_REMOVED = "member.removed"


class ActivityEntityType(str, enum.Enum):
    DECISION = "decision"
    EXPERIMENT = "experiment"
    MEMBER = "member"


class ActivityLog(Base):
    __tablename__ = "activity_log"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("workspaces.id"), nullable=False
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)

    action: Mapped[ActivityAction] = mapped_column(
        pg_enum(ActivityAction, name="activityaction"), nullable=False
    )

    # Без FK: entity_id указывает на decision.id / experiment.id / user.id
    # в зависимости от entity_type — одна колонка под разные таблицы
    # принципиально не проверяется через FK. Это и развязывает лог от
    # судьбы самой сущности: запись "решение X создано" должна остаться
    # в истории, даже если решение потом удалили.
    entity_type: Mapped[ActivityEntityType] = mapped_column(
        pg_enum(ActivityEntityType, name="activityentitytype"), nullable=False
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)

    # Готовая строка, а не шаблон + сырые данные для рендера на фронте —
    # лог фиксирует факт на момент события. Если решение потом переименуют,
    # старая запись лога не должна "переиграться" под новое название.
    summary: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    actor: Mapped["User"] = relationship("User", lazy="selectin")

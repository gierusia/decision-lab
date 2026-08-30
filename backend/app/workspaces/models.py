import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.types import GUID


class WorkspaceRole(str, enum.Enum):
    """Member/Viewer пока нигде не выдаются — появятся, когда добавим
    приглашение участников. Заводим все три значения сразу, чтобы потом
    не переделывать колонку и не гонять лишнюю миграцию."""

    OWNER = "owner"
    MEMBER = "member"
    VIEWER = "viewer"


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)

    # Владелец хранится и здесь напрямую (для простых проверок "кто owner"
    # без лишнего JOIN), и продублирован строкой в WorkspaceMember ниже —
    # это осознанное дублирование ради простоты на первом шаге Этапа 2.
    owner_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)

    stale_threshold_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class WorkspaceMember(Base):
    """Таблица существует с этого шага, но пока в ней ровно одна строка
    на workspace — сам Owner. Add-member эндпоинт и проверки роли Member/
    Viewer — следующий кусочек Этапа 2."""

    __tablename__ = "workspace_members"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("workspaces.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    role: Mapped[WorkspaceRole] = mapped_column(SAEnum(WorkspaceRole), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        # Один пользователь — не больше одной роли в одном workspace.
        # Сейчас это не проверяется нигде в коде (добавлять некому, кроме
        # Owner при создании), но пусть база подстрахует с первого дня.
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),
    )

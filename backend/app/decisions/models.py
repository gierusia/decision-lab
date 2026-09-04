import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.types import GUID


class DecisionStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    NEEDS_REVISION = "needs_revision"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("workspaces.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[DecisionStatus] = mapped_column(
        SAEnum(DecisionStatus), nullable=False, default=DecisionStatus.DRAFT
    )

    created_by: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    tags: Mapped[list["DecisionTag"]] = relationship(
        "DecisionTag", cascade="all, delete-orphan", lazy="selectin"
    )
    experiments: Mapped[list["Experiment"]] = relationship(
        "Experiment",
        back_populates="decision",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class DecisionTag(Base):
    __tablename__ = "decision_tags"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    decision_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("decisions.id"), nullable=False
    )
    tag: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (UniqueConstraint("decision_id", "tag", name="uq_decision_tag"),)

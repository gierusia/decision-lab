import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.types import GUID, pg_enum


class ExperimentStatus(str, enum.Enum):
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"


class ExperimentVerdict(str, enum.Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class MetricDirection(str, enum.Enum):
    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    decision_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("decisions.id"), nullable=False
    )
    created_by: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)

    status: Mapped[ExperimentStatus] = mapped_column(
        pg_enum(ExperimentStatus, name="experimentstatus"), nullable=False, default=ExperimentStatus.PLANNED
    )
    verdict: Mapped[ExperimentVerdict | None] = mapped_column(
        pg_enum(ExperimentVerdict, name="experimentverdict"), nullable=True, default=None
    )

    metric_name: Mapped[str] = mapped_column(String, nullable=False)
    metric_direction: Mapped[MetricDirection] = mapped_column(
        pg_enum(MetricDirection, name="metricdirection"), nullable=False
    )
    target_value: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    actual_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    partial_tolerance_percent: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    feature_flag_key: Mapped[str | None] = mapped_column(String, nullable=True)

    is_frozen: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    decision: Mapped["Decision"] = relationship("Decision", back_populates="experiments")

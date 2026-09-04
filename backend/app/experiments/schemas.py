import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.experiments.models import ExperimentStatus, ExperimentVerdict, MetricDirection


class ExperimentCreateRequest(BaseModel):
    metric_name: str = Field(min_length=1, max_length=200)
    metric_direction: MetricDirection
    target_value: Decimal
    partial_tolerance_percent: Decimal
    actual_value: Decimal | None = None
    notes: str | None = None
    feature_flag_key: str | None = Field(default=None, max_length=200)

    @field_validator("partial_tolerance_percent")
    @classmethod
    def _tolerance_range(cls, value: Decimal) -> Decimal:
        if value < 0 or value > 100:
            raise ValueError("partial_tolerance_percent must be between 0 and 100")
        return value

    @field_validator("feature_flag_key")
    @classmethod
    def _clean_flag(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ExperimentUpdateRequest(BaseModel):
    """None = не трогать поле. is_frozen меняет только Owner — это
    проверяет service, не схема."""

    metric_name: str | None = Field(default=None, min_length=1, max_length=200)
    metric_direction: MetricDirection | None = None
    target_value: Decimal | None = None
    actual_value: Decimal | None = None
    partial_tolerance_percent: Decimal | None = None
    notes: str | None = None
    feature_flag_key: str | None = Field(default=None, max_length=200)
    status: ExperimentStatus | None = None
    is_frozen: bool | None = None

    @field_validator("partial_tolerance_percent")
    @classmethod
    def _tolerance_range(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        if value < 0 or value > 100:
            raise ValueError("partial_tolerance_percent must be between 0 and 100")
        return value

    @field_validator("feature_flag_key")
    @classmethod
    def _clean_flag(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ExperimentOut(BaseModel):
    id: uuid.UUID
    decision_id: uuid.UUID
    created_by: uuid.UUID
    status: ExperimentStatus
    verdict: ExperimentVerdict | None
    metric_name: str
    metric_direction: MetricDirection
    target_value: Decimal
    actual_value: Decimal | None
    partial_tolerance_percent: Decimal
    notes: str | None
    feature_flag_key: str | None
    is_frozen: bool
    created_at: datetime
    updated_at: datetime

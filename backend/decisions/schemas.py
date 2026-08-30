import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.decisions.models import DecisionStatus


class DecisionCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str | None = None


class DecisionUpdateRequest(BaseModel):
    """Все поля опциональны — можно менять что-то одно. status здесь можно
    выставить в любое значение enum'а; проверка допустимости перехода
    (например, что completed нельзя вернуть в draft) — следующий шаг."""

    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = None
    status: DecisionStatus | None = None


class DecisionOut(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    title: str
    description: str | None
    status: DecisionStatus
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class WorkspaceCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    stale_threshold_days: int = Field(default=30, ge=1)


class WorkspaceUpdateRequest(BaseModel):
    """Оба поля опциональны — можно поменять что-то одно. Пока этот
    эндпоинт доступен только Owner'у (см. workspaces/deps.py)."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    stale_threshold_days: int | None = Field(default=None, ge=1)


class WorkspaceOut(BaseModel):
    id: uuid.UUID
    name: str
    owner_id: uuid.UUID
    stale_threshold_days: int
    created_at: datetime

    class Config:
        from_attributes = True

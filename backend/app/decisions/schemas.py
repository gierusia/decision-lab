import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.decisions.models import DecisionStatus


def _clean_tags(value: list[str]) -> list[str]:
    seen: list[str] = []
    for tag in value:
        cleaned = tag.strip()
        if cleaned and cleaned not in seen:
            seen.append(cleaned)
    return seen


class DecisionCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str | None = None
    tags: list[str] = Field(default_factory=list)

    @field_validator("tags")
    @classmethod
    def _validate_tags(cls, value: list[str]) -> list[str]:
        return _clean_tags(value)


class DecisionUpdateRequest(BaseModel):
    """tags: None значит "не трогать теги", [] значит "стереть все теги" 
    два разных случая, поэтому нельзя просто проверять на falsy."""

    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = None
    status: DecisionStatus | None = None
    tags: list[str] | None = None

    @field_validator("tags")
    @classmethod
    def _validate_tags(cls, value: list[str] | None) -> list[str] | None:
        return value if value is None else _clean_tags(value)


class DecisionOut(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    title: str
    description: str | None
    status: DecisionStatus
    tags: list[str]
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

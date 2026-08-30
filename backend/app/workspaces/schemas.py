import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.workspaces.models import WorkspaceRole


class WorkspaceCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    stale_threshold_days: int = Field(default=30, ge=1)


class WorkspaceUpdateRequest(BaseModel):
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


def _reject_owner_role(value: WorkspaceRole) -> WorkspaceRole:
    if value == WorkspaceRole.OWNER:
        raise ValueError("Owner role can't be assigned through this endpoint")
    return value


class MemberAddRequest(BaseModel):
    email: EmailStr
    role: WorkspaceRole = WorkspaceRole.MEMBER

    @field_validator("role")
    @classmethod
    def _validate_role(cls, value: WorkspaceRole) -> WorkspaceRole:
        return _reject_owner_role(value)


class MemberRoleUpdateRequest(BaseModel):
    role: WorkspaceRole

    @field_validator("role")
    @classmethod
    def _validate_role(cls, value: WorkspaceRole) -> WorkspaceRole:
        return _reject_owner_role(value)


class MemberOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    email: EmailStr
    full_name: str | None
    role: WorkspaceRole
    created_at: datetime

    class Config:
        from_attributes = True

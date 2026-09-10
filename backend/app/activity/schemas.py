import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.activity.models import ActivityAction, ActivityEntityType


class ActivityLogOut(BaseModel):
    id: uuid.UUID
    action: ActivityAction
    entity_type: ActivityEntityType
    entity_id: uuid.UUID
    summary: str
    actor_id: uuid.UUID
    actor_email: EmailStr
    actor_full_name: str | None
    created_at: datetime

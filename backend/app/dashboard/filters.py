import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from app.decisions.models import DecisionStatus


def as_utc(value: datetime) -> datetime:
    """Return an aware UTC datetime; naïve inputs are interpreted as UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class DashboardFilters:
    """Normalised query values shared by the future dashboard reader."""

    date_from: datetime | None = None
    date_to: datetime | None = None
    status: DecisionStatus | None = None
    author_id: uuid.UUID | None = None
    stale_only: bool = False
    limit: int = 50
    offset: int = 0

    def __post_init__(self) -> None:
        if self.date_from is not None:
            object.__setattr__(self, "date_from", as_utc(self.date_from))
        if self.date_to is not None:
            object.__setattr__(self, "date_to", as_utc(self.date_to))
        if self.date_from is not None and self.date_to is not None:
            if self.date_from > self.date_to:
                raise ValueError("date_from must not be after date_to")
        if not 1 <= self.limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        if self.offset < 0:
            raise ValueError("offset must be at least 0")

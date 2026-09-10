from pydantic import BaseModel

from app.workspaces.models import WorkspaceRole


class ContributionVerdicts(BaseModel):
    success: int = 0
    partial: int = 0
    failed: int = 0


class ContributionRow(BaseModel):
    user_id: str
    email: str
    full_name: str | None
    role: WorkspaceRole
    decisions_created: int
    experiments_created: int
    verdicts: ContributionVerdicts
    status_changes: int
    experiments_completed: int

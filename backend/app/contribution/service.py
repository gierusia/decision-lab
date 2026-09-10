from collections import defaultdict
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.activity.models import ActivityAction, ActivityLog
from app.decisions.models import Decision
from app.experiments.models import Experiment, ExperimentVerdict
from app.workspaces.models import Workspace, WorkspaceMember


def _empty_verdicts() -> dict[str, int]:
    return {"success": 0, "partial": 0, "failed": 0}


def list_contribution(db: Session, workspace: Workspace) -> list[dict]:
    members = (
        db.query(WorkspaceMember)
        .filter(WorkspaceMember.workspace_id == workspace.id)
        .all()
    )

    decision_counts = dict(
        db.query(Decision.created_by, func.count(Decision.id))
        .filter(Decision.workspace_id == workspace.id)
        .group_by(Decision.created_by)
        .all()
    )

    experiment_counts = dict(
        db.query(Experiment.created_by, func.count(Experiment.id))
        .join(Decision, Decision.id == Experiment.decision_id)
        .filter(Decision.workspace_id == workspace.id)
        .group_by(Experiment.created_by)
        .all()
    )

    verdict_rows = (
        db.query(Experiment.created_by, Experiment.verdict, func.count(Experiment.id))
        .join(Decision, Decision.id == Experiment.decision_id)
        .filter(Decision.workspace_id == workspace.id, Experiment.verdict.isnot(None))
        .group_by(Experiment.created_by, Experiment.verdict)
        .all()
    )
    verdicts: dict[UUID, dict[str, int]] = defaultdict(_empty_verdicts)
    for user_id, verdict, count in verdict_rows:
        if verdict is None:
            continue
        key = verdict.value if hasattr(verdict, "value") else str(verdict)
        verdicts[user_id][key] = count

    status_rows = (
        db.query(ActivityLog.actor_id, func.count(ActivityLog.id))
        .filter(
            ActivityLog.workspace_id == workspace.id,
            ActivityLog.action.in_(
                [
                    ActivityAction.DECISION_STATUS_CHANGED,
                    ActivityAction.EXPERIMENT_STATUS_CHANGED,
                ]
            ),
        )
        .group_by(ActivityLog.actor_id)
        .all()
    )
    status_changes = dict(status_rows)

    completed_rows = (
        db.query(ActivityLog.actor_id, func.count(ActivityLog.id))
        .filter(
            ActivityLog.workspace_id == workspace.id,
            ActivityLog.action == ActivityAction.EXPERIMENT_STATUS_CHANGED,
            ActivityLog.summary.like("%→ completed%"),
        )
        .group_by(ActivityLog.actor_id)
        .all()
    )
    completed = dict(completed_rows)

    rows = []
    for membership in members:
        user = membership.user
        user_id = membership.user_id
        rows.append(
            {
                "user_id": str(user_id),
                "email": user.email,
                "full_name": user.full_name,
                "role": membership.role,
                "decisions_created": int(decision_counts.get(user_id, 0)),
                "experiments_created": int(experiment_counts.get(user_id, 0)),
                "verdicts": verdicts.get(user_id, _empty_verdicts()),
                "status_changes": int(status_changes.get(user_id, 0)),
                "experiments_completed": int(completed.get(user_id, 0)),
            }
        )
    return rows

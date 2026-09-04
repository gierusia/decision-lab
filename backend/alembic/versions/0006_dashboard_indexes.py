"""indexes for dashboard filters and experiment rollups

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-04
"""

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_decisions_workspace_updated_at",
        "decisions",
        ["workspace_id", "updated_at"],
    )
    op.create_index(
        "ix_decisions_workspace_status",
        "decisions",
        ["workspace_id", "status"],
    )
    op.create_index(
        "ix_decisions_workspace_created_by",
        "decisions",
        ["workspace_id", "created_by"],
    )
    op.create_index(
        "ix_experiments_decision_status",
        "experiments",
        ["decision_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_experiments_decision_status", table_name="experiments")
    op.drop_index("ix_decisions_workspace_created_by", table_name="decisions")
    op.drop_index("ix_decisions_workspace_status", table_name="decisions")
    op.drop_index("ix_decisions_workspace_updated_at", table_name="decisions")

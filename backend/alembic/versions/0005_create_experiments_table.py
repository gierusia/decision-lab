"""create experiments table

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-04
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

experiment_status = postgresql.ENUM(
    "planned", "running", "completed",
    name="experimentstatus", create_type=False,
)
experiment_verdict = postgresql.ENUM(
    "success", "partial", "failed",
    name="experimentverdict", create_type=False,
)
metric_direction = postgresql.ENUM(
    "higher_is_better", "lower_is_better",
    name="metricdirection", create_type=False,
)


def upgrade() -> None:
    experiment_status.create(op.get_bind(), checkfirst=True)
    experiment_verdict.create(op.get_bind(), checkfirst=True)
    metric_direction.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "experiments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "decision_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("decisions.id"),
            nullable=False,
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("status", experiment_status, nullable=False, server_default="planned"),
        sa.Column("verdict", experiment_verdict, nullable=True),
        sa.Column("metric_name", sa.String(), nullable=False),
        sa.Column("metric_direction", metric_direction, nullable=False),
        sa.Column("target_value", sa.Numeric(18, 6), nullable=False),
        sa.Column("actual_value", sa.Numeric(18, 6), nullable=True),
        sa.Column("partial_tolerance_percent", sa.Numeric(6, 3), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("feature_flag_key", sa.String(), nullable=True),
        sa.Column("is_frozen", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_experiments_decision_id", "experiments", ["decision_id"])


def downgrade() -> None:
    op.drop_index("ix_experiments_decision_id", table_name="experiments")
    op.drop_table("experiments")
    metric_direction.drop(op.get_bind(), checkfirst=True)
    experiment_verdict.drop(op.get_bind(), checkfirst=True)
    experiment_status.drop(op.get_bind(), checkfirst=True)

"""create activity_log table

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-10
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

activity_action = postgresql.ENUM(
    "decision.created",
    "decision.status_changed",
    "experiment.created",
    "experiment.status_changed",
    "member.added",
    "member.removed",
    name="activityaction",
    create_type=False,
)
activity_entity_type = postgresql.ENUM(
    "decision", "experiment", "member",
    name="activityentitytype", create_type=False,
)


def upgrade() -> None:
    activity_action.create(op.get_bind(), checkfirst=True)
    activity_entity_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "activity_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id"),
            nullable=False,
        ),
        sa.Column(
            "actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("action", activity_action, nullable=False),
        sa.Column("entity_type", activity_entity_type, nullable=False),
        # entity_id намеренно без ForeignKey — см. комментарий в models.py:
        # указывает на разные таблицы в зависимости от entity_type.
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    # Основной паттерн чтения — "последние N событий этого workspace",
    # индекс покрывает его напрямую вместо full scan + sort.
    op.create_index(
        "ix_activity_log_workspace_created_at",
        "activity_log",
        ["workspace_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_activity_log_workspace_created_at", table_name="activity_log")
    op.drop_table("activity_log")
    activity_entity_type.drop(op.get_bind(), checkfirst=True)
    activity_action.drop(op.get_bind(), checkfirst=True)

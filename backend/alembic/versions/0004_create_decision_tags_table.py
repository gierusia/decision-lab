"""create decision_tags table

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-30
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "decision_tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "decision_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("decisions.id"),
            nullable=False,
        ),
        sa.Column("tag", sa.String(), nullable=False),
        sa.UniqueConstraint("decision_id", "tag", name="uq_decision_tag"),
    )
    # Ускоряет фильтр ?tag=... — без индекса это был бы full scan таблицы
    # decision_tags при любом поиске по тегу.
    op.create_index("ix_decision_tags_tag", "decision_tags", ["tag"])


def downgrade() -> None:
    op.drop_index("ix_decision_tags_tag", table_name="decision_tags")
    op.drop_table("decision_tags")

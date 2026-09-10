"""add sample_size and baseline_rate to experiments

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-10
"""

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("experiments", sa.Column("sample_size", sa.Integer(), nullable=True))
    op.add_column("experiments", sa.Column("baseline_rate", sa.Numeric(18, 6), nullable=True))


def downgrade() -> None:
    op.drop_column("experiments", "baseline_rate")
    op.drop_column("experiments", "sample_size")

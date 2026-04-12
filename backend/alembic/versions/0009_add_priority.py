"""add priority column to tasks

Revision ID: 0009_add_priority
Revises: 0008_perf_indexes
Create Date: 2026-04-12
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0009_add_priority"
down_revision = "0008_perf_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the enum type first
    op.execute("CREATE TYPE task_priority AS ENUM ('low', 'medium', 'high')")
    # Add the column with a default of 'medium'
    op.add_column(
        "tasks",
        sa.Column(
            "priority",
            sa.Enum("low", "medium", "high", name="task_priority", create_type=False),
            nullable=False,
            server_default="medium",
        ),
    )


def downgrade() -> None:
    op.drop_column("tasks", "priority")
    op.execute("DROP TYPE IF EXISTS task_priority")

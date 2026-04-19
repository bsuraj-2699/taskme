"""add overdue status, last_activity_at, task_submissions

Revision ID: 0006_submissions_followup
Revises: 0005_task_comments
Create Date: 2026-04-10
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0006_submissions_followup"
down_revision = "0005_task_comments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add 'overdue' value to task_status enum.
    # `ALTER TYPE ... ADD VALUE` cannot run inside a multi-statement transaction
    # on some PostgreSQL configurations. We use an autocommit block so this
    # statement runs on its own connection, avoiding that failure mode.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE task_status ADD VALUE IF NOT EXISTS 'overdue'")

    # 2. Add last_activity_at column to tasks (default to now()).
    op.add_column(
        "tasks",
        sa.Column(
            "last_activity_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    # Backfill existing rows: set last_activity_at = updated_at.
    op.execute("UPDATE tasks SET last_activity_at = updated_at")

    # 3. Create task_submissions table.
    op.create_table(
        "task_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "uploaded_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(1024), nullable=False),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("task_submissions")
    op.drop_column("tasks", "last_activity_at")
    # Note: cannot remove enum value in PostgreSQL without recreating the type.

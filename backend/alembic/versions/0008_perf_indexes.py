"""performance indexes and file size column

Revision ID: 0008_perf_indexes
Revises: 0007_report_overdue
Create Date: 2026-04-11
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0008_perf_indexes"
down_revision = "0007_report_overdue"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Index on tasks.status — critical for follow-up job & filtered queries
    op.create_index("ix_tasks_status", "tasks", ["status"])

    # 2. Index on tasks.deadline — used in sorting and overdue checks
    op.create_index("ix_tasks_deadline", "tasks", ["deadline"])

    # 3. Composite index for follow-up stale check (status + last_activity_at)
    op.create_index("ix_tasks_status_activity", "tasks", ["status", "last_activity_at"])

    # 4. Index on notifications.is_read for poll queries
    op.create_index("ix_notifications_is_read", "notifications", ["user_id", "is_read"])

    # 5. Add file_size column to task_attachments for enforcing limits
    op.add_column(
        "task_attachments",
        sa.Column("file_size", sa.BigInteger(), nullable=True, server_default="0"),
    )

    # 6. Add file_size column to task_submissions
    op.add_column(
        "task_submissions",
        sa.Column("file_size", sa.BigInteger(), nullable=True, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("task_submissions", "file_size")
    op.drop_column("task_attachments", "file_size")
    op.drop_index("ix_notifications_is_read", table_name="notifications")
    op.drop_index("ix_tasks_status_activity", table_name="tasks")
    op.drop_index("ix_tasks_deadline", table_name="tasks")
    op.drop_index("ix_tasks_status", table_name="tasks")

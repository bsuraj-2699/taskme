"""monthly reports + schedule, drop unused notified column

Revision ID: 0010_monthly_reports
Revises: 0009_add_priority
Create Date: 2026-04-16
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0010_monthly_reports"
down_revision = "0009_add_priority"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Drop the unused `notified` column from tasks. Nothing reads or writes it.
    op.drop_column("tasks", "notified")

    # 2. Monthly schedule fields on existing singleton report_schedules row.
    op.add_column(
        "report_schedules",
        sa.Column(
            "monthly_is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "report_schedules",
        sa.Column(
            "monthly_day",
            sa.Integer(),
            nullable=False,
            server_default="1",  # first of month by default
        ),
    )
    op.add_column(
        "report_schedules",
        sa.Column(
            "monthly_report_time",
            sa.String(length=5),
            nullable=False,
            server_default="09:00",
        ),
    )

    # 3. New table for monthly reports (separate from daily EOD reports).
    op.create_table(
        "monthly_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        # Month identifier: we store the first day of the reporting month.
        sa.Column("month_start", sa.Date(), nullable=False),
        sa.Column("total_tasks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pending", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("in_progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("done", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("overdue", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
    )
    op.create_index("ix_monthly_reports_month_start", "monthly_reports", ["month_start"])


def downgrade() -> None:
    op.drop_index("ix_monthly_reports_month_start", table_name="monthly_reports")
    op.drop_table("monthly_reports")
    op.drop_column("report_schedules", "monthly_report_time")
    op.drop_column("report_schedules", "monthly_day")
    op.drop_column("report_schedules", "monthly_is_active")
    # Re-add notified column on downgrade for symmetry.
    op.add_column(
        "tasks",
        sa.Column(
            "notified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

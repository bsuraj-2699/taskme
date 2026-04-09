"""eod reports and schedule

Revision ID: 0004_eod_reports
Revises: 0003_task_attachments
Create Date: 2026-04-09
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0004_eod_reports"
down_revision = "0003_task_attachments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "eod_reports",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("total_tasks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pending", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("in_progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("done", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
    )
    op.create_table(
        "report_schedules",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("report_time", sa.String(length=5), nullable=False, server_default="18:00"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("timezone", sa.String(length=50), nullable=False, server_default="Asia/Kolkata"),
    )


def downgrade() -> None:
    op.drop_table("report_schedules")
    op.drop_table("eod_reports")


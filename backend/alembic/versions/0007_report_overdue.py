"""add overdue column to eod_reports

Revision ID: 0007_report_overdue
Revises: 0006_submissions_followup
Create Date: 2026-04-10
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007_report_overdue"
down_revision = "0006_submissions_followup"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "eod_reports",
        sa.Column("overdue", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("eod_reports", "overdue")

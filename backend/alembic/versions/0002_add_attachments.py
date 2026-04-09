"""add attachments to tasks

Revision ID: 0002_add_attachments
Revises: 0001_init
Create Date: 2026-04-08
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_add_attachments"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("attachment_path", sa.String(), nullable=True))
    op.add_column("tasks", sa.Column("attachment_name", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("tasks", "attachment_name")
    op.drop_column("tasks", "attachment_path")


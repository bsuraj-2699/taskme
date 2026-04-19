from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class MonthlyReport(Base):
    """Aggregated monthly report. One row per generated monthly report."""

    __tablename__ = "monthly_reports"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    # First day of the reporting month (e.g. 2026-04-01).
    month_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    total_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pending: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    in_progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    done: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    overdue: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")

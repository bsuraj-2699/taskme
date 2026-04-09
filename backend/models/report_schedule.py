from __future__ import annotations

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class ReportSchedule(Base):
    __tablename__ = "report_schedules"

    # Singleton row (we always keep exactly one row with id=1)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    report_time: Mapped[str] = mapped_column(String(5), nullable=False, default="18:00")  # HH:MM
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="Asia/Kolkata")


from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ── Daily (EOD) report schemas ──────────────────────────────────────────────


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    generated_at: datetime
    report_date: date
    total_tasks: int
    pending: int
    in_progress: int
    done: int
    overdue: int = 0
    content: str


class ReportListItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    generated_at: datetime
    report_date: date
    total_tasks: int
    pending: int
    in_progress: int
    done: int
    overdue: int = 0


class PaginatedReports(BaseModel):
    """Paginated response for daily report list."""

    items: list[ReportListItemOut]
    total: int
    page: int
    page_size: int
    total_pages: int


# ── Monthly report schemas ──────────────────────────────────────────────────


class MonthlyReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    generated_at: datetime
    month_start: date
    total_tasks: int
    pending: int
    in_progress: int
    done: int
    overdue: int = 0
    content: str


class MonthlyReportListItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    generated_at: datetime
    month_start: date
    total_tasks: int
    pending: int
    in_progress: int
    done: int
    overdue: int = 0


class PaginatedMonthlyReports(BaseModel):
    """Paginated response for monthly report list."""

    items: list[MonthlyReportListItemOut]
    total: int
    page: int
    page_size: int
    total_pages: int


# ── Schedule schemas ────────────────────────────────────────────────────────


class ScheduleOut(BaseModel):
    """Schedule output — includes both daily (EOD) and monthly fields."""

    model_config = ConfigDict(from_attributes=True)

    # Daily.
    report_time: str
    timezone: str
    is_active: bool
    # Monthly.
    monthly_is_active: bool = True
    monthly_day: int = 1
    monthly_report_time: str = "09:00"


class ScheduleUpdate(BaseModel):
    """Schedule update — daily fields required (for back-compat), monthly optional."""

    report_time: str = Field(default="18:00", min_length=5, max_length=5)
    timezone: str = Field(default="Asia/Kolkata", min_length=1, max_length=50)
    is_active: bool = True

    # Monthly — optional so existing frontend payloads keep working.
    monthly_is_active: bool | None = None
    monthly_day: int | None = Field(default=None, ge=1, le=28)
    monthly_report_time: str | None = Field(default=None, min_length=5, max_length=5)

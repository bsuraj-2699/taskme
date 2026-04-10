from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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


class ScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    report_time: str
    timezone: str
    is_active: bool


class ScheduleUpdate(BaseModel):
    report_time: str = Field(default="18:00", min_length=5, max_length=5)
    timezone: str = Field(default="Asia/Kolkata", min_length=1, max_length=50)
    is_active: bool = True


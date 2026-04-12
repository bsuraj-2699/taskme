from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    file_name: str
    file_size: int = 0
    uploaded_at: datetime


class SubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    file_name: str
    note: str = ""
    file_size: int = 0
    uploaded_at: datetime
    uploaded_by: UUID
    uploader_name: str = ""


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    assigned_to: UUID
    assigned_by: UUID
    status: str
    priority: str = "medium"
    progress: int
    deadline: date
    created_at: datetime
    updated_at: datetime
    # Legacy single-attachment field (kept for backwards compat)
    attachment_name: str | None = None
    # New multi-attachment list
    attachments: list[AttachmentOut] = []
    # Comment count for list views (populated from ORM property)
    comment_count: int = 0
    # Employee submissions
    submission_count: int = 0


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    assigned_to: UUID
    deadline: date
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    assigned_to: UUID | None = None
    deadline: date | None = None
    status: str | None = None
    progress: int | None = Field(default=None, ge=0, le=100)
    priority: str | None = Field(default=None, pattern="^(low|medium|high)$")


class ProgressUpdate(BaseModel):
    progress: int = Field(ge=0, le=100)


class ReassignTask(BaseModel):
    assigned_to: UUID


# ── Pagination wrapper ─────────────────────────────────────────────────────

class PaginatedTasks(BaseModel):
    """Paginated response for task list endpoints."""
    items: list[TaskOut]
    total: int
    page: int
    page_size: int
    total_pages: int

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    file_name: str
    uploaded_at: datetime


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    assigned_to: UUID
    assigned_by: UUID
    status: str
    progress: int
    deadline: date
    created_at: datetime
    updated_at: datetime
    # Legacy single-attachment field (kept for backwards compat)
    attachment_name: str | None = None
    # New multi-attachment list
    attachments: list[AttachmentOut] = []


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    assigned_to: UUID
    deadline: date


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    assigned_to: UUID | None = None
    deadline: date | None = None
    status: str | None = None
    progress: int | None = Field(default=None, ge=0, le=100)


class ProgressUpdate(BaseModel):
    progress: int = Field(ge=0, le=100)


class ReassignTask(BaseModel):
    assigned_to: UUID
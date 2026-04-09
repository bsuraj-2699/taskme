from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    username: str
    role: str
    created_at: datetime
    is_active: bool


class UserCreate(BaseModel):
    name: str
    username: str
    password: str
    role: str = "employee"


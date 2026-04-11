from __future__ import annotations

import enum
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class UserRole(str, enum.Enum):
    ceo = "ceo"
    employee = "employee"


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Changed from selectin → lazy="raise" to prevent accidental N+1 loads.
    # Any code that needs these must use explicit joins/queries instead.
    tasks_assigned_to = relationship(
        "Task",
        foreign_keys="Task.assigned_to",
        back_populates="assignee",
        lazy="noload",
    )
    tasks_assigned_by = relationship(
        "Task",
        foreign_keys="Task.assigned_by",
        back_populates="assigner",
        lazy="noload",
    )

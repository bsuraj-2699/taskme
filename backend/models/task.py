from __future__ import annotations

import enum
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class TaskStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    done = "done"
    overdue = "overdue"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")

    assigned_to: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    assigned_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus, name="task_status"), nullable=False, default=TaskStatus.pending)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deadline: Mapped[date] = mapped_column(Date, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    notified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    attachment_path: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    attachment_name: Mapped[str | None] = mapped_column(String, nullable=True, default=None)

    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    assignee = relationship("User", foreign_keys=[assigned_to], back_populates="tasks_assigned_to", lazy="selectin")
    assigner = relationship("User", foreign_keys=[assigned_by], back_populates="tasks_assigned_by", lazy="selectin")
    notifications = relationship("Notification", back_populates="task", cascade="all, delete-orphan", lazy="selectin")
    attachments = relationship("TaskAttachment", back_populates="task", cascade="all, delete-orphan", lazy="selectin")
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan", lazy="selectin", order_by="TaskComment.created_at.asc()")
    submissions = relationship("TaskSubmission", back_populates="task", cascade="all, delete-orphan", lazy="selectin", order_by="TaskSubmission.uploaded_at.desc()")

    @property
    def comment_count(self) -> int:
        return len(self.comments) if self.comments else 0

    @property
    def submission_count(self) -> int:
        return len(self.submissions) if self.submissions else 0
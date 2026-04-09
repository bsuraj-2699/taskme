from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import CurrentUser, get_current_user
from core.errors import http_error
from models.comment import TaskComment
from models.notification import Notification
from models.task import Task
from models.user import User
from schemas.comment import CommentCreate, CommentOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["comments"])


def _get_task_or_404(db: Session, task_id: UUID) -> Task:
    task = db.scalar(select(Task).where(Task.id == task_id))
    if not task:
        raise http_error(404, "Task not found", 404)
    return task


def _ensure_task_access(task: Task, user: CurrentUser) -> None:
    if user.role == "ceo":
        return
    if task.assigned_to != user.id:
        raise http_error(403, "Forbidden", 403)


@router.get("/{task_id}/comments", response_model=list[CommentOut])
def list_comments(
    task_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Get all comments for a task. Both CEO and assigned employee can view."""
    try:
        task = _get_task_or_404(db, task_id)
        _ensure_task_access(task, user)

        comments = list(
            db.scalars(
                select(TaskComment)
                .where(TaskComment.task_id == task_id)
                .order_by(TaskComment.created_at.asc())
            ).all()
        )

        # Build user name lookup
        user_ids = {c.user_id for c in comments}
        users = {
            u.id: u.name
            for u in db.scalars(select(User).where(User.id.in_(user_ids))).all()
        } if user_ids else {}

        return [
            CommentOut(
                id=c.id,
                task_id=c.task_id,
                user_id=c.user_id,
                author_name=users.get(c.user_id, "Unknown"),
                body=c.body,
                created_at=c.created_at,
            )
            for c in comments
        ]
    except Exception as e:
        if hasattr(e, "status_code"):
            raise
        logger.exception("list comments failed")
        raise http_error(500, "Failed to list comments", 500)


@router.post("/{task_id}/comments", response_model=CommentOut)
def add_comment(
    task_id: UUID,
    payload: CommentCreate,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Add a comment to a task. Both CEO and assigned employee can comment."""
    try:
        task = _get_task_or_404(db, task_id)
        _ensure_task_access(task, user)

        comment = TaskComment(
            task_id=task.id,
            user_id=user.id,
            body=payload.body,
        )
        db.add(comment)

        # Notify the other party
        author = db.scalar(select(User).where(User.id == user.id))
        author_name = author.name if author else "Someone"

        if user.role == "ceo":
            # Notify the assigned employee
            notif = Notification(
                user_id=task.assigned_to,
                task_id=task.id,
                message=f"{author_name} commented on \"{task.title}\": {payload.body[:80]}",
                is_read=False,
            )
            db.add(notif)
        else:
            # Notify the CEO (assigner)
            notif = Notification(
                user_id=task.assigned_by,
                task_id=task.id,
                message=f"{author_name} commented on \"{task.title}\": {payload.body[:80]}",
                is_read=False,
            )
            db.add(notif)

        db.commit()
        db.refresh(comment)

        return CommentOut(
            id=comment.id,
            task_id=comment.task_id,
            user_id=comment.user_id,
            author_name=author_name,
            body=comment.body,
            created_at=comment.created_at,
        )
    except Exception as e:
        db.rollback()
        if hasattr(e, "status_code"):
            raise
        logger.exception("add comment failed")
        raise http_error(500, "Failed to add comment", 500)

from __future__ import annotations

import logging
import math
import mimetypes
import os
import shutil
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.deps import CurrentUser, get_current_user, require_role
from core.errors import http_error
from models.attachment import TaskAttachment
from models.notification import Notification
from models.task import Task, TaskPriority, TaskStatus
from models.user import User, UserRole
from schemas.task import (
    PaginatedTasks,
    ProgressUpdate,
    ReassignTask,
    TaskCreate,
    TaskOut,
    TaskUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

UPLOADS_DIR = Path(os.getenv("UPLOADS_DIR", "/app/uploads"))

MAX_FILE_SIZE = settings.max_file_size_bytes
MAX_FILES_PER_UPLOAD = settings.max_files_per_upload


def _ensure_employee_exists(db: Session, user_id: UUID) -> User:
    user = db.scalar(select(User).where(User.id == user_id))
    if not user or not user.is_active:
        raise http_error(404, "User not found", 404)
    if user.role != UserRole.employee:
        raise http_error(422, "assigned_to must be an employee", 422)
    return user


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


async def _validate_file_size(file: UploadFile) -> bytes:
    """Read file data and validate against size limit. Returns bytes."""
    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise http_error(
            413,
            f"File '{file.filename}' exceeds the {settings.max_file_size_mb}MB limit.",
            413,
        )
    return data


def _cleanup_task_files(task_id: UUID) -> None:
    """Remove upload directory for a task from disk."""
    task_dir = UPLOADS_DIR / str(task_id)
    if task_dir.exists() and task_dir.is_dir():
        shutil.rmtree(task_dir, ignore_errors=True)
    # Also clean submission files
    sub_dir = UPLOADS_DIR / "submissions" / str(task_id)
    if sub_dir.exists() and sub_dir.is_dir():
        shutil.rmtree(sub_dir, ignore_errors=True)


# ── Static routes MUST come before /{task_id} ──────────────────────────────

@router.get("/my", response_model=PaginatedTasks)
def my_tasks(
    user: CurrentUser = Depends(require_role("employee")),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size),
    status: str | None = Query(None),
    priority: str | None = Query(None),
) -> Any:
    try:
        from datetime import date as date_type
        from sqlalchemy import case

        q = select(Task).where(Task.assigned_to == user.id)
        count_q = select(func.count()).select_from(Task).where(Task.assigned_to == user.id)

        if status and status != "all":
            if status == "overdue":
                today = date_type.today()
                q = q.where(Task.deadline < today, Task.status != TaskStatus.done)
                count_q = count_q.where(Task.deadline < today, Task.status != TaskStatus.done)
            else:
                q = q.where(Task.status == TaskStatus(status))
                count_q = count_q.where(Task.status == TaskStatus(status))

        if priority and priority != "all":
            if priority in ("low", "medium", "high"):
                q = q.where(Task.priority == TaskPriority(priority))
                count_q = count_q.where(Task.priority == TaskPriority(priority))

        total = db.scalar(count_q) or 0
        total_pages = max(1, math.ceil(total / page_size))

        # Sort: pending/in_progress/overdue first (by created_at desc = newest on top),
        # then done tasks sink to the bottom.
        status_order = case(
            (Task.status == TaskStatus.done, 1),
            else_=0,
        )

        tasks = list(
            db.scalars(
                q.order_by(status_order.asc(), Task.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return PaginatedTasks(
            items=tasks,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception:
        logger.exception("my tasks failed")
        raise http_error(500, "Failed to fetch tasks", 500)


# ── Collection routes ───────────────────────────────────────────────────────

@router.get("/", response_model=PaginatedTasks)
def list_tasks(
    _: CurrentUser = Depends(require_role("ceo")),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size),
    status: str | None = Query(None),
    assigned_to: str | None = Query(None),
) -> Any:
    try:
        from datetime import date as date_type
        from uuid import UUID as UUID_type

        q = select(Task)
        count_q = select(func.count()).select_from(Task)

        # Employee filter
        if assigned_to and assigned_to != "all":
            try:
                uid = UUID_type(assigned_to)
                q = q.where(Task.assigned_to == uid)
                count_q = count_q.where(Task.assigned_to == uid)
            except (ValueError, TypeError):
                pass

        # Status filter — "overdue" is a virtual filter based on deadline
        if status and status != "all":
            if status == "overdue":
                today = date_type.today()
                q = q.where(Task.deadline < today, Task.status != TaskStatus.done)
                count_q = count_q.where(Task.deadline < today, Task.status != TaskStatus.done)
            else:
                q = q.where(Task.status == TaskStatus(status))
                count_q = count_q.where(Task.status == TaskStatus(status))

        total = db.scalar(count_q) or 0
        total_pages = max(1, math.ceil(total / page_size))

        tasks = list(
            db.scalars(
                q.order_by(Task.deadline.asc(), Task.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return PaginatedTasks(
            items=tasks,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception:
        logger.exception("list tasks failed")
        raise http_error(500, "Failed to fetch tasks", 500)


@router.post("/", response_model=TaskOut)
def create_task(
    payload: TaskCreate,
    user: CurrentUser = Depends(require_role("ceo")),
    db: Session = Depends(get_db),
) -> Any:
    try:
        _ensure_employee_exists(db, payload.assigned_to)

        # Validate priority
        priority_val = payload.priority or "medium"
        if priority_val not in ("low", "medium", "high"):
            priority_val = "medium"

        task = Task(
            title=payload.title,
            description=payload.description or "",
            assigned_to=payload.assigned_to,
            assigned_by=user.id,
            status=TaskStatus.pending,
            priority=TaskPriority(priority_val),
            progress=0,
            deadline=payload.deadline,
        )

        db.add(task)
        db.flush()

        notif = Notification(
            user_id=payload.assigned_to,
            task_id=task.id,
            message=f"New task: {task.title} — Due: {task.deadline.isoformat()}",
            is_read=False,
        )
        db.add(notif)

        db.commit()
        db.refresh(task)
        return task
    except Exception as e:
        db.rollback()
        if hasattr(e, "status_code"):
            raise
        logger.exception("create task failed")
        raise http_error(500, "Failed to create task", 500)


# ── Item routes ─────────────────────────────────────────────────────────────

@router.put("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    _: CurrentUser = Depends(require_role("ceo")),
    db: Session = Depends(get_db),
) -> Any:
    try:
        task = _get_task_or_404(db, task_id)

        if payload.assigned_to is not None:
            _ensure_employee_exists(db, payload.assigned_to)
            task.assigned_to = payload.assigned_to

        if payload.title is not None:
            task.title = payload.title
        if payload.description is not None:
            task.description = payload.description
        if payload.deadline is not None:
            task.deadline = payload.deadline
        if payload.status is not None:
            if payload.status not in (s.value for s in TaskStatus):
                raise http_error(422, "Invalid status", 422)
            task.status = TaskStatus(payload.status)
        if payload.progress is not None:
            task.progress = int(payload.progress)
        if payload.priority is not None:
            if payload.priority not in (p.value for p in TaskPriority):
                raise http_error(422, "Invalid priority", 422)
            task.priority = TaskPriority(payload.priority)

        if task.status == TaskStatus.done:
            task.progress = 100
        elif task.progress >= 100:
            task.progress = 100
            task.status = TaskStatus.done
        elif task.progress > 0 and task.status == TaskStatus.pending:
            task.status = TaskStatus.in_progress

        db.commit()
        db.refresh(task)
        return task
    except Exception as e:
        db.rollback()
        if hasattr(e, "status_code"):
            raise
        logger.exception("update task failed")
        raise http_error(500, "Failed to update task", 500)


@router.patch("/{task_id}/status", response_model=TaskOut)
def update_status(
    task_id: UUID,
    status: str,
    _: CurrentUser = Depends(require_role("ceo")),
    db: Session = Depends(get_db),
) -> Any:
    try:
        task = _get_task_or_404(db, task_id)
        if status not in (s.value for s in TaskStatus):
            raise http_error(422, "Invalid status", 422)
        task.status = TaskStatus(status)
        if task.status == TaskStatus.done:
            task.progress = 100
        db.commit()
        db.refresh(task)
        return task
    except Exception as e:
        db.rollback()
        if hasattr(e, "status_code"):
            raise
        logger.exception("update status failed")
        raise http_error(500, "Failed to update status", 500)


@router.patch("/{task_id}/done", response_model=TaskOut)
def mark_done(
    task_id: UUID,
    _: CurrentUser = Depends(require_role("ceo")),
    db: Session = Depends(get_db),
) -> Any:
    try:
        task = _get_task_or_404(db, task_id)
        task.status = TaskStatus.done
        task.progress = 100
        db.commit()
        db.refresh(task)
        return task
    except Exception as e:
        db.rollback()
        if hasattr(e, "status_code"):
            raise
        logger.exception("mark done failed")
        raise http_error(500, "Failed to mark task done", 500)


@router.patch("/{task_id}/reassign", response_model=TaskOut)
def reassign_task(
    task_id: UUID,
    payload: ReassignTask,
    _: CurrentUser = Depends(require_role("ceo")),
    db: Session = Depends(get_db),
) -> Any:
    try:
        task = _get_task_or_404(db, task_id)
        _ensure_employee_exists(db, payload.assigned_to)

        task.assigned_to = payload.assigned_to
        task.status = TaskStatus.pending
        task.progress = 0

        notif = Notification(
            user_id=payload.assigned_to,
            task_id=task.id,
            message=f"Task reassigned to you: {task.title} — Due: {task.deadline.isoformat()}",
            is_read=False,
        )
        db.add(notif)
        db.commit()
        db.refresh(task)
        return task
    except Exception as e:
        db.rollback()
        if hasattr(e, "status_code"):
            raise
        logger.exception("reassign task failed")
        raise http_error(500, "Failed to reassign task", 500)


@router.delete("/{task_id}")
def delete_task(
    task_id: UUID,
    _: CurrentUser = Depends(require_role("ceo")),
    db: Session = Depends(get_db),
) -> Any:
    try:
        # Clean up files from disk BEFORE deleting from DB
        _cleanup_task_files(task_id)

        res = db.execute(delete(Task).where(Task.id == task_id))
        if res.rowcount == 0:
            raise http_error(404, "Task not found", 404)
        db.commit()
        return {"ok": True}
    except Exception as e:
        db.rollback()
        if hasattr(e, "status_code"):
            raise
        logger.exception("delete task failed")
        raise http_error(500, "Failed to delete task", 500)


# ── Attachment routes ───────────────────────────────────────────────────────

@router.post("/{task_id}/attach", response_model=TaskOut)
async def attach_files(
    task_id: UUID,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_role("ceo")),
) -> Any:
    """Upload one or more files to a task. Each call appends to existing attachments."""
    try:
        if len(files) > MAX_FILES_PER_UPLOAD:
            raise http_error(400, f"Max {MAX_FILES_PER_UPLOAD} files per upload.", 400)

        task = _get_task_or_404(db, task_id)

        dest_dir = UPLOADS_DIR / str(task_id)
        dest_dir.mkdir(parents=True, exist_ok=True)

        for file in files:
            data = await _validate_file_size(file)
            safe_name = os.path.basename(file.filename or "attachment")
            dest_path = dest_dir / safe_name

            dest_path.write_bytes(data)

            attachment = TaskAttachment(
                task_id=task.id,
                file_name=safe_name,
                file_path=str(dest_path),
                file_size=len(data),
            )
            db.add(attachment)

            # Keep legacy single-attachment fields updated to the last file
            task.attachment_path = str(dest_path)
            task.attachment_name = safe_name

        db.commit()
        db.refresh(task)
        return task
    except Exception as e:
        db.rollback()
        if hasattr(e, "status_code"):
            raise
        logger.exception("attach files failed")
        raise http_error(500, "Failed to attach files", 500)


@router.delete("/{task_id}/attachments/{attachment_id}")
def delete_attachment(
    task_id: UUID,
    attachment_id: UUID,
    _: CurrentUser = Depends(require_role("ceo")),
    db: Session = Depends(get_db),
) -> Any:
    """Remove a single attachment from a task."""
    try:
        att = db.scalar(
            select(TaskAttachment).where(
                TaskAttachment.id == attachment_id,
                TaskAttachment.task_id == task_id,
            )
        )
        if not att:
            raise http_error(404, "Attachment not found", 404)

        path = Path(att.file_path)
        if path.exists():
            path.unlink(missing_ok=True)

        db.delete(att)
        db.commit()
        return {"ok": True}
    except Exception as e:
        db.rollback()
        if hasattr(e, "status_code"):
            raise
        logger.exception("delete attachment failed")
        raise http_error(500, "Failed to delete attachment", 500)


@router.get("/{task_id}/attachments/{attachment_id}/download")
def download_attachment(
    task_id: UUID,
    attachment_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    try:
        task = _get_task_or_404(db, task_id)
        _ensure_task_access(task, user)

        att = db.scalar(
            select(TaskAttachment).where(
                TaskAttachment.id == attachment_id,
                TaskAttachment.task_id == task_id,
            )
        )
        if not att:
            raise http_error(404, "Attachment not found", 404)

        path = Path(att.file_path)
        if not path.exists():
            raise http_error(404, "File missing on disk", 404)

        return FileResponse(
            path=str(path),
            filename=att.file_name,
            media_type="application/octet-stream",
        )
    except Exception as e:
        if hasattr(e, "status_code"):
            raise
        logger.exception("download attachment failed")
        raise http_error(500, "Failed to download attachment", 500)


@router.get("/{task_id}/attachments/{attachment_id}/preview")
def preview_attachment(
    task_id: UUID,
    attachment_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Serve the file with its real MIME type so the browser can render inline."""
    try:
        task = _get_task_or_404(db, task_id)
        _ensure_task_access(task, user)

        att = db.scalar(
            select(TaskAttachment).where(
                TaskAttachment.id == attachment_id,
                TaskAttachment.task_id == task_id,
            )
        )
        if not att:
            raise http_error(404, "Attachment not found", 404)

        path = Path(att.file_path)
        if not path.exists():
            raise http_error(404, "File missing on disk", 404)

        mime, _ = mimetypes.guess_type(att.file_name)
        if not mime:
            mime = "application/octet-stream"

        return FileResponse(
            path=str(path),
            filename=att.file_name,
            media_type=mime,
            headers={"Content-Disposition": "inline"},
        )
    except Exception as e:
        if hasattr(e, "status_code"):
            raise
        logger.exception("preview attachment failed")
        raise http_error(500, "Failed to preview attachment", 500)


# Legacy single-file download (kept for backwards compat)
@router.get("/{task_id}/download")
def download_file(
    task_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    try:
        task = _get_task_or_404(db, task_id)
        _ensure_task_access(task, user)

        if not task.attachment_path or not task.attachment_name:
            raise http_error(404, "No attachment", 404)

        path = Path(task.attachment_path)
        if not path.exists():
            raise http_error(404, "Attachment missing", 404)

        return FileResponse(
            path=str(path),
            filename=task.attachment_name,
            media_type="application/octet-stream",
        )
    except Exception as e:
        if hasattr(e, "status_code"):
            raise
        logger.exception("download file failed")
        raise http_error(500, "Failed to download file", 500)


@router.patch("/{task_id}/progress", response_model=TaskOut)
def update_progress(
    task_id: UUID,
    payload: ProgressUpdate,
    user: CurrentUser = Depends(require_role("employee")),
    db: Session = Depends(get_db),
) -> Any:
    try:
        from datetime import UTC, datetime as dt
        task = _get_task_or_404(db, task_id)
        if task.assigned_to != user.id:
            raise http_error(403, "Forbidden", 403)

        task.progress = int(payload.progress)
        if task.progress >= 100:
            task.progress = 100
            task.status = TaskStatus.done
        elif task.progress > 0:
            task.status = TaskStatus.in_progress
        else:
            task.status = TaskStatus.pending

        # Bump activity timestamp
        task.last_activity_at = dt.now(UTC)

        db.commit()
        db.refresh(task)
        return task
    except Exception as e:
        db.rollback()
        if hasattr(e, "status_code"):
            raise
        logger.exception("update progress failed")
        raise http_error(500, "Failed to update progress", 500)
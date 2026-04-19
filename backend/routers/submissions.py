from __future__ import annotations

import logging
import mimetypes
import os
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.deps import CurrentUser, get_current_user, require_role
from core.errors import http_error
from models.notification import Notification
from models.submission import TaskSubmission
from models.task import Task
from models.user import User
from schemas.task import SubmissionOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["submissions"])

UPLOADS_DIR = Path(os.getenv("UPLOADS_DIR", "/app/uploads"))

MAX_FILE_SIZE = settings.max_file_size_bytes
MAX_FILES_PER_UPLOAD = settings.max_files_per_upload


def _get_task_or_404(db: Session, task_id: UUID) -> Task:
    task = db.scalar(select(Task).where(Task.id == task_id))
    if not task:
        raise http_error(404, "Task not found", 404)
    return task


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


def _unique_on_disk_name(original_name: str) -> str:
    """Prepend a short UUID so concurrent submissions with the same name don't clash."""
    base = os.path.basename(original_name or "file")
    stem, ext = os.path.splitext(base)
    return f"{uuid4().hex[:8]}_{stem}{ext}" if stem else uuid4().hex


@router.get("/{task_id}/submissions", response_model=list[SubmissionOut])
def list_submissions(
    task_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """List all employee submissions for a task. CEO and assigned employee can view."""
    try:
        task = _get_task_or_404(db, task_id)
        if user.role != "ceo" and task.assigned_to != user.id:
            raise http_error(403, "Forbidden", 403)

        subs = list(
            db.scalars(
                select(TaskSubmission)
                .where(TaskSubmission.task_id == task_id)
                .order_by(TaskSubmission.uploaded_at.desc())
            ).all()
        )
        user_ids = {s.uploaded_by for s in subs}
        users = (
            {u.id: u.name for u in db.scalars(select(User).where(User.id.in_(user_ids))).all()}
            if user_ids else {}
        )

        return [
            SubmissionOut(
                id=s.id,
                file_name=s.file_name,
                note=s.note,
                file_size=s.file_size or 0,
                uploaded_at=s.uploaded_at,
                uploaded_by=s.uploaded_by,
                uploader_name=users.get(s.uploaded_by, "Unknown"),
            )
            for s in subs
        ]
    except Exception as e:
        if hasattr(e, "status_code"):
            raise
        logger.exception("list submissions failed")
        raise http_error(500, "Failed to list submissions", 500)


@router.post("/{task_id}/submissions", response_model=list[SubmissionOut])
async def upload_submission(
    task_id: UUID,
    files: list[UploadFile] = File(...),
    user: CurrentUser = Depends(require_role("employee")),
    db: Session = Depends(get_db),
) -> Any:
    """Employee uploads work files (deliverables) for a task."""
    try:
        if len(files) > MAX_FILES_PER_UPLOAD:
            raise http_error(400, f"Max {MAX_FILES_PER_UPLOAD} files per upload.", 400)

        task = _get_task_or_404(db, task_id)
        if task.assigned_to != user.id:
            raise http_error(403, "Forbidden", 403)

        dest_dir = UPLOADS_DIR / "submissions" / str(task_id)
        dest_dir.mkdir(parents=True, exist_ok=True)

        created: list[TaskSubmission] = []
        for file in files:
            data = await _validate_file_size(file)
            display_name = os.path.basename(file.filename or "submission")
            disk_name = _unique_on_disk_name(display_name)
            dest_path = dest_dir / disk_name
            dest_path.write_bytes(data)

            sub = TaskSubmission(
                task_id=task.id,
                uploaded_by=user.id,
                file_name=display_name,
                file_path=str(dest_path),
                file_size=len(data),
                note="",
            )
            db.add(sub)
            created.append(sub)

        # Bump last_activity_at.
        from datetime import UTC, datetime
        task.last_activity_at = datetime.now(UTC)

        # Notify CEO.
        author = db.scalar(select(User).where(User.id == user.id))
        author_name = author.name if author else "Employee"
        file_names = ", ".join(f.filename or "file" for f in files)
        notif = Notification(
            user_id=task.assigned_by,
            task_id=task.id,
            message=f"{author_name} submitted files for \"{task.title}\": {file_names[:100]}",
            is_read=False,
        )
        db.add(notif)

        db.commit()
        for s in created:
            db.refresh(s)

        return [
            SubmissionOut(
                id=s.id,
                file_name=s.file_name,
                note=s.note,
                file_size=s.file_size or 0,
                uploaded_at=s.uploaded_at,
                uploaded_by=s.uploaded_by,
                uploader_name=author_name,
            )
            for s in created
        ]
    except Exception as e:
        db.rollback()
        if hasattr(e, "status_code"):
            raise
        logger.exception("upload submission failed")
        raise http_error(500, "Failed to upload submission", 500)


@router.get("/{task_id}/submissions/{submission_id}/download")
def download_submission(
    task_id: UUID,
    submission_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    try:
        task = _get_task_or_404(db, task_id)
        if user.role != "ceo" and task.assigned_to != user.id:
            raise http_error(403, "Forbidden", 403)

        sub = db.scalar(
            select(TaskSubmission).where(
                TaskSubmission.id == submission_id,
                TaskSubmission.task_id == task_id,
            )
        )
        if not sub:
            raise http_error(404, "Submission not found", 404)

        path = Path(sub.file_path)
        if not path.exists():
            raise http_error(404, "File missing on disk", 404)

        return FileResponse(
            path=str(path), filename=sub.file_name,
            media_type="application/octet-stream",
        )
    except Exception as e:
        if hasattr(e, "status_code"):
            raise
        logger.exception("download submission failed")
        raise http_error(500, "Failed to download submission", 500)


@router.get("/{task_id}/submissions/{submission_id}/preview")
def preview_submission(
    task_id: UUID,
    submission_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    try:
        task = _get_task_or_404(db, task_id)
        if user.role != "ceo" and task.assigned_to != user.id:
            raise http_error(403, "Forbidden", 403)

        sub = db.scalar(
            select(TaskSubmission).where(
                TaskSubmission.id == submission_id,
                TaskSubmission.task_id == task_id,
            )
        )
        if not sub:
            raise http_error(404, "Submission not found", 404)

        path = Path(sub.file_path)
        if not path.exists():
            raise http_error(404, "File missing on disk", 404)

        mime, _ = mimetypes.guess_type(sub.file_name)
        if not mime:
            mime = "application/octet-stream"

        return FileResponse(
            path=str(path), filename=sub.file_name,
            media_type=mime, headers={"Content-Disposition": "inline"},
        )
    except Exception as e:
        if hasattr(e, "status_code"):
            raise
        logger.exception("preview submission failed")
        raise http_error(500, "Failed to preview submission", 500)


@router.delete("/{task_id}/submissions/{submission_id}")
def delete_submission(
    task_id: UUID,
    submission_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Employee can delete their own submission, CEO can delete any."""
    try:
        sub = db.scalar(
            select(TaskSubmission).where(
                TaskSubmission.id == submission_id,
                TaskSubmission.task_id == task_id,
            )
        )
        if not sub:
            raise http_error(404, "Submission not found", 404)
        if user.role != "ceo" and sub.uploaded_by != user.id:
            raise http_error(403, "Forbidden", 403)

        path = Path(sub.file_path)
        if path.exists():
            path.unlink(missing_ok=True)

        db.delete(sub)
        db.commit()
        return {"ok": True}
    except Exception as e:
        db.rollback()
        if hasattr(e, "status_code"):
            raise
        logger.exception("delete submission failed")
        raise http_error(500, "Failed to delete submission", 500)

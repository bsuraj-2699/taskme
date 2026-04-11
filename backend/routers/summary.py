from __future__ import annotations

import logging
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import CurrentUser, get_current_user
from core.errors import http_error
from models.task import Task, TaskStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/summary", tags=["summary"])


@router.get("/counts")
def task_counts(
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Lightweight endpoint returning only aggregated counts.

    Used by the frontend for periodic polling instead of reloading
    the full task list every 30 seconds. Returns status counts and
    a max(updated_at) timestamp so the client can decide whether
    to do a full refresh.
    """
    try:
        today = date.today()

        if user.role == "ceo":
            base = select(Task)
        else:
            base = select(Task).where(Task.assigned_to == user.id)

        counts_q = select(
            func.count().label("total"),
            func.count().filter(Task.status == TaskStatus.pending).label("pending"),
            func.count().filter(Task.status == TaskStatus.in_progress).label("in_progress"),
            func.count().filter(Task.status == TaskStatus.done).label("done"),
            func.count().filter(
                Task.deadline < today,
                Task.status != TaskStatus.done,
            ).label("overdue"),
            func.max(Task.updated_at).label("last_updated"),
        )

        if user.role != "ceo":
            counts_q = counts_q.where(Task.assigned_to == user.id)

        row = db.execute(counts_q.select_from(Task)).one()

        return {
            "total": row.total,
            "pending": row.pending,
            "in_progress": row.in_progress,
            "done": row.done,
            "overdue": row.overdue,
            "last_updated": row.last_updated.isoformat() if row.last_updated else None,
        }
    except Exception:
        logger.exception("summary counts failed")
        raise http_error(500, "Failed to fetch summary", 500)

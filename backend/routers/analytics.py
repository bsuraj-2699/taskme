from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import CurrentUser, require_role
from core.errors import http_error
from models.task import Task, TaskStatus
from models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/")
def get_analytics(
    _: CurrentUser = Depends(require_role("ceo")),
    db: Session = Depends(get_db),
) -> Any:
    """Return aggregated analytics for the CEO dashboard."""
    try:
        tasks = list(db.scalars(select(Task)).all())
        users = {str(u.id): u.name for u in db.scalars(select(User)).all()}
        today = date.today()

        total = len(tasks)
        pending = sum(1 for t in tasks if t.status == TaskStatus.pending)
        in_progress = sum(1 for t in tasks if t.status == TaskStatus.in_progress)
        done = sum(1 for t in tasks if t.status == TaskStatus.done)
        overdue = sum(
            1 for t in tasks
            if t.deadline < today and t.status != TaskStatus.done
        )

        # Average completion time (days) for done tasks
        completion_times: list[float] = []
        for t in tasks:
            if t.status == TaskStatus.done and t.created_at and t.updated_at:
                delta = (t.updated_at - t.created_at).total_seconds() / 86400.0
                completion_times.append(max(delta, 0))
        avg_completion_days = round(
            sum(completion_times) / len(completion_times), 1
        ) if completion_times else 0.0

        # Per-employee workload
        employee_workload: dict[str, dict[str, Any]] = {}
        for t in tasks:
            uid = str(t.assigned_to)
            name = users.get(uid, "Unknown")
            if uid not in employee_workload:
                employee_workload[uid] = {
                    "user_id": uid,
                    "name": name,
                    "total": 0,
                    "pending": 0,
                    "in_progress": 0,
                    "done": 0,
                    "overdue": 0,
                }
            w = employee_workload[uid]
            w["total"] += 1
            if t.status == TaskStatus.pending:
                w["pending"] += 1
            elif t.status == TaskStatus.in_progress:
                w["in_progress"] += 1
            elif t.status == TaskStatus.done:
                w["done"] += 1
            if t.deadline < today and t.status != TaskStatus.done:
                w["overdue"] += 1

        # Overdue task list
        overdue_tasks = [
            {
                "id": str(t.id),
                "title": t.title,
                "assigned_to_name": users.get(str(t.assigned_to), "Unknown"),
                "deadline": t.deadline.isoformat(),
                "days_overdue": (today - t.deadline).days,
                "progress": t.progress,
            }
            for t in tasks
            if t.deadline < today and t.status != TaskStatus.done
        ]
        overdue_tasks.sort(key=lambda x: x["days_overdue"], reverse=True)

        return {
            "total": total,
            "pending": pending,
            "in_progress": in_progress,
            "done": done,
            "overdue": overdue,
            "avg_completion_days": avg_completion_days,
            "employee_workload": list(employee_workload.values()),
            "overdue_tasks": overdue_tasks[:20],
        }
    except Exception:
        logger.exception("analytics failed")
        raise http_error(500, "Failed to compute analytics", 500)

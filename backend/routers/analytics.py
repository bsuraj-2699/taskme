from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
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
    """Return aggregated analytics for the CEO dashboard using SQL aggregations."""
    try:
        today = date.today()

        # ── Aggregated counts (single query, uses ix_tasks_status) ──────────
        counts_q = select(
            func.count().label("total"),
            func.count().filter(Task.status == TaskStatus.pending).label("pending"),
            func.count().filter(Task.status == TaskStatus.in_progress).label("in_progress"),
            func.count().filter(Task.status == TaskStatus.done).label("done"),
            func.count().filter(
                Task.deadline < today,
                Task.status != TaskStatus.done,
            ).label("overdue"),
        ).select_from(Task)

        row = db.execute(counts_q).one()
        total = row.total
        pending = row.pending
        in_progress = row.in_progress
        done = row.done
        overdue = row.overdue

        # ── Average completion time (SQL) ───────────────────────────────────
        avg_q = select(
            func.avg(
                func.extract("epoch", Task.updated_at - Task.created_at) / 86400.0
            ).label("avg_days")
        ).where(
            Task.status == TaskStatus.done,
            Task.created_at.isnot(None),
            Task.updated_at.isnot(None),
        )
        avg_days_raw = db.scalar(avg_q)
        avg_completion_days = round(float(avg_days_raw), 1) if avg_days_raw else 0.0

        # ── Per-employee workload (SQL group by) ────────────────────────────
        users_map = {str(u.id): u.name for u in db.scalars(select(User)).all()}

        workload_q = (
            select(
                Task.assigned_to,
                func.count().label("total"),
                func.count().filter(Task.status == TaskStatus.pending).label("pending"),
                func.count().filter(Task.status == TaskStatus.in_progress).label("in_progress"),
                func.count().filter(Task.status == TaskStatus.done).label("done"),
                func.count().filter(
                    Task.deadline < today,
                    Task.status != TaskStatus.done,
                ).label("overdue"),
            )
            .group_by(Task.assigned_to)
        )

        employee_workload = []
        for w in db.execute(workload_q).all():
            uid = str(w.assigned_to)
            employee_workload.append({
                "user_id": uid,
                "name": users_map.get(uid, "Unknown"),
                "total": w.total,
                "pending": w.pending,
                "in_progress": w.in_progress,
                "done": w.done,
                "overdue": w.overdue,
            })

        # ── Overdue task list (limited to top 20) ───────────────────────────
        overdue_q = (
            select(Task)
            .where(Task.deadline < today, Task.status != TaskStatus.done)
            .order_by(Task.deadline.asc())
            .limit(20)
        )
        overdue_tasks = [
            {
                "id": str(t.id),
                "title": t.title,
                "assigned_to_name": users_map.get(str(t.assigned_to), "Unknown"),
                "deadline": t.deadline.isoformat(),
                "days_overdue": (today - t.deadline).days,
                "progress": t.progress,
            }
            for t in db.scalars(overdue_q).all()
        ]
        overdue_tasks.sort(key=lambda x: x["days_overdue"], reverse=True)

        return {
            "total": total,
            "pending": pending,
            "in_progress": in_progress,
            "done": done,
            "overdue": overdue,
            "avg_completion_days": avg_completion_days,
            "employee_workload": employee_workload,
            "overdue_tasks": overdue_tasks,
        }
    except Exception:
        logger.exception("analytics failed")
        raise http_error(500, "Failed to compute analytics", 500)

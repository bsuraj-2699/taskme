"""Auto follow-up service — runs hourly via APScheduler.

Rules:
1. No activity for 24h+ on a non-done task → gentle reminder to employee
   (but only once per 24h — uses last_activity_at to avoid spam).
2. Deadline within 6 hours → urgent reminder to employee.
3. Deadline crossed and task is not done → mark as overdue, notify CEO.

Optimised: uses indexed queries with LIMIT/batching to avoid loading all tasks.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.notification import Notification
from models.task import Task, TaskStatus
from models.user import User, UserRole

logger = logging.getLogger(__name__)

# Process tasks in batches to avoid holding huge result sets in memory.
_BATCH_SIZE = 200


def run_followup_job() -> None:
    """Entry point called by APScheduler every hour."""
    from core.database import SessionLocal

    with SessionLocal() as db:
        try:
            _process_overdue(db)
            _process_deadline_approaching(db)
            _process_stale(db)
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("follow-up job failed")


def _get_ceo_ids(db: Session) -> list:
    return [
        u.id for u in db.scalars(
            select(User).where(User.role == UserRole.ceo)
        ).all()
    ]


def _process_overdue(db: Session) -> None:
    """Mark tasks with past deadlines as overdue and notify.

    We commit after every batch so the next fetch correctly excludes rows that
    were just flipped to overdue — the previous implementation relied on the
    session identity map and could loop indefinitely in edge cases.
    """
    ceo_ids = _get_ceo_ids(db)

    while True:
        now = datetime.now(UTC)
        today_date = now.date()

        # Query only tasks that are past deadline AND not already done/overdue.
        # Uses ix_tasks_status and ix_tasks_deadline indexes.
        stmt = (
            select(Task)
            .where(
                Task.deadline < today_date,
                Task.status.notin_([TaskStatus.done, TaskStatus.overdue]),
            )
            .limit(_BATCH_SIZE)
        )

        tasks = list(db.scalars(stmt).all())
        if not tasks:
            break

        for task in tasks:
            task.status = TaskStatus.overdue
            task.last_activity_at = now

            for ceo_id in ceo_ids:
                db.add(Notification(
                    user_id=ceo_id,
                    task_id=task.id,
                    message=f"OVERDUE: \"{task.title}\" was due {task.deadline.isoformat()} and is not completed.",
                    is_read=False,
                ))

            db.add(Notification(
                user_id=task.assigned_to,
                task_id=task.id,
                message=f"Your task \"{task.title}\" is now overdue. It was due {task.deadline.isoformat()}.",
                is_read=False,
            ))

        # Commit this batch so subsequent queries see the status change and
        # won't re-select the same rows.
        db.commit()

        # If we pulled fewer than a full batch, we're done.
        if len(tasks) < _BATCH_SIZE:
            break


def _process_deadline_approaching(db: Session) -> None:
    """If deadline is within 6 hours → send urgent reminder (once per 6h window)."""
    now = datetime.now(UTC)
    today_date = now.date()
    # Only look at tasks due today that are not done/overdue.
    stmt = (
        select(Task)
        .where(
            Task.deadline == today_date,
            Task.status.notin_([TaskStatus.done, TaskStatus.overdue]),
        )
        .limit(_BATCH_SIZE)
    )

    tasks = list(db.scalars(stmt).all())
    recent_cutoff = now - timedelta(hours=6)

    for task in tasks:
        deadline_dt = datetime(
            task.deadline.year, task.deadline.month, task.deadline.day,
            23, 59, 59, tzinfo=UTC,
        )
        time_left = deadline_dt - now

        if time_left.total_seconds() <= 0 or time_left.total_seconds() > 6 * 3600:
            continue

        # Check for existing urgent reminder — use indexed query.
        existing = db.scalar(
            select(Notification.id).where(
                Notification.task_id == task.id,
                Notification.user_id == task.assigned_to,
                Notification.created_at >= recent_cutoff,
                Notification.message.like("URGENT%"),
            ).limit(1)
        )
        if existing:
            continue

        hours_left = int(time_left.total_seconds() / 3600)
        db.add(Notification(
            user_id=task.assigned_to,
            task_id=task.id,
            message=f"URGENT: \"{task.title}\" is due in ~{hours_left}h. Please complete it soon.",
            is_read=False,
        ))

    db.flush()


def _process_stale(db: Session) -> None:
    """If no activity for threshold hours → gentle reminder."""
    now = datetime.now(UTC)

    # Only check tasks that haven't been touched in at least 12 hours
    # (the minimum threshold). This uses the composite index on status+last_activity_at.
    min_stale_cutoff = now - timedelta(hours=12)

    stmt = (
        select(Task)
        .where(
            Task.status.notin_([TaskStatus.done, TaskStatus.overdue]),
            Task.last_activity_at <= min_stale_cutoff,
        )
        .limit(_BATCH_SIZE)
    )

    tasks = list(db.scalars(stmt).all())

    for task in tasks:
        if not task.last_activity_at:
            continue

        hours_since_activity = (now - task.last_activity_at).total_seconds() / 3600

        # Scale threshold based on deadline proximity.
        deadline_dt = datetime(
            task.deadline.year, task.deadline.month, task.deadline.day,
            23, 59, 59, tzinfo=UTC,
        )
        days_until_deadline = (deadline_dt - now).total_seconds() / 86400

        if days_until_deadline > 7:
            threshold_hours = 48
        elif days_until_deadline > 3:
            threshold_hours = 24
        else:
            threshold_hours = 12

        if hours_since_activity < threshold_hours:
            continue

        # Check for existing stale reminder.
        recent_cutoff = now - timedelta(hours=threshold_hours)
        existing = db.scalar(
            select(Notification.id).where(
                Notification.task_id == task.id,
                Notification.user_id == task.assigned_to,
                Notification.created_at >= recent_cutoff,
                Notification.message.like("Reminder%"),
            ).limit(1)
        )
        if existing:
            continue

        db.add(Notification(
            user_id=task.assigned_to,
            task_id=task.id,
            message=(
                f"Reminder: \"{task.title}\" has had no updates for "
                f"{int(hours_since_activity)}h. Due: {task.deadline.isoformat()}"
            ),
            is_read=False,
        ))

    db.flush()

"""Auto follow-up service — runs hourly via APScheduler.

Rules:
1. No activity for 24h+ on a non-done task → gentle reminder to employee
   (but only once per 24h — uses last_activity_at to avoid spam)
2. Deadline within 6 hours → urgent reminder to employee
3. Deadline crossed and task is not done → mark as overdue, notify CEO
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


def run_followup_job() -> None:
    """Entry point called by APScheduler every hour."""
    from core.database import SessionLocal

    with SessionLocal() as db:
        _process_followups(db)


def _process_followups(db: Session) -> None:
    now = datetime.now(UTC)
    today_date = now.date()

    # Get all non-done tasks
    tasks = list(
        db.scalars(
            select(Task).where(Task.status.notin_([TaskStatus.done]))
        ).all()
    )

    # Get CEO user(s) for notifications
    ceo_users = list(
        db.scalars(select(User).where(User.role == UserRole.ceo)).all()
    )
    ceo_ids = [u.id for u in ceo_users]

    for task in tasks:
        try:
            _check_overdue(db, task, today_date, ceo_ids, now)
            _check_deadline_approaching(db, task, now)
            _check_stale(db, task, now)
        except Exception:
            logger.exception("follow-up check failed for task %s", task.id)

    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("follow-up commit failed")


def _check_overdue(db: Session, task: Task, today_date, ceo_ids: list, now: datetime) -> None:
    """If deadline has passed and task is not done/overdue → mark overdue and notify CEO."""
    if task.deadline >= today_date:
        return
    if task.status == TaskStatus.overdue:
        return  # Already marked

    task.status = TaskStatus.overdue
    task.last_activity_at = now

    for ceo_id in ceo_ids:
        notif = Notification(
            user_id=ceo_id,
            task_id=task.id,
            message=f"OVERDUE: \"{task.title}\" was due {task.deadline.isoformat()} and is not completed.",
            is_read=False,
        )
        db.add(notif)

    # Also notify the employee
    notif = Notification(
        user_id=task.assigned_to,
        task_id=task.id,
        message=f"Your task \"{task.title}\" is now overdue. It was due {task.deadline.isoformat()}.",
        is_read=False,
    )
    db.add(notif)


def _check_deadline_approaching(db: Session, task: Task, now: datetime) -> None:
    """If deadline is within 6 hours → send urgent reminder (once per 6h window)."""
    # Convert date deadline to datetime (end of day)
    deadline_dt = datetime(task.deadline.year, task.deadline.month, task.deadline.day, 23, 59, 59, tzinfo=UTC)
    time_left = deadline_dt - now

    if time_left.total_seconds() <= 0 or time_left.total_seconds() > 6 * 3600:
        return  # Not in the 6-hour window

    # Check if we already sent an urgent reminder recently (within last 6 hours)
    recent_cutoff = now - timedelta(hours=6)
    existing = db.scalar(
        select(Notification).where(
            Notification.task_id == task.id,
            Notification.user_id == task.assigned_to,
            Notification.created_at >= recent_cutoff,
            Notification.message.like("%URGENT%"),
        )
    )
    if existing:
        return  # Already reminded

    hours_left = int(time_left.total_seconds() / 3600)
    notif = Notification(
        user_id=task.assigned_to,
        task_id=task.id,
        message=f"URGENT: \"{task.title}\" is due in ~{hours_left}h. Please complete it soon.",
        is_read=False,
    )
    db.add(notif)


def _check_stale(db: Session, task: Task, now: datetime) -> None:
    """If no activity for 24h+ → gentle reminder (but scale with deadline proximity)."""
    if not task.last_activity_at:
        return

    hours_since_activity = (now - task.last_activity_at).total_seconds() / 3600

    # Scale: if deadline is far (>7d), only remind every 48h; if close (<=3d), every 24h
    deadline_dt = datetime(task.deadline.year, task.deadline.month, task.deadline.day, 23, 59, 59, tzinfo=UTC)
    days_until_deadline = (deadline_dt - now).total_seconds() / 86400

    if days_until_deadline > 7:
        threshold_hours = 48
    elif days_until_deadline > 3:
        threshold_hours = 24
    else:
        threshold_hours = 12  # Close to deadline, more frequent

    if hours_since_activity < threshold_hours:
        return

    # Check we haven't already sent a stale reminder recently
    recent_cutoff = now - timedelta(hours=threshold_hours)
    existing = db.scalar(
        select(Notification).where(
            Notification.task_id == task.id,
            Notification.user_id == task.assigned_to,
            Notification.created_at >= recent_cutoff,
            Notification.message.like("%no updates%"),
        )
    )
    if existing:
        return

    notif = Notification(
        user_id=task.assigned_to,
        task_id=task.id,
        message=f"Reminder: \"{task.title}\" has had no updates for {int(hours_since_activity)}h. Due: {task.deadline.isoformat()}",
        is_read=False,
    )
    db.add(notif)

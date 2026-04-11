from __future__ import annotations

import logging
import math
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from apscheduler.triggers.cron import CronTrigger
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from core.config import settings
from core.scheduler import get_scheduler
from core.database import get_db
from core.deps import CurrentUser, require_role
from core.errors import http_error
from models.eod_report import EODReport
from models.report_schedule import ReportSchedule
from models.task import Task, TaskStatus
from models.user import User
from schemas.report import PaginatedReports, ReportListItemOut, ReportOut, ScheduleOut, ScheduleUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _get_or_create_schedule(db: Session) -> ReportSchedule:
    sched = db.get(ReportSchedule, 1)
    if not sched:
        sched = ReportSchedule(id=1)
        db.add(sched)
        db.commit()
        db.refresh(sched)
    return sched


def generate_eod_report(db: Session) -> EODReport:
    import json
    today = date.today()
    tasks = list(db.scalars(select(Task)).all())
    users = {str(u.id): u.name for u in db.scalars(select(User)).all()}

    total = len(tasks)
    pending = sum(1 for t in tasks if t.status == TaskStatus.pending)
    in_progress = sum(1 for t in tasks if t.status == TaskStatus.in_progress)
    done = sum(1 for t in tasks if t.status == TaskStatus.done)
    overdue = sum(1 for t in tasks if t.status == TaskStatus.overdue)

    # Build structured task rows with submissions
    task_rows: list[dict] = []
    for t in tasks:
        subs = []
        if hasattr(t, "submissions") and t.submissions:
            for s in t.submissions:
                subs.append({
                    "id": str(s.id),
                    "file_name": s.file_name,
                    "uploaded_at": s.uploaded_at.isoformat() if s.uploaded_at else "",
                    "task_id": str(t.id),
                })
        task_rows.append({
            "id": str(t.id),
            "title": t.title,
            "assigned_to_name": users.get(str(t.assigned_to), "Unknown"),
            "status": t.status.value,
            "progress": t.progress,
            "deadline": t.deadline.isoformat(),
            "submissions": subs,
        })

    content = json.dumps({"tasks": task_rows, "overdue": overdue})

    report = EODReport(
        report_date=today,
        total_tasks=total,
        pending=pending,
        in_progress=in_progress,
        done=done,
        content=content,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/", response_model=PaginatedReports)
def list_reports(
    _: CurrentUser = Depends(require_role("ceo")),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Any:
    try:
        count_q = select(func.count()).select_from(EODReport)
        total = db.scalar(count_q) or 0
        total_pages = max(1, math.ceil(total / page_size))

        reports = list(
            db.scalars(
                select(EODReport)
                .order_by(desc(EODReport.generated_at))
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return PaginatedReports(
            items=reports,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception:
        logger.exception("list reports failed")
        raise http_error(500, "Failed to list reports", 500)


@router.get("/schedule", response_model=ScheduleOut)
def get_schedule(
    _: CurrentUser = Depends(require_role("ceo")),
    db: Session = Depends(get_db),
) -> Any:
    try:
        sched = _get_or_create_schedule(db)
        return sched
    except Exception:
        logger.exception("get schedule failed")
        raise http_error(500, "Failed to get schedule", 500)


@router.post("/schedule", response_model=ScheduleOut)
def update_schedule(
    payload: ScheduleUpdate,
    _: CurrentUser = Depends(require_role("ceo")),
    db: Session = Depends(get_db),
) -> Any:
    try:
        sched = _get_or_create_schedule(db)
        sched.report_time = payload.report_time
        sched.timezone = payload.timezone
        sched.is_active = bool(payload.is_active)
        db.commit()
        db.refresh(sched)

        # Reschedule job on change (if scheduler is available)
        scheduler = get_scheduler()
        if scheduler.running:
            if sched.is_active:
                h, m = sched.report_time.split(":")
                scheduler.add_job(
                    func=_run_report_job,
                    trigger=CronTrigger(hour=int(h), minute=int(m), timezone=sched.timezone),
                    id="eod_report",
                    replace_existing=True,
                )
            else:
                try:
                    scheduler.remove_job("eod_report")
                except Exception:
                    pass
        return sched
    except Exception:
        db.rollback()
        logger.exception("update schedule failed")
        raise http_error(500, "Failed to update schedule", 500)


@router.post("/generate", response_model=ReportOut)
def generate_now(
    _: CurrentUser = Depends(require_role("ceo")),
    db: Session = Depends(get_db),
) -> Any:
    try:
        return generate_eod_report(db)
    except Exception:
        db.rollback()
        logger.exception("generate report failed")
        raise http_error(500, "Failed to generate report", 500)


@router.get("/{report_id}", response_model=ReportOut)
def get_report(
    report_id: UUID,
    _: CurrentUser = Depends(require_role("ceo")),
    db: Session = Depends(get_db),
) -> Any:
    try:
        report = db.scalar(select(EODReport).where(EODReport.id == report_id))
        if not report:
            raise http_error(404, "Report not found", 404)
        return report
    except Exception as e:
        if hasattr(e, "status_code"):
            raise
        logger.exception("get report failed")
        raise http_error(500, "Failed to get report", 500)


def _run_report_job() -> None:
    from core.database import SessionLocal

    with SessionLocal() as db:
        generate_eod_report(db)

from __future__ import annotations

import io
import json
import logging
import math
from calendar import monthrange
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID

from apscheduler.triggers.cron import CronTrigger
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from core.config import settings
from core.scheduler import get_scheduler
from core.database import get_db
from core.deps import CurrentUser, require_role
from core.errors import http_error
from models.eod_report import EODReport
from models.monthly_report import MonthlyReport
from models.report_schedule import ReportSchedule
from models.task import Task, TaskStatus
from models.user import User
from schemas.report import (
    MonthlyReportOut,
    PaginatedMonthlyReports,
    PaginatedReports,
    ReportOut,
    ScheduleOut,
    ScheduleUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])


# ── Schedule helpers ────────────────────────────────────────────────────────


def _get_or_create_schedule(db: Session) -> ReportSchedule:
    sched = db.get(ReportSchedule, 1)
    if not sched:
        sched = ReportSchedule(id=1)
        db.add(sched)
        db.commit()
        db.refresh(sched)
    return sched


# ── Daily (EOD) report generation ───────────────────────────────────────────


def generate_eod_report(db: Session) -> EODReport:
    """Generate and persist an end-of-day report."""
    today = date.today()
    tasks = list(db.scalars(select(Task)).all())
    users = {str(u.id): u.name for u in db.scalars(select(User)).all()}

    total = len(tasks)
    pending = sum(1 for t in tasks if t.status == TaskStatus.pending)
    in_progress = sum(1 for t in tasks if t.status == TaskStatus.in_progress)
    done = sum(1 for t in tasks if t.status == TaskStatus.done)
    overdue = sum(1 for t in tasks if t.status == TaskStatus.overdue)

    task_rows: list[dict] = []
    for t in tasks:
        subs = []
        if t.submissions:
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
        overdue=overdue,
        content=content,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def _run_report_job() -> None:
    """APScheduler entry point for daily report generation."""
    from core.database import SessionLocal

    with SessionLocal() as db:
        generate_eod_report(db)


# ── Monthly report generation ───────────────────────────────────────────────


def _month_bounds(ref: date) -> tuple[date, date]:
    """Return (first_day, last_day) of the month containing `ref`."""
    first = ref.replace(day=1)
    last = first.replace(day=monthrange(first.year, first.month)[1])
    return first, last


def generate_monthly_report(db: Session, month_ref: date | None = None) -> MonthlyReport:
    """Generate and persist a monthly report for the month containing `month_ref`.

    If `month_ref` is None, defaults to the current month.
    Aggregates tasks whose deadline falls inside the month, plus an overall snapshot.
    """
    if month_ref is None:
        month_ref = date.today()
    month_start, month_end = _month_bounds(month_ref)

    # Pull tasks whose deadline is within the month OR that were updated in the month.
    # We union both so the report reflects in-month activity as well as in-month deliverables.
    all_tasks = list(db.scalars(select(Task)).all())
    users = {str(u.id): u.name for u in db.scalars(select(User)).all()}

    def _in_month(t: Task) -> bool:
        if t.deadline and month_start <= t.deadline <= month_end:
            return True
        if t.updated_at and month_start <= t.updated_at.date() <= month_end:
            return True
        return False

    tasks = [t for t in all_tasks if _in_month(t)]

    total = len(tasks)
    pending = sum(1 for t in tasks if t.status == TaskStatus.pending)
    in_progress = sum(1 for t in tasks if t.status == TaskStatus.in_progress)
    done = sum(1 for t in tasks if t.status == TaskStatus.done)
    overdue = sum(1 for t in tasks if t.status == TaskStatus.overdue)

    # Per-employee breakdown for richer monthly reporting.
    by_employee: dict[str, dict[str, Any]] = {}
    for t in tasks:
        uid = str(t.assigned_to)
        entry = by_employee.setdefault(uid, {
            "user_id": uid,
            "name": users.get(uid, "Unknown"),
            "total": 0,
            "pending": 0,
            "in_progress": 0,
            "done": 0,
            "overdue": 0,
        })
        entry["total"] += 1
        entry[t.status.value] = entry.get(t.status.value, 0) + 1

    task_rows: list[dict[str, Any]] = []
    for t in tasks:
        task_rows.append({
            "id": str(t.id),
            "title": t.title,
            "assigned_to_name": users.get(str(t.assigned_to), "Unknown"),
            "status": t.status.value,
            "priority": t.priority.value,
            "progress": t.progress,
            "deadline": t.deadline.isoformat(),
            "created_at": t.created_at.isoformat() if t.created_at else "",
            "updated_at": t.updated_at.isoformat() if t.updated_at else "",
        })

    content = json.dumps({
        "month_start": month_start.isoformat(),
        "month_end": month_end.isoformat(),
        "tasks": task_rows,
        "by_employee": list(by_employee.values()),
    })

    report = MonthlyReport(
        month_start=month_start,
        total_tasks=total,
        pending=pending,
        in_progress=in_progress,
        done=done,
        overdue=overdue,
        content=content,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def _run_monthly_report_job() -> None:
    """APScheduler entry point for monthly report generation."""
    from core.database import SessionLocal

    with SessionLocal() as db:
        generate_monthly_report(db)


# ── Scheduler wiring helpers (called from main.py and update_schedule) ──────


def _reschedule_eod(sched: ReportSchedule) -> None:
    scheduler = get_scheduler()
    if not scheduler.running:
        return
    if sched.is_active:
        try:
            h, m = sched.report_time.split(":")
            scheduler.add_job(
                func=_run_report_job,
                trigger=CronTrigger(hour=int(h), minute=int(m), timezone=sched.timezone),
                id="eod_report",
                replace_existing=True,
            )
        except Exception:
            logger.exception("Failed to reschedule eod_report job")
    else:
        try:
            scheduler.remove_job("eod_report")
        except Exception:
            pass


def _reschedule_monthly(sched: ReportSchedule) -> None:
    scheduler = get_scheduler()
    if not scheduler.running:
        return
    if sched.monthly_is_active:
        try:
            h, m = sched.monthly_report_time.split(":")
            # Clamp day to 1..28 so it always fires (avoids missing Feb/30-day months).
            day = max(1, min(28, int(sched.monthly_day or 1)))
            scheduler.add_job(
                func=_run_monthly_report_job,
                trigger=CronTrigger(
                    day=day, hour=int(h), minute=int(m), timezone=sched.timezone,
                ),
                id="monthly_report",
                replace_existing=True,
            )
        except Exception:
            logger.exception("Failed to reschedule monthly_report job")
    else:
        try:
            scheduler.remove_job("monthly_report")
        except Exception:
            pass


# ── Daily report endpoints ──────────────────────────────────────────────────


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
        return _get_or_create_schedule(db)
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
        # Daily fields (always sent).
        sched.report_time = payload.report_time
        sched.timezone = payload.timezone
        sched.is_active = bool(payload.is_active)
        # Monthly fields (optional — only apply if provided).
        if payload.monthly_is_active is not None:
            sched.monthly_is_active = bool(payload.monthly_is_active)
        if payload.monthly_day is not None:
            sched.monthly_day = max(1, min(28, int(payload.monthly_day)))
        if payload.monthly_report_time is not None:
            sched.monthly_report_time = payload.monthly_report_time
        db.commit()
        db.refresh(sched)

        _reschedule_eod(sched)
        _reschedule_monthly(sched)

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


# ── Monthly report endpoints ────────────────────────────────────────────────


@router.get("/monthly/", response_model=PaginatedMonthlyReports)
def list_monthly_reports(
    _: CurrentUser = Depends(require_role("ceo")),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Any:
    try:
        count_q = select(func.count()).select_from(MonthlyReport)
        total = db.scalar(count_q) or 0
        total_pages = max(1, math.ceil(total / page_size))

        reports = list(
            db.scalars(
                select(MonthlyReport)
                .order_by(desc(MonthlyReport.generated_at))
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return PaginatedMonthlyReports(
            items=reports,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception:
        logger.exception("list monthly reports failed")
        raise http_error(500, "Failed to list monthly reports", 500)


@router.post("/monthly/generate", response_model=MonthlyReportOut)
def generate_monthly_now(
    _: CurrentUser = Depends(require_role("ceo")),
    db: Session = Depends(get_db),
) -> Any:
    try:
        return generate_monthly_report(db)
    except Exception:
        db.rollback()
        logger.exception("generate monthly report failed")
        raise http_error(500, "Failed to generate monthly report", 500)


@router.get("/monthly/{report_id}", response_model=MonthlyReportOut)
def get_monthly_report(
    report_id: UUID,
    _: CurrentUser = Depends(require_role("ceo")),
    db: Session = Depends(get_db),
) -> Any:
    try:
        report = db.scalar(select(MonthlyReport).where(MonthlyReport.id == report_id))
        if not report:
            raise http_error(404, "Monthly report not found", 404)
        return report
    except Exception as e:
        if hasattr(e, "status_code"):
            raise
        logger.exception("get monthly report failed")
        raise http_error(500, "Failed to get monthly report", 500)


@router.get("/monthly/{report_id}/pdf")
def download_monthly_report_pdf(
    report_id: UUID,
    _: CurrentUser = Depends(require_role("ceo")),
    db: Session = Depends(get_db),
) -> Any:
    """Generate and stream a PDF version of a monthly report."""
    try:
        report = db.scalar(select(MonthlyReport).where(MonthlyReport.id == report_id))
        if not report:
            raise http_error(404, "Monthly report not found", 404)

        try:
            parsed = json.loads(report.content or "{}")
        except Exception:
            parsed = {}
        task_rows: list[dict] = parsed.get("tasks", []) or []
        by_employee: list[dict] = parsed.get("by_employee", []) or []

        pdf_bytes = _build_monthly_pdf(report, task_rows, by_employee)

        filename = f"monthly-report-{report.month_start.isoformat()}.pdf"
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        if hasattr(e, "status_code"):
            raise
        logger.exception("download monthly pdf failed")
        raise http_error(500, "Failed to generate PDF", 500)


# ── PDF builder ─────────────────────────────────────────────────────────────


def _build_monthly_pdf(
    report: MonthlyReport,
    task_rows: list[dict],
    by_employee: list[dict],
) -> bytes:
    """Build a nicely formatted monthly-report PDF and return the bytes."""
    # Imported lazily so the rest of the module still loads if reportlab is missing
    # (e.g. during a partial `pip install`).
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=f"Monthly Report — {report.month_start.isoformat()}",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleOrange",
        parent=styles["Title"],
        textColor=colors.HexColor("#1A1A1A"),
        fontSize=22,
        leading=26,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        textColor=colors.HexColor("#6B7280"),
        fontSize=11,
        leading=14,
        spaceAfter=14,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#F97316"),
        fontSize=14,
        leading=18,
        spaceBefore=10,
        spaceAfter=6,
    )

    story: list[Any] = []

    # Title + generated timestamp.
    month_label = report.month_start.strftime("%B %Y")
    story.append(Paragraph(f"Monthly Report — {month_label}", title_style))
    gen_at = (
        report.generated_at.strftime("%Y-%m-%d %H:%M UTC")
        if report.generated_at
        else "—"
    )
    story.append(Paragraph(f"Generated at {gen_at}", subtitle_style))

    # Summary table.
    story.append(Paragraph("Summary", section_style))
    summary_header = ["Total", "Pending", "In Progress", "Done", "Overdue"]
    summary_row = [
        str(report.total_tasks),
        str(report.pending),
        str(report.in_progress),
        str(report.done),
        str(report.overdue),
    ]
    summary_table = Table(
        [summary_header, summary_row],
        colWidths=[50 * mm] * 5,
        hAlign="LEFT",
    )
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A2B56")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#FFF8F3")),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#1A1A1A")),
        ("FONTSIZE", (0, 1), (-1, 1), 14),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("TOPPADDING", (0, 1), (-1, 1), 10),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 10),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 10))

    # Per-employee breakdown.
    if by_employee:
        story.append(Paragraph("Employee Breakdown", section_style))
        emp_data = [["Employee", "Total", "Pending", "In Progress", "Done", "Overdue"]]
        for e in by_employee:
            emp_data.append([
                str(e.get("name", "—")),
                str(e.get("total", 0)),
                str(e.get("pending", 0)),
                str(e.get("in_progress", 0)),
                str(e.get("done", 0)),
                str(e.get("overdue", 0)),
            ])
        emp_table = Table(
            emp_data,
            colWidths=[70 * mm, 25 * mm, 25 * mm, 35 * mm, 25 * mm, 25 * mm],
            repeatRows=1,
        )
        emp_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A2B56")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
        ]))
        story.append(emp_table)
        story.append(Spacer(1, 10))

    # Task table.
    story.append(Paragraph("Tasks", section_style))
    if not task_rows:
        story.append(Paragraph("No tasks in this month.", styles["Italic"]))
    else:
        task_data = [[
            "Title", "Assigned To", "Priority", "Status",
            "Progress", "Deadline", "Updated",
        ]]
        # reportlab wraps Paragraph cells; plain strings don't wrap. Wrap the title.
        body_cell_style = ParagraphStyle(
            "Body", parent=styles["Normal"], fontSize=8, leading=10,
        )
        for t in task_rows:
            title_p = Paragraph(str(t.get("title", "")), body_cell_style)
            task_data.append([
                title_p,
                str(t.get("assigned_to_name", "—")),
                str(t.get("priority", "—")).title(),
                str(t.get("status", "—")).replace("_", " ").title(),
                f"{t.get('progress', 0)}%",
                str(t.get("deadline", "—")),
                (t.get("updated_at") or "")[:10],
            ])
        task_table = Table(
            task_data,
            colWidths=[70 * mm, 40 * mm, 22 * mm, 30 * mm, 22 * mm, 28 * mm, 28 * mm],
            repeatRows=1,
        )
        task_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F97316")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("TOPPADDING", (0, 1), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ]))
        story.append(task_table)

    doc.build(story)
    buf.seek(0)
    return buf.read()

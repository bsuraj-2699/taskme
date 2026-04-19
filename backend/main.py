from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from core.config import settings
from core.database import SessionLocal
from core.followup import run_followup_job
from core.logging import setup_logging
from core.scheduler import get_scheduler
from models import (  # noqa: F401 — registers all mappers
    EODReport,
    MonthlyReport,
    Notification,
    ReportSchedule,
    Task,
    TaskAttachment,
    TaskComment,
    TaskSubmission,
    User,
)
from routers import (
    analytics,
    auth,
    comments,
    notifications,
    reports,
    submissions,
    summary,
    tasks,
    users,
)
from routers.reports import (
    _get_or_create_schedule,
    _reschedule_eod,
    _reschedule_monthly,
)

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown. Replaces the deprecated @app.on_event hooks."""
    # ── Startup ────────────────────────────────────────────────────────────
    # 1. Ensure uploads dir exists.
    os.makedirs(os.getenv("UPLOADS_DIR", "/app/uploads"), exist_ok=True)

    # 2. Start APScheduler and register all recurring jobs.
    scheduler = get_scheduler()
    if not scheduler.running:
        try:
            scheduler.start()
        except Exception:
            logger.exception("Failed to start APScheduler")

    # Daily + monthly report jobs (driven by DB-persisted schedule).
    try:
        with SessionLocal() as db:
            sched = _get_or_create_schedule(db)
            _reschedule_eod(sched)
            _reschedule_monthly(sched)
    except Exception:
        logger.exception("Failed to schedule report jobs")

    # Follow-up job runs every hour and never depends on DB state.
    try:
        scheduler.add_job(
            func=run_followup_job,
            trigger=IntervalTrigger(hours=1),
            id="followup_check",
            replace_existing=True,
            max_instances=1,
        )
    except Exception:
        logger.exception("Failed to schedule follow-up job")

    yield

    # ── Shutdown ───────────────────────────────────────────────────────────
    try:
        if scheduler.running:
            scheduler.shutdown(wait=False)
    except Exception:
        logger.exception("Failed to shutdown scheduler")


app = FastAPI(title="Taskme API", version="1.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(settings.backend_cors_origin).rstrip("/")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

app.state.limiter = auth.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"error": True, "message": "Validation error", "code": 422, "details": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"error": True, "message": "Internal server error", "code": 500},
    )


@app.get("/api/health")
def health() -> Any:
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "db": "disconnected"},
        )


app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(comments.router)
app.include_router(submissions.router)
app.include_router(users.router)
app.include_router(notifications.router)
app.include_router(reports.router)
app.include_router(analytics.router)
app.include_router(summary.router)

from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from core.config import settings
from core.database import SessionLocal
from core.logging import setup_logging
from core.scheduler import get_scheduler
from models import (  # noqa: F401 — registers all mappers
    EODReport,
    Notification,
    ReportSchedule,
    Task,
    TaskAttachment,
    User,
)
from routers import auth, notifications, reports, tasks, users
from routers.reports import _run_report_job, _get_or_create_schedule
from apscheduler.triggers.cron import CronTrigger

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Taskme API", version="1.0.0")


@app.on_event("startup")
def _ensure_uploads_dir() -> None:
    os.makedirs(os.getenv("UPLOADS_DIR", "/app/uploads"), exist_ok=True)


@app.on_event("startup")
def _start_eod_scheduler() -> None:
    """Start APScheduler and schedule the EOD report job based on DB settings."""
    try:
        scheduler = get_scheduler()
        if not scheduler.running:
            scheduler.start()

        with SessionLocal() as db:
            sched = _get_or_create_schedule(db)
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
    except Exception:
        logger.exception("Failed to start EOD scheduler")


@app.on_event("shutdown")
def _stop_scheduler() -> None:
    try:
        scheduler = get_scheduler()
        if scheduler.running:
            scheduler.shutdown(wait=False)
    except Exception:
        logger.exception("Failed to shutdown scheduler")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(settings.backend_cors_origin)],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    return JSONResponse(status_code=500, content={"error": True, "message": "Internal server error", "code": 500})


@app.get("/api/health")
def health() -> Any:
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "degraded", "db": "disconnected"})


app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(users.router)
app.include_router(notifications.router)
app.include_router(reports.router)
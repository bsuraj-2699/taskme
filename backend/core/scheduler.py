from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler

# Global scheduler instance (started in main.py startup).
scheduler: BackgroundScheduler | None = None


def get_scheduler() -> BackgroundScheduler:
    global scheduler
    if scheduler is None:
        scheduler = BackgroundScheduler()
    return scheduler


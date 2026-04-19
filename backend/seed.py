from __future__ import annotations

import os
from datetime import date, timedelta

from sqlalchemy import select

from core.database import SessionLocal
from core.security import hash_password
from models.task import Task, TaskPriority, TaskStatus
from models.user import User, UserRole


def _req(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(f"Missing required env var: {name}")
    return val


def run() -> None:
    with SessionLocal() as db:
        existing = db.scalar(select(User.id).limit(1))
        if existing:
            print("Seed skipped: users already exist.")
            return

        ceo = User(
            name="CEO",
            username=_req("SEED_CEO_USERNAME"),
            hashed_password=hash_password(_req("SEED_CEO_PASSWORD")),
            role=UserRole.ceo,
            is_active=True,
        )
        emp1 = User(
            name="Employee 1",
            username=_req("SEED_EMP1_USERNAME"),
            hashed_password=hash_password(_req("SEED_EMP1_PASSWORD")),
            role=UserRole.employee,
            is_active=True,
        )
        emp2 = User(
            name="Employee 2",
            username=_req("SEED_EMP2_USERNAME"),
            hashed_password=hash_password(_req("SEED_EMP2_PASSWORD")),
            role=UserRole.employee,
            is_active=True,
        )
        emp3 = User(
            name="Employee 3",
            username=_req("SEED_EMP3_USERNAME"),
            hashed_password=hash_password(_req("SEED_EMP3_PASSWORD")),
            role=UserRole.employee,
            is_active=True,
        )
        db.add_all([ceo, emp1, emp2, emp3])
        db.flush()

        today = date.today()
        tasks = [
            Task(
                title="Prepare onboarding checklist",
                description="Draft onboarding steps for new hires, including IT provisioning, HR paperwork, and first-week schedule.",
                assigned_to=emp1.id,
                assigned_by=ceo.id,
                status=TaskStatus.pending,
                priority=TaskPriority.medium,
                progress=0,
                deadline=today + timedelta(days=7),
            ),
            Task(
                title="Client follow-up emails",
                description="Send follow-up emails to 3 clients regarding the Q2 contract renewals.",
                assigned_to=emp2.id,
                assigned_by=ceo.id,
                status=TaskStatus.in_progress,
                priority=TaskPriority.high,
                progress=45,
                deadline=today + timedelta(days=3),
            ),
            Task(
                title="Quarterly report draft",
                description="Create initial draft for quarterly report with KPIs, wins, and risks.",
                assigned_to=emp3.id,
                assigned_by=ceo.id,
                status=TaskStatus.done,
                priority=TaskPriority.high,
                progress=100,
                deadline=today - timedelta(days=1),
            ),
            Task(
                title="Update office plant inventory",
                description="Low-priority task: catalogue current plants by room and note any replacements needed.",
                assigned_to=emp1.id,
                assigned_by=ceo.id,
                status=TaskStatus.pending,
                priority=TaskPriority.low,
                progress=0,
                deadline=today + timedelta(days=14),
            ),
        ]
        db.add_all(tasks)
        db.commit()

    print("Seed complete.")


if __name__ == "__main__":
    run()

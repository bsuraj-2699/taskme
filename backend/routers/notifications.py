from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import CurrentUser, get_current_user
from core.errors import http_error
from models.notification import Notification
from schemas.notification import NotificationOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("/", response_model=list[NotificationOut])
def unread_notifications(
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    try:
        notifs = list(
            db.scalars(
                select(Notification)
                .where(Notification.user_id == user.id, Notification.is_read == False)  # noqa: E712
                .order_by(Notification.created_at.desc())
            ).all()
        )
        return notifs
    except Exception:
        logger.exception("fetch notifications failed")
        raise http_error(500, "Failed to fetch notifications", 500)


@router.get("/poll", response_model=NotificationOut | None)
def poll(
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    try:
        notif = db.scalar(
            select(Notification)
            .where(Notification.user_id == user.id, Notification.is_read == False)  # noqa: E712
            .order_by(Notification.created_at.desc())
            .limit(1)
        )
        return notif
    except Exception:
        logger.exception("poll notifications failed")
        raise http_error(500, "Failed to poll notifications", 500)


@router.patch("/{notification_id}/read")
def mark_read(
    notification_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    try:
        notif = db.scalar(select(Notification).where(Notification.id == notification_id))
        if not notif:
            raise http_error(404, "Notification not found", 404)
        if notif.user_id != user.id:
            raise http_error(403, "Forbidden", 403)
        notif.is_read = True
        db.commit()
        return {"ok": True}
    except Exception as e:
        db.rollback()
        if hasattr(e, "status_code"):
            raise
        logger.exception("mark read failed")
        raise http_error(500, "Failed to mark read", 500)

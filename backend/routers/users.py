from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import CurrentUser, require_role
from core.errors import http_error
from core.security import hash_password
from models.user import User, UserRole
from schemas.user import UserCreate, UserOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/", response_model=list[UserOut])
def list_users(_: CurrentUser = Depends(require_role("ceo")), db: Session = Depends(get_db)) -> Any:
    try:
        users = list(db.scalars(select(User).order_by(User.created_at.desc())).all())
        return users
    except Exception:
        logger.exception("list users failed")
        raise http_error(500, "Failed to fetch users", 500)


@router.post("/", response_model=UserOut)
def create_user(
    payload: UserCreate, _: CurrentUser = Depends(require_role("ceo")), db: Session = Depends(get_db)
) -> Any:
    try:
        role = payload.role
        if role not in ("employee", "ceo"):
            raise http_error(422, "Invalid role", 422)
        user = User(
            name=payload.name,
            username=payload.username,
            hashed_password=hash_password(payload.password),
            role=UserRole(role),
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        if hasattr(e, "status_code"):
            raise
        logger.exception("create user failed")
        raise http_error(500, "Failed to create user", 500)


@router.delete("/{user_id}")
def delete_user(
    user_id: UUID,
    _: CurrentUser = Depends(require_role("ceo")),
    db: Session = Depends(get_db),
) -> Any:
    try:
        res = db.execute(delete(User).where(User.id == user_id))
        if res.rowcount == 0:
            raise http_error(404, "User not found", 404)
        db.commit()
        return {"ok": True}
    except Exception as e:
        db.rollback()
        if hasattr(e, "status_code"):
            raise
        logger.exception("delete user failed")
        raise http_error(500, "Failed to delete user", 500)


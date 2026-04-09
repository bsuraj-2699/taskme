from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from core.config import settings
from core.database import get_db
from core.deps import CurrentUser, get_current_user
from core.errors import http_error
from core.security import (
    TokenPayloadError,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

limiter = Limiter(key_func=get_remote_address)


class LoginIn(BaseModel):
    username: str
    password: str


class LoginOut(BaseModel):
    access_token: str
    refresh_token: str
    role: str
    user_id: UUID
    name: str


class RefreshIn(BaseModel):
    refresh_token: str


class RefreshOut(BaseModel):
    access_token: str


@router.post("/login", response_model=LoginOut)
@limiter.limit(settings.login_rate_limit)
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)) -> Any:
    try:
        user = db.scalar(select(User).where(User.username == payload.username))
        if not user or not user.is_active:
            raise http_error(401, "Invalid credentials", 401)

        if not verify_password(payload.password, user.hashed_password):
            raise http_error(401, "Invalid credentials", 401)

        access = create_access_token(user_id=user.id, role=user.role.value)
        refresh = create_refresh_token(user_id=user.id, role=user.role.value)
        return {
            "access_token": access,
            "refresh_token": refresh,
            "role": user.role.value,
            "user_id": user.id,
            "name": user.name,
        }
    except Exception as e:
        if hasattr(e, "status_code"):
            raise
        logger.exception("login failed")
        raise http_error(500, "Login failed", 500)


@router.post("/refresh", response_model=RefreshOut)
def refresh(payload: RefreshIn) -> Any:
    try:
        decoded = decode_token(payload.refresh_token)
        if decoded.get("type") != "refresh":
            raise http_error(401, "Invalid refresh token", 401)

        user_id = UUID(str(decoded.get("sub")))
        role = decoded.get("role")
        if role not in ("ceo", "employee"):
            raise http_error(401, "Invalid refresh token", 401)

        access = create_access_token(user_id=user_id, role=role)
        return {"access_token": access}
    except TokenPayloadError:
        raise http_error(401, "Invalid refresh token", 401)
    except Exception as e:
        if hasattr(e, "status_code"):
            raise
        logger.exception("refresh failed")
        raise http_error(500, "Refresh failed", 500)


@router.post("/logout")
def logout(user: CurrentUser = Depends(get_current_user)) -> Any:
    # Stateless JWT: client discards tokens; endpoint exists for symmetry.
    return {"ok": True}


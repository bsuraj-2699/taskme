from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Literal
from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.security import TokenPayloadError, decode_token

security = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    id: UUID
    role: Literal["ceo", "employee"]


def _unauthorized(message: str = "Not authenticated") -> HTTPException:
    return HTTPException(status_code=401, detail={"error": True, "message": message, "code": 401})


def _forbidden(message: str = "Forbidden") -> HTTPException:
    return HTTPException(status_code=403, detail={"error": True, "message": message, "code": 403})


def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> CurrentUser:
    if creds is None or not creds.credentials:
        raise _unauthorized()

    try:
        payload = decode_token(creds.credentials)
    except TokenPayloadError:
        raise _unauthorized("Invalid token")

    if payload.get("type") != "access":
        raise _unauthorized("Invalid token type")

    try:
        user_id = UUID(str(payload.get("sub")))
    except Exception:
        raise _unauthorized("Invalid subject")

    role = payload.get("role")
    if role not in ("ceo", "employee"):
        raise _unauthorized("Invalid role")

    return CurrentUser(id=user_id, role=role)


def require_role(required: Literal["ceo", "employee"]):
    def _dep(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        if user.role != required:
            raise _forbidden()
        return user

    return _dep


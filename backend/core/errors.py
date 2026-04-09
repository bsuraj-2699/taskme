from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException

logger = logging.getLogger("taskme.api")


def http_error(status_code: int, message: str, code: int | None = None) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"error": True, "message": message, "code": code if code is not None else status_code},
    )


def unexpected_error(message: str = "Unexpected error") -> dict[str, Any]:
    return {"error": True, "message": message, "code": 500}


from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler

from core.config import settings


def setup_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    os.makedirs(settings.log_dir, exist_ok=True)

    fmt = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    root = logging.getLogger()
    root.setLevel(level)

    # Avoid duplicate handlers on reload.
    if root.handlers:
        return

    file_handler = RotatingFileHandler(
        filename=os.path.join(settings.log_dir, "taskme.log"),
        maxBytes=5_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)
    file_handler.setLevel(level)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)
    stream_handler.setLevel(level)

    root.addHandler(file_handler)
    root.addHandler(stream_handler)

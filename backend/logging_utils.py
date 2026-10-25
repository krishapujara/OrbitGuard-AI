"""Structured logging to a local file. UI must not receive stack traces."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from config.settings import get_settings

_LOGGER: logging.Logger | None = None


def get_logger() -> logging.Logger:
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER
    settings = get_settings()
    logger = logging.getLogger("orbitalguard")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        path = settings.logs_dir / "orbitalguard.log"
        handler = RotatingFileHandler(path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    _LOGGER = logger
    return logger


def log_event(level: str, event: str, **fields: Any) -> None:
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **{k: _safe(v) for k, v in fields.items()},
    }
    logger = get_logger()
    message = json.dumps(payload, default=str)
    getattr(logger, level.lower(), logger.info)(message)


def _safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    text = str(value)
    lowered = text.lower()
    if any(token in lowered for token in ("api_key", "secret", "password", "token=")):
        return "[redacted]"
    return value

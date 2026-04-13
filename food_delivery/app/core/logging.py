from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings

APP_LOGGER_NAME = "food_delivery"


class JsonFormatter(logging.Formatter):
    _reserved = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "message",
        "asctime",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "logger": record.name,
            "extra": {},
        }

        for key, value in record.__dict__.items():
            if key not in self._reserved:
                payload["extra"][key] = value

        if record.exc_info:
            payload["extra"]["exc_info"] = self.formatException(record.exc_info)

        if not payload["extra"]:
            payload["extra"] = {}

        return json.dumps(payload, ensure_ascii=False, default=str)


def setup_logging() -> None:
    level = logging.DEBUG if settings.debug else logging.INFO

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)

    app_logger = logging.getLogger(APP_LOGGER_NAME)
    app_logger.setLevel(level)
    app_logger.propagate = True


def get_logger(name: str) -> logging.Logger:
    if not name:
        return logging.getLogger(APP_LOGGER_NAME)
    if name == APP_LOGGER_NAME or name.startswith(f"{APP_LOGGER_NAME}."):
        return logging.getLogger(name)
    return logging.getLogger(f"{APP_LOGGER_NAME}.{name}")

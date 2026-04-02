# -*- coding: utf-8 -*-
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_LOGGER_CONFIGURED = False


def _resolve_level(environment: str, configured_level: str) -> int:
    if configured_level:
        return getattr(logging, configured_level.upper(), logging.INFO)
    if environment.lower() == "development":
        return logging.DEBUG
    return logging.INFO


def setup_logging(environment: str, configured_level: str = "") -> None:
    global _LOGGER_CONFIGURED
    if _LOGGER_CONFIGURED:
        return

    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(_resolve_level(environment, configured_level))
    root_logger.handlers.clear()

    formatter = logging.Formatter(_LOG_FORMAT)

    file_handler = RotatingFileHandler(
        logs_dir / "app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    _LOGGER_CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

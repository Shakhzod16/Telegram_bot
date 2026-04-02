# -*- coding: utf-8 -*-
from utils.i18n import get_frontend_texts, get_text

LANGUAGE_CODES = ("uz", "ru", "en")

STATUS_TEXT_KEYS = {
    "CREATED": "status_created",
    "PENDING": "status_created",
    "CONFIRMED": "status_confirmed",
    "PREPARING": "status_in_progress",
    "IN_PROGRESS": "status_in_progress",
    "DELIVERING": "status_delivering",
    "DELIVERED": "status_delivered",
    "PAID": "status_paid",
    "CANCELLED": "status_cancelled",
}


def t(key: str, language: str, **kwargs: str) -> str:
    return get_text(key, language, **kwargs)


def status_text(status: str, language: str) -> str:
    key = STATUS_TEXT_KEYS.get((status or "").upper(), "status_unknown")
    return t(key, language)


def frontend_texts(language: str) -> dict[str, str]:
    return get_frontend_texts(language)

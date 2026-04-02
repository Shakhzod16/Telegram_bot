# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

SUPPORTED_LANGUAGES = ("uz", "ru", "en")
DEFAULT_LANGUAGE = "en"
LOCALES_DIR = Path(__file__).resolve().parent.parent / "bot" / "locales"

_LOCALE_CACHE: dict[str, dict[str, str]] = {}


def _normalize_lang(language: str | None) -> str:
    lang = (language or "").strip().lower()
    if lang not in SUPPORTED_LANGUAGES:
        return DEFAULT_LANGUAGE
    return lang


def load_locale(language: str) -> dict[str, str]:
    lang = _normalize_lang(language)
    cached = _LOCALE_CACHE.get(lang)
    if cached is not None:
        return cached

    target = LOCALES_DIR / f"{lang}.json"
    if not target.exists():
        _LOCALE_CACHE[lang] = {}
        return _LOCALE_CACHE[lang]

    with target.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    _LOCALE_CACHE[lang] = {str(key): str(value) for key, value in payload.items()}
    return _LOCALE_CACHE[lang]


def get_text(key: str, language: str, **kwargs: str) -> str:
    lang = _normalize_lang(language)
    locale = load_locale(lang)
    template = locale.get(key)
    if template is None and lang != DEFAULT_LANGUAGE:
        template = load_locale(DEFAULT_LANGUAGE).get(key)
    if template is None:
        template = key
    try:
        return template.format(**kwargs)
    except Exception:
        return template


def get_frontend_texts(language: str) -> dict[str, str]:
    lang = _normalize_lang(language)
    keys = set(load_locale(lang).keys()) | set(load_locale(DEFAULT_LANGUAGE).keys())
    return {key: get_text(key, lang) for key in keys if key.startswith("frontend_")}

# -*- coding: utf-8 -*-
from telegram import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

from config import settings
from utils.texts import LANGUAGE_CODES, t

LANGUAGE_BUTTONS: dict[str, str] = {}
for _lang in LANGUAGE_CODES:
    LANGUAGE_BUTTONS[t("language_uz", _lang)] = "uz"
    LANGUAGE_BUTTONS[t("language_ru", _lang)] = "ru"
    LANGUAGE_BUTTONS[t("language_en", _lang)] = "en"


def language_keyboard(language: str = "en") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [t("language_uz", language)],
            [t("language_ru", language)],
            [t("language_en", language)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def phone_keyboard(language: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton(t("share_phone_button", language), request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def main_menu_keyboard(language: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(t("order_button", language), web_app=WebAppInfo(url=settings.web_app_url))],
            [KeyboardButton(t("history_button", language))],
            [KeyboardButton(t("change_language_button", language))],
        ],
        resize_keyboard=True,
    )

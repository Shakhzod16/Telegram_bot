from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    WebAppInfo,
)
from sqlalchemy import select

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.user import User
from bot.states.onboarding import OnboardingStates

router = Router()
logger = get_logger(__name__)
BASE_DIR = Path(__file__).resolve().parents[2]

SUPPORTED_LANGUAGES = {"uz", "ru", "en"}

I18N = {
    "uz": {
        "choose_language": "🌍 Tilni tanlang / Выберите язык / Choose language",
        "ask_phone": "📞 Telefon raqamingizni yuboring",
        "contact_button": "📱 Raqamni yuborish",
        "registered": "✅ Ro'yxatdan o'tdingiz!\nXush kelibsiz, {first_name}! 🎉",
        "welcome_back": "Xush kelibsiz, {first_name}! 🎉",
        "open_webapp": "🌐 WebApp ochish",
        "open_webapp_prompt": "WebApp orqali kirish:",
        "contact_owner_only": "Iltimos, faqat o'zingizning telefon raqamingizni yuboring.",
        "phone_invalid": "Telefon raqam formati noto'g'ri. Iltimos, qaytadan yuboring.",
    },
    "ru": {
        "choose_language": "🌍 Tilni tanlang / Выберите язык / Choose language",
        "ask_phone": "📞 Отправьте ваш номер телефона",
        "contact_button": "📱 Отправить номер",
        "registered": "✅ Вы зарегистрированы!\nДобро пожаловать, {first_name}! 🎉",
        "welcome_back": "Добро пожаловать, {first_name}! 🎉",
        "open_webapp": "🌐 Открыть WebApp",
        "open_webapp_prompt": "Вход через WebApp:",
        "contact_owner_only": "Пожалуйста, отправьте только ваш номер телефона.",
        "phone_invalid": "Неверный формат номера. Отправьте контакт еще раз.",
    },
    "en": {
        "choose_language": "🌍 Tilni tanlang / Выберите язык / Choose language",
        "ask_phone": "📞 Please share your phone number",
        "contact_button": "📱 Share number",
        "registered": "✅ You are registered!\nWelcome, {first_name}! 🎉",
        "welcome_back": "Welcome, {first_name}! 🎉",
        "open_webapp": "🌐 Open WebApp",
        "open_webapp_prompt": "Open WebApp:",
        "contact_owner_only": "Please share only your own phone number.",
        "phone_invalid": "Invalid phone format. Please share your contact again.",
    },
}


@dataclass(slots=True)
class UserContext:
    first_name: str
    language: str
    is_admin: bool
    is_superadmin: bool


def _safe_lang(value: str | None) -> str:
    lang = (value or "").strip().lower()
    return lang if lang in SUPPORTED_LANGUAGES else "uz"


def _t(lang: str, key: str) -> str:
    return I18N[_safe_lang(lang)][key]


def _normalize_webapp_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    try:
        parsed = urlsplit(raw)
    except Exception:
        return raw
    path = parsed.path or ""
    if path in {"", "/"}:
        path = "/webapp/"
    elif path.rstrip("/") == "/webapp":
        path = "/webapp/"
    normalized = parsed._replace(path=path, query="", fragment="")
    return urlunsplit(normalized)


def get_webapp_url() -> str:
    for path in ["runtime_webapp_url.txt", "logs/runtime_webapp_url.txt"]:
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as file:
                    url = file.read().strip()
            except OSError:
                continue
            if url.startswith("https://"):
                return _normalize_webapp_url(url)

    for path in [BASE_DIR / "runtime_webapp_url.txt", BASE_DIR / "logs" / "runtime_webapp_url.txt"]:
        if path.exists():
            try:
                url = path.read_text(encoding="utf-8").strip()
            except OSError:
                continue
            if url.startswith("https://"):
                return _normalize_webapp_url(url)

    return _normalize_webapp_url(str(getattr(settings, "WEBAPP_URL", "")).strip())


def _build_language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang_uz"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
            ]
        ]
    )


def _build_phone_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=_t(lang, "contact_button"),
                    request_contact=True,
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def _build_webapp_keyboard(lang: str, webapp_url: str) -> InlineKeyboardMarkup | None:
    if not webapp_url.lower().startswith("https://"):
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_t(lang, "open_webapp"),
                    web_app=WebAppInfo(url=webapp_url),
                )
            ]
        ]
    )


def _display_first_name(message: Message) -> str:
    if message.from_user and message.from_user.first_name:
        return message.from_user.first_name
    return "Friend"


def _normalize_uz_phone(phone_raw: str | None) -> str | None:
    digits = re.sub(r"\D+", "", phone_raw or "")
    if not digits:
        return None
    if digits.startswith("998") and len(digits) == 12:
        return f"+{digits}"
    if digits.startswith("0") and len(digits) == 10:
        return f"+998{digits[1:]}"
    if len(digits) == 9:
        return f"+998{digits}"
    return None


async def _load_existing_user(message: Message) -> UserContext | None:
    if not message.from_user:
        return None
    telegram_id = message.from_user.id
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.telegram_id == telegram_id))
            user = result.scalar_one_or_none()
            if user is None:
                return None

            changed = False
            first_name = message.from_user.first_name or ""
            if first_name != user.first_name:
                user.first_name = first_name
                changed = True

            if message.from_user.last_name != user.last_name:
                user.last_name = message.from_user.last_name
                changed = True

            if message.from_user.username != user.username:
                user.username = message.from_user.username
                changed = True

            if user.telegram_id in settings.admin_telegram_id_set and not user.is_admin:
                user.is_admin = True
                changed = True

            if user.telegram_id in settings.SUPERADMIN_TELEGRAM_IDS:
                if not user.is_superadmin or not user.is_admin:
                    user.is_superadmin = True
                    user.is_admin = True
                    changed = True

            if changed:
                await session.commit()
                await session.refresh(user)

            # Agar profilda telefon yo'q bo'lsa, onboarding qayta ishga tushadi.
            # Shu bilan eski user ham til+telefon bosqichidan o'ta oladi.
            if not (user.phone and str(user.phone).strip()):
                return None

            return UserContext(
                first_name=user.first_name or _display_first_name(message),
                language=_safe_lang(user.language),
                is_admin=bool(user.is_admin),
                is_superadmin=bool(user.is_superadmin),
            )
    except Exception:
        logger.exception("start_load_existing_user_failed", extra={"telegram_id": telegram_id})
        return None


async def _upsert_user_from_onboarding(message: Message, *, language: str, phone: str) -> UserContext:
    if not message.from_user:
        return UserContext(first_name="Friend", language="uz", is_admin=False, is_superadmin=False)

    telegram_id = message.from_user.id
    safe_lang = _safe_lang(language)
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.telegram_id == telegram_id))
            user = result.scalar_one_or_none()

            if user is None:
                user = User(
                    telegram_id=telegram_id,
                    first_name=message.from_user.first_name or "",
                    last_name=message.from_user.last_name,
                    username=message.from_user.username,
                    phone=phone,
                    language=safe_lang,
                    is_admin=telegram_id in settings.admin_telegram_id_set,
                    is_superadmin=telegram_id in settings.SUPERADMIN_TELEGRAM_IDS,
                )
                if user.is_superadmin:
                    user.is_admin = True
                session.add(user)
            else:
                user.first_name = message.from_user.first_name or user.first_name or ""
                user.last_name = message.from_user.last_name
                user.username = message.from_user.username
                user.language = safe_lang
                user.phone = phone
                if telegram_id in settings.admin_telegram_id_set:
                    user.is_admin = True
                if telegram_id in settings.SUPERADMIN_TELEGRAM_IDS:
                    user.is_superadmin = True
                    user.is_admin = True

            await session.commit()
            await session.refresh(user)
            return UserContext(
                first_name=user.first_name or _display_first_name(message),
                language=_safe_lang(user.language),
                is_admin=bool(user.is_admin),
                is_superadmin=bool(user.is_superadmin),
            )
    except Exception:
        logger.exception("start_upsert_user_failed", extra={"telegram_id": telegram_id})
        return UserContext(
            first_name=_display_first_name(message),
            language=safe_lang,
            is_admin=False,
            is_superadmin=False,
        )


async def _send_webapp_entry(message: Message, *, lang: str, first_name: str, is_registered: bool) -> None:
    text_key = "registered" if is_registered else "welcome_back"
    await message.answer(
        _t(lang, text_key).format(first_name=first_name),
        reply_markup=ReplyKeyboardRemove(),
    )

    webapp_url = get_webapp_url()
    web_button = _build_webapp_keyboard(lang, webapp_url)
    if web_button is None:
        logger.warning("webapp_url_not_https", extra={"webapp_url": webapp_url})
        return
    await message.answer(_t(lang, "open_webapp_prompt"), reply_markup=web_button)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    user = await _load_existing_user(message)
    if user is not None:
        await state.clear()
        await _send_webapp_entry(
            message,
            lang=user.language,
            first_name=user.first_name,
            is_registered=False,
        )
        return

    await state.clear()
    await message.answer(
        _t("uz", "choose_language"),
        reply_markup=_build_language_keyboard(),
    )
    await state.set_state(OnboardingStates.choosing_language)


@router.callback_query(F.data.startswith("lang_"), StateFilter(OnboardingStates.choosing_language))
async def onboarding_choose_language(callback: CallbackQuery, state: FSMContext) -> None:
    data = callback.data or ""
    lang = data.replace("lang_", "", 1).strip().lower()
    safe_lang = _safe_lang(lang)

    await state.update_data(language=safe_lang)
    if callback.message:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        await callback.message.answer(
            _t(safe_lang, "ask_phone"),
            reply_markup=_build_phone_keyboard(safe_lang),
        )
    await state.set_state(OnboardingStates.sharing_phone)
    await callback.answer()


@router.message(F.contact, StateFilter(OnboardingStates.sharing_phone))
async def onboarding_share_phone(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = _safe_lang(data.get("language"))

    if not message.from_user or not message.contact:
        await message.answer(_t(lang, "phone_invalid"), reply_markup=_build_phone_keyboard(lang))
        return

    if message.contact.user_id and message.contact.user_id != message.from_user.id:
        await message.answer(_t(lang, "contact_owner_only"), reply_markup=_build_phone_keyboard(lang))
        return

    normalized_phone = _normalize_uz_phone(message.contact.phone_number)
    if not normalized_phone:
        await message.answer(_t(lang, "phone_invalid"), reply_markup=_build_phone_keyboard(lang))
        return

    user = await _upsert_user_from_onboarding(
        message,
        language=lang,
        phone=normalized_phone,
    )
    await state.clear()
    await _send_webapp_entry(
        message,
        lang=user.language,
        first_name=user.first_name,
        is_registered=True,
    )


@router.message(StateFilter(OnboardingStates.sharing_phone))
async def onboarding_waiting_phone_fallback(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = _safe_lang(data.get("language"))
    await message.answer(
        _t(lang, "ask_phone"),
        reply_markup=_build_phone_keyboard(lang),
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
    await cmd_start(message, state)


@router.message(Command("contact"))
async def cmd_contact(message: Message) -> None:
    await message.answer("Aloqa: @foodexpress_support")

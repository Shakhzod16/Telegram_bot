from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from pathlib import Path

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.user import User

router = Router()
logger = get_logger(__name__)
BASE_DIR = Path(__file__).resolve().parents[2]


def get_webapp_url() -> str:
    # 1. runtime fayldan o'qi
    for path in ["runtime_webapp_url.txt", "logs/runtime_webapp_url.txt"]:
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as file:
                    url = file.read().strip()
            except OSError:
                continue
            if url.startswith("https://"):
                return url

    # Optional absolute-path fallback for service runs from another CWD.
    for path in [BASE_DIR / "runtime_webapp_url.txt", BASE_DIR / "logs" / "runtime_webapp_url.txt"]:
        if path.exists():
            try:
                url = path.read_text(encoding="utf-8").strip()
            except OSError:
                continue
            if url.startswith("https://"):
                return url

    # 2. env dan fallback
    return str(getattr(settings, "WEBAPP_URL", "")).strip()


def _is_https(url: str) -> bool:
    return url.lower().startswith("https://")


def _build_web_button(webapp_url: str) -> InlineKeyboardMarkup | None:
    if not _is_https(webapp_url):
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌐 WebApp ochish",
                    web_app=WebAppInfo(url=webapp_url),
                )
            ]
        ]
    )


def _full_name(first_name: str | None, last_name: str | None, username: str | None) -> str:
    parts = [part.strip() for part in (first_name or "", last_name or "") if part and part.strip()]
    if parts:
        return " ".join(parts)
    if username:
        return f"@{username}"
    return "Foydalanuvchi"


@dataclass(slots=True)
class UserContext:
    full_name: str
    is_admin: bool
    is_superadmin: bool


def _superadmin_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Adminlar"), KeyboardButton(text="📋 Whitelist")],
            [KeyboardButton(text="📊 Statistika")],
        ],
        resize_keyboard=True,
    )


def _admin_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Mahsulotlarim"), KeyboardButton(text="📁 Kategoriyalarim")],
            [KeyboardButton(text="📋 Buyurtmalar")],
            [KeyboardButton(text="👤 Profil")],
        ],
        resize_keyboard=True,
    )


def _user_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍 Katalog"), KeyboardButton(text="🛒 Savat")],
            [KeyboardButton(text="📦 Buyurtmalarim"), KeyboardButton(text="👤 Profil")],
        ],
        resize_keyboard=True,
    )


def _build_start_response(user: UserContext) -> tuple[str, ReplyKeyboardMarkup]:
    if user.is_superadmin:
        text = (
            "👑 Superadmin paneliga xush kelibsiz!\n\n"
            f"Salom, {user.full_name}!\n"
            "Siz barcha tizimni boshqara olasiz."
        )
        return text, _superadmin_keyboard()

    if user.is_admin:
        text = (
            "🛠 Admin paneliga xush kelibsiz!\n\n"
            f"Salom, {user.full_name}!\n"
            "Siz admin bo'limini boshqara olasiz."
        )
        return text, _admin_keyboard()

    text = (
        "Xush kelibsiz!\n\n"
        f"Salom, {user.full_name}!\n"
        "Asosiy bo'limlardan birini tanlang."
    )
    return text, _user_keyboard()


async def _ensure_user(message: Message) -> UserContext:
    tid = message.from_user.id if message.from_user else 0
    fallback_name = _full_name(
        message.from_user.first_name if message.from_user else None,
        message.from_user.last_name if message.from_user else None,
        message.from_user.username if message.from_user else None,
    )
    try:
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select

            result = await session.execute(select(User).where(User.telegram_id == tid))
            user = result.scalar_one_or_none()
            changed = False
            if user is None:
                user = User(
                    telegram_id=tid,
                    first_name=message.from_user.first_name if message.from_user else "",
                    last_name=message.from_user.last_name if message.from_user else None,
                    username=message.from_user.username if message.from_user else None,
                    language="uz",
                    is_admin=tid in settings.admin_telegram_id_set,
                )
                session.add(user)
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
            return UserContext(
                full_name=_full_name(user.first_name, user.last_name, user.username),
                is_admin=bool(user.is_admin),
                is_superadmin=bool(user.is_superadmin),
            )
    except Exception:
        logger.exception("start_handler_db_error", extra={"telegram_id": tid})
    return UserContext(full_name=fallback_name, is_admin=False, is_superadmin=False)


async def _reply_with_menu(message: Message, *, user_context: UserContext) -> None:
    webapp_url = get_webapp_url()
    logging.info(f"WebApp URL: {get_webapp_url()}")
    text, reply_markup = _build_start_response(user_context)
    await message.answer(
        text,
        reply_markup=reply_markup,
    )

    web_button = _build_web_button(webapp_url)
    if web_button is not None:
        await message.answer(
            "WebApp orqali kirish:",
            reply_markup=web_button,
        )
    else:
        logger.warning("webapp_url_not_https", extra={"webapp_url": webapp_url})


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    user_context = await _ensure_user(message)
    await _reply_with_menu(message, user_context=user_context)


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    user_context = await _ensure_user(message)
    await _reply_with_menu(message, user_context=user_context)


@router.message(Command("contact"))
async def cmd_contact(message: Message) -> None:
    await message.answer("Aloqa: @foodexpress_support")

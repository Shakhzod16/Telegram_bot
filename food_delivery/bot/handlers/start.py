from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, WebAppInfo

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.user import User

router = Router()
logger = get_logger(__name__)
BASE_DIR = Path(__file__).resolve().parents[2]


def _runtime_webapp_url() -> str | None:
    candidate_paths = (
        BASE_DIR / "runtime_webapp_url.txt",
        BASE_DIR / "logs" / "runtime_webapp_url.txt",
        Path("runtime_webapp_url.txt"),
        Path("logs/runtime_webapp_url.txt"),
    )
    for path in candidate_paths:
        try:
            value = path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        parsed = urlsplit(value)
        if value and parsed.scheme.lower() == "https" and parsed.netloc:
            return value
    return None


def _webapp_url() -> str:
    raw = (_runtime_webapp_url() or settings.WEBAPP_URL).strip()
    if not raw:
        raw = settings.BACKEND_URL.strip()

    parsed = urlsplit(raw)
    path = parsed.path or ""
    if path in {"", "/"}:
        path = "/webapp/"
    elif not path.endswith("/"):
        path = f"{path}/"

    return urlunsplit((parsed.scheme, parsed.netloc, path, parsed.query, parsed.fragment))


def _is_https(url: str) -> bool:
    return url.lower().startswith("https://")


def _build_webapp_button(webapp_url: str) -> KeyboardButton:
    if _is_https(webapp_url):
        return KeyboardButton(text="🌐 WebApp", web_app=WebAppInfo(url=webapp_url))
    return KeyboardButton(text="🌐 WebApp")


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


def _superadmin_keyboard(webapp_url: str) -> ReplyKeyboardMarkup:
    superadmin_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Adminlar"), KeyboardButton(text="📋 Whitelist")],
            [KeyboardButton(text="📊 Statistika"), _build_webapp_button(webapp_url)],
        ],
        resize_keyboard=True,
    )
    return superadmin_kb


def _admin_keyboard(webapp_url: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Mahsulotlarim"), KeyboardButton(text="📁 Kategoriyalarim")],
            [KeyboardButton(text="📋 Buyurtmalar"), _build_webapp_button(webapp_url)],
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


def _build_start_response(user: UserContext, webapp_url: str) -> tuple[str, ReplyKeyboardMarkup]:
    if user.is_superadmin:
        text = (
            "👑 Superadmin paneliga xush kelibsiz!\n\n"
            f"Salom, {user.full_name}!\n"
            "Siz barcha tizimni boshqara olasiz."
        )
        return text, _superadmin_keyboard(webapp_url)

    if user.is_admin:
        text = (
            "🛠 Admin paneliga xush kelibsiz!\n\n"
            f"Salom, {user.full_name}!\n"
            "Siz admin bo'limini boshqara olasiz."
        )
        return text, _admin_keyboard(webapp_url)

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
    webapp_url = _webapp_url()
    text, reply_markup = _build_start_response(user_context, webapp_url)
    await message.answer(
        text,
        reply_markup=reply_markup,
    )


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

from __future__ import annotations

import logging

import httpx
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()
logger = logging.getLogger(__name__)
BACKEND = "http://localhost:8000/api/v1"


@router.message(Command("start"), F.chat.type.in_({"group", "supergroup"}))
async def log_group_start(message: Message) -> None:
    """Group /start command handler for chat id discovery in logs."""
    chat_id = message.chat.id
    chat_type = message.chat.type
    chat_title = message.chat.title or "—"
    logger.info(
        "group_start_detected chat_id=%s chat_type=%s chat_title=%s",
        chat_id,
        chat_type,
        chat_title,
    )


@router.message(Command("get_group_id"))
async def get_group_id(message: Message) -> None:
    """Guruh ID sini olish"""
    chat_id = message.chat.id
    chat_type = message.chat.type
    chat_title = message.chat.title or "—"
    logger.info(
        "group_id_request chat_id=%s chat_type=%s chat_title=%s",
        chat_id,
        chat_type,
        chat_title,
    )
    await message.answer(
        f"📋 Chat ma'lumotlari:\n"
        f"ID: <code>{chat_id}</code>\n"
        f"Turi: {chat_type}\n"
        f"Nomi: {chat_title}\n\n"
        f".env ga qo'shing:\n"
        f"<code>DEFAULT_GROUP_CHAT_ID={chat_id}</code>",
        parse_mode="HTML",
    )


@router.message(F.text == "⚙️ Sozlamalar")
async def admin_settings_menu(message: Message) -> None:
    telegram_id = message.from_user.id
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND}/admin/settings",
                headers={"X-Telegram-Id": str(telegram_id)},
            )
        data = resp.json()
        if data.get("has_group"):
            status = f"✅ Ulangan\nID: <code>{data['group_chat_id']}</code>"
        else:
            status = "❌ Ulanmagan"
    except Exception:
        status = "❌ Ma'lumot olishda xatolik"

    await message.answer(
        f"⚙️ <b>Admin Sozlamalari</b>\n\n"
        f"📱 Buyurtmalar guruhi:\n{status}\n\n"
        f"Guruh ulash:\n"
        f"1) Botni guruhga admin qilib qo'shing\n"
        f"2) /link_group yozing\n\n"
        f"Uzish: /unlink_group",
        parse_mode="HTML",
    )

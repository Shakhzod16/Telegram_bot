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


@router.message(Command("link_group"))
async def link_group(message: Message) -> None:
    """Adminni shu guruhga bog'lash."""
    if message.chat.type not in {"group", "supergroup"}:
        await message.answer("❌ /link_group ni guruh ichida yuboring.")
        return

    telegram_id = message.from_user.id if message.from_user else 0
    group_chat_id = message.chat.id
    group_title = message.chat.title or "—"

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BACKEND}/admin/settings/group",
                headers={"X-Telegram-Id": str(telegram_id)},
                json={"group_chat_id": group_chat_id},
            )

        if resp.status_code == 200:
            await message.answer(
                f"✅ Guruh muvaffaqiyatli ulandi!\n\n"
                f"Nomi: {group_title}\n"
                f"ID: <code>{group_chat_id}</code>",
                parse_mode="HTML",
            )
        elif resp.status_code == 403:
            await message.answer("❌ Bu amal faqat admin uchun ruxsat etilgan.")
        else:
            await message.answer(f"❌ Xatolik: {resp.text}")
    except Exception as exc:  # noqa: BLE001
        logger.error("link_group_error: %s", exc)
        await message.answer("❌ Guruhni ulashda server xatoligi.")


@router.message(Command("unlink_group"))
async def unlink_group(message: Message) -> None:
    """Adminning bog'langan guruhini uzish."""
    telegram_id = message.from_user.id if message.from_user else 0
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{BACKEND}/admin/settings/group",
                headers={"X-Telegram-Id": str(telegram_id)},
            )

        if resp.status_code == 200:
            await message.answer("✅ Buyurtmalar guruhi uzildi.")
        elif resp.status_code == 403:
            await message.answer("❌ Bu amal faqat admin uchun ruxsat etilgan.")
        else:
            await message.answer(f"❌ Xatolik: {resp.text}")
    except Exception as exc:  # noqa: BLE001
        logger.error("unlink_group_error: %s", exc)
        await message.answer("❌ Guruhni uzishda server xatoligi.")


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

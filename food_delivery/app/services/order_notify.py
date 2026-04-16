from __future__ import annotations

import logging
from datetime import datetime
from html import escape
from typing import Optional

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.order import Order
from app.models.user import User

logger = logging.getLogger(__name__)


def _user_full_name(user: User | None) -> str:
    if not user:
        return "Noma'lum"
    parts = [part.strip() for part in ((user.first_name or ""), (user.last_name or "")) if part and part.strip()]
    if parts:
        return " ".join(parts)
    if user.username:
        return f"@{user.username}"
    return "Noma'lum"


def _order_address_text(order: Order) -> str:
    manual_text = getattr(order, "delivery_address_text", None)
    if manual_text:
        return str(manual_text)

    lat = getattr(order, "latitude", None)
    lon = getattr(order, "longitude", None)
    if lat is not None and lon is not None:
        return f"{float(lat):.6f}, {float(lon):.6f}"

    return "—"


async def get_target_group(order: Order, db: AsyncSession) -> Optional[int]:
    """
    Buyurtma yuborilishi kerak bo'lgan guruhni aniqlaydi.
    1. Admin guruh (owner_id bo'yicha)
    2. Birinchi admin guruh
    3. DEFAULT_GROUP_CHAT_ID (.env dan)
    """
    # 1. Order ga tegishli admin guruhini top
    if hasattr(order, "owner_id") and getattr(order, "owner_id", None):
        admin_result = await db.execute(
            select(User).where(
                User.id == order.owner_id,
                User.group_chat_id.isnot(None),
            )
        )
        admin = admin_result.scalar_one_or_none()
        if admin and admin.group_chat_id:
            return int(admin.group_chat_id)

    # 2. Istalgan admin guruhini top
    admin_result = await db.execute(
        select(User)
        .where(
            User.is_admin.is_(True),
            User.group_chat_id.isnot(None),
        )
        .limit(1)
    )
    admin = admin_result.scalar_one_or_none()
    if admin and admin.group_chat_id:
        return int(admin.group_chat_id)

    # 3. Default guruh (.env dan)
    if settings.DEFAULT_GROUP_CHAT_ID:
        return int(settings.DEFAULT_GROUP_CHAT_ID)

    return None


async def notify_admin_group(order_id: int, db: AsyncSession, bot: Bot) -> None:
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items),
            selectinload(Order.user),
        )
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        return

    user_result = await db.execute(select(User).where(User.id == order.user_id))
    user = user_result.scalar_one_or_none()

    group_chat_id = await get_target_group(order, db)
    if not group_chat_id:
        logger.warning("Guruh topilmadi! Order #%s", order_id)
        return

    items_text = ""
    total = getattr(order, "total_price", None)
    if total is None:
        total = getattr(order, "total_amount", 0) or 0

    if hasattr(order, "items") and order.items:
        for item in order.items:
            snapshot = getattr(item, "snapshot_json", {}) or {}
            name = (
                getattr(item, "product_name", None)
                or snapshot.get("product_name_uz")
                or snapshot.get("product_name")
                or getattr(item, "name", "Mahsulot")
            )
            qty = getattr(item, "quantity", 1)
            price = getattr(item, "total_price", 0) or 0
            items_text += f"  • {name} x{qty} — {int(price):,} so'm\n"

    order_address = _order_address_text(order)
    order_note = getattr(order, "note", None) or getattr(order, "comment", None) or ""
    user_name = _user_full_name(user or getattr(order, "user", None))
    user_phone = (user.phone if user else None) or "—"
    lat = getattr(order, "latitude", None)
    lon = getattr(order, "longitude", None)
    maps_url = getattr(order, "maps_url", None)
    if not maps_url and lat is not None and lon is not None:
        maps_url = f"https://maps.google.com/?q={lat},{lon}"

    text = (
        f"🛍 <b>YANGI BUYURTMA #{order.id}</b>\n\n"
        f"👤 Mijoz: <b>{user_name}</b>\n"
        f"📱 Telefon: {user_phone}\n"
        f"📍 Manzil: {order_address}\n"
    )
    if order_note:
        text += f"📝 Izoh: {order_note}\n"
    if maps_url:
        text += f"🗺 <a href='{escape(maps_url, quote=True)}'>Xaritada ko'rish</a>\n"
    text += (
        f"\n🧾 <b>Tarkib:</b>\n{items_text or '  • Mahsulotlar topilmadi'}\n"
        f"💰 Jami: <b>{int(total):,} so'm</b>\n"
        f"🕐 Vaqt: {datetime.now().strftime('%H:%M')}"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Qabul qildim", callback_data=f"order_accept:{order.id}")],
            [InlineKeyboardButton(text="❌ Rad etish", callback_data=f"order_reject:{order.id}")],
        ]
    )

    try:
        await bot.send_message(
            chat_id=group_chat_id,
            text=text,
            parse_mode="HTML",
            reply_markup=kb,
        )
        if lat is not None and lon is not None:
            try:
                await bot.send_location(
                    chat_id=group_chat_id,
                    latitude=float(lat),
                    longitude=float(lon),
                )
            except Exception as exc:
                logger.error("Lokatsiya pin xato: %s", exc)
        logger.info("Order #%s guruhga yuborildi: %s", order_id, group_chat_id)
    except Exception as exc:
        logger.error("Guruhga yuborishda xato: %s", exc)


async def notify_user_delivered(order_id: int, db: AsyncSession, bot: Bot) -> None:
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        return

    user_result = await db.execute(select(User).where(User.id == order.user_id))
    user = user_result.scalar_one_or_none()
    if not user or not user.telegram_id:
        return

    try:
        await bot.send_message(
            chat_id=user.telegram_id,
            text=(
                "✅ <b>Buyurtmangiz yetkazildi!</b>\n\n"
                f"Buyurtma #{order_id} muvaffaqiyatli yetkazildi.\n"
                "Xarid uchun rahmat! 🙏"
            ),
            parse_mode="HTML",
        )
    except Exception as exc:
        logger.error("User notify xato: %s", exc)

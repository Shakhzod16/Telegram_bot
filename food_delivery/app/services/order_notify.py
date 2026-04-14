from __future__ import annotations

import logging
from datetime import datetime
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
    address = getattr(order, "address", None)
    if isinstance(address, str):
        return address
    if not address:
        return "—"

    parts: list[str] = []
    address_line = getattr(address, "address_line", None)
    if address_line:
        parts.append(str(address_line))
    apartment = getattr(address, "apartment", None)
    if apartment:
        parts.append(f"kv. {apartment}")
    floor = getattr(address, "floor", None)
    if floor:
        parts.append(f"{floor}-qavat")
    entrance = getattr(address, "entrance", None)
    if entrance:
        parts.append(f"{entrance}-kirish")
    landmark = getattr(address, "landmark", None)
    if landmark:
        parts.append(f"Mo'ljal: {landmark}")

    return ", ".join(parts) if parts else "—"


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
            selectinload(Order.address),
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

    text = (
        f"🛍 <b>YANGI BUYURTMA #{order.id}</b>\n\n"
        f"👤 Mijoz: <b>{user_name}</b>\n"
        f"📱 Telefon: {user_phone}\n"
        f"📍 Manzil: {order_address}\n"
    )
    if order_note:
        text += f"📝 Izoh: {order_note}\n"
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

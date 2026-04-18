from __future__ import annotations

from datetime import datetime
import logging

import httpx
from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import async_session
from app.models.order import Order

router = Router()
logger = logging.getLogger(__name__)
BACKEND = "http://localhost:8000/api/v1"


def _extract_accept_order_id(raw_data: str) -> int | None:
    try:
        if raw_data.startswith("order_accept:"):
            return int(raw_data.split(":", 1)[1])
        if raw_data.startswith("courier_accept_"):
            return int(raw_data.rsplit("_", 1)[1])
    except (TypeError, ValueError):
        return None
    return None


async def _get_order_contact_data(order_id: int) -> tuple[str | None, str | None]:
    async with async_session() as db:
        result = await db.execute(
            select(Order)
            .options(selectinload(Order.user))
            .where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            return None, None

        phone = None
        if order.user and order.user.phone:
            phone = str(order.user.phone).strip()

        maps_url = (order.maps_url or "").strip() or None
        if not maps_url and order.latitude is not None and order.longitude is not None:
            maps_url = f"https://maps.google.com/?q={order.latitude},{order.longitude}"

        return phone, maps_url


def _build_in_progress_keyboard(order_id: int, maps_url: str | None) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text="✅ Tugatdim (Yetkazildi)",
                callback_data=f"order_complete:{order_id}",
            )
        ]
    ]

    second_row: list[InlineKeyboardButton] = []
    if maps_url:
        second_row.append(InlineKeyboardButton(text="🗺 Xaritada ko'r", url=maps_url))
    else:
        second_row.append(
            InlineKeyboardButton(
                text="🗺 Xaritada ko'r",
                callback_data=f"order_map_missing:{order_id}",
            )
        )

    second_row.append(
        InlineKeyboardButton(
            text="📞 Mijoz bilan bog'lanish",
            callback_data=f"order_contact:{order_id}",
        )
    )
    rows.append(second_row)

    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data.startswith("courier_accept_"))
@router.callback_query(F.data.startswith("order_accept:"))
async def order_accept(callback: CallbackQuery) -> None:
    raw_data = callback.data or ""
    order_id = _extract_accept_order_id(raw_data)
    if order_id is None:
        await callback.answer("❌ Buyurtma ID topilmadi", show_alert=True)
        return

    courier_name = callback.from_user.full_name
    courier_id = callback.from_user.id

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"{BACKEND}/orders/{order_id}/status",
                json={
                    "status": "in_progress",
                    "courier_id": courier_id,
                    "courier_name": courier_name,
                },
            )

        if resp.status_code == 200:
            _phone, maps_url = await _get_order_contact_data(order_id)
            new_kb = _build_in_progress_keyboard(order_id, maps_url)

            original_text = callback.message.text if callback.message else ""
            new_text = (
                original_text
                + f"\n\n{'─' * 25}\n"
                + f"🚴 <b>Kuryer:</b> {courier_name}\n"
                + "⏳ <b>Status:</b> Yo'lda\n"
                + f"🕐 {datetime.now().strftime('%H:%M')}"
            )

            if callback.message:
                await callback.message.edit_text(
                    new_text,
                    parse_mode="HTML",
                    reply_markup=new_kb,
                )
            await callback.answer("✅ Qabul qilindi!", show_alert=True)
        else:
            await callback.answer(f"❌ Xatolik: {resp.status_code}", show_alert=True)
    except Exception as exc:
        logger.error("order_accept: %s", exc)
        await callback.answer("❌ Server xatolik", show_alert=True)


@router.callback_query(F.data.startswith("order_contact:"))
async def show_customer_phone(callback: CallbackQuery) -> None:
    try:
        order_id = int((callback.data or "").split(":", 1)[1])
    except (TypeError, ValueError, IndexError):
        await callback.answer("❌ Buyurtma ID xato", show_alert=True)
        return

    try:
        phone, _maps_url = await _get_order_contact_data(order_id)
        if phone:
            await callback.answer(f"📞 Mijoz raqami: {phone}", show_alert=True)
        else:
            await callback.answer("❌ Mijozning telefon raqami yo'q", show_alert=True)
    except Exception as exc:
        logger.error("show_customer_phone: %s", exc)
        await callback.answer("❌ Server xatolik", show_alert=True)


@router.callback_query(F.data.startswith("order_map_missing:"))
async def map_missing(callback: CallbackQuery) -> None:
    await callback.answer("❌ Xarita havolasi topilmadi", show_alert=True)


@router.callback_query(F.data.startswith("order_complete:"))
async def order_complete(callback: CallbackQuery) -> None:
    order_id = int((callback.data or "").split(":")[1])

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"{BACKEND}/orders/{order_id}/status",
                json={"status": "delivered"},
            )

        if resp.status_code == 200:
            original_text = callback.message.text if callback.message else ""
            base_text = original_text.split("─")[0].strip()
            new_text = (
                base_text + f"\n\n{'─' * 25}\n" + "✅ <b>YETKAZILDI!</b>\n" + f"🕐 {datetime.now().strftime('%H:%M')}"
            )
            if callback.message:
                await callback.message.edit_text(
                    new_text,
                    parse_mode="HTML",
                    reply_markup=None,
                )
            await callback.answer("✅ Yakunlandi!", show_alert=True)

            # Userni xabardor qil
            try:
                from app.core.bot_instance import bot
                from app.services.order_notify import notify_user_delivered

                async with async_session() as db:
                    await notify_user_delivered(order_id, db, bot)
            except Exception as exc:
                logger.error("User notify xato: %s", exc)
        else:
            await callback.answer("❌ Xatolik", show_alert=True)

    except Exception as exc:
        logger.error("order_complete: %s", exc)
        await callback.answer("❌ Server xatolik", show_alert=True)


@router.callback_query(F.data.startswith("order_reject:"))
async def order_reject(callback: CallbackQuery) -> None:
    order_id = int((callback.data or "").split(":")[1])

    try:
        async with httpx.AsyncClient() as client:
            await client.patch(
                f"{BACKEND}/orders/{order_id}/status",
                json={"status": "cancelled"},
            )

        original_text = callback.message.text if callback.message else ""
        new_text = (
            original_text
            + f"\n\n{'─' * 25}\n"
            + "❌ <b>RAD ETILDI</b>\n"
            + f"🕐 {datetime.now().strftime('%H:%M')}"
        )
        if callback.message:
            await callback.message.edit_text(
                new_text,
                parse_mode="HTML",
                reply_markup=None,
            )
        await callback.answer("Rad etildi")

        # Userni xabardor qil
        try:
            async with httpx.AsyncClient() as client:
                order_resp = await client.get(f"{BACKEND}/orders/{order_id}")
            if order_resp.status_code == 200:
                order = order_resp.json()
                tg_id = order.get("user_telegram_id")
                if tg_id:
                    from app.core.bot_instance import bot

                    await bot.send_message(
                        chat_id=tg_id,
                        text=(
                            f"❌ <b>Buyurtmangiz #{order_id} rad etildi.</b>\n\n"
                            "Boshqa mahsulot tanlashingiz mumkin."
                        ),
                        parse_mode="HTML",
                    )
        except Exception as exc:
            logger.error("Rad etish notify: %s", exc)

    except Exception as exc:
        logger.error("order_reject: %s", exc)
        await callback.answer("❌ Xatolik", show_alert=True)

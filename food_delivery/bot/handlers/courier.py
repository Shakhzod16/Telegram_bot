from __future__ import annotations

from datetime import datetime
import logging

import httpx
from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

router = Router()
logger = logging.getLogger(__name__)
BACKEND = "http://localhost:8000/api/v1"


@router.callback_query(F.data.startswith("order_accept:"))
async def order_accept(callback: CallbackQuery) -> None:
    order_id = int((callback.data or "").split(":")[1])
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
            new_kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✅ Tugatdim (Yetkazildi)",
                            callback_data=f"order_complete:{order_id}",
                        )
                    ]
                ]
            )
            original_text = callback.message.text or ""
            new_text = (
                original_text
                + f"\n\n{'─' * 25}\n"
                + f"🚴 <b>Kuryer:</b> {courier_name}\n"
                + "⏳ <b>Status:</b> Yo'lda\n"
                + f"🕐 {datetime.now().strftime('%H:%M')}"
            )
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
            original_text = callback.message.text or ""
            base_text = original_text.split("─")[0].strip()
            new_text = (
                base_text + f"\n\n{'─' * 25}\n" + "✅ <b>YETKAZILDI!</b>\n" + f"🕐 {datetime.now().strftime('%H:%M')}"
            )
            await callback.message.edit_text(
                new_text,
                parse_mode="HTML",
                reply_markup=None,
            )
            await callback.answer("✅ Yakunlandi!", show_alert=True)

            # Userni xabardor qil
            try:
                from app.core.bot_instance import bot
                from app.db.session import async_session
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

        original_text = callback.message.text or ""
        new_text = (
            original_text
            + f"\n\n{'─' * 25}\n"
            + "❌ <b>RAD ETILDI</b>\n"
            + f"🕐 {datetime.now().strftime('%H:%M')}"
        )
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

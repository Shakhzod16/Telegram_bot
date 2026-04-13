from __future__ import annotations

from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery

router = Router()


@router.callback_query(F.data.startswith("courier_accept_"))
async def courier_accept_order(callback: CallbackQuery) -> None:
    data = callback.data or ""
    if not data.startswith("courier_accept_"):
        await callback.answer()
        return

    order_id_raw = data.split("_")[-1]
    try:
        order_id = int(order_id_raw)
    except ValueError:
        await callback.answer("Noto'g'ri buyurtma ID", show_alert=True)
        return

    courier_name = (callback.from_user.first_name or "Kuryer").strip()

    message = callback.message
    if message is not None:
        original_text = getattr(message, "html_text", None) or message.text or message.caption or ""
        accepted_time = datetime.now().strftime("%H:%M")
        new_text = (
            f"{original_text}\n\n"
            f"{'━' * 28}\n"
            f"🏃 <b>KURYER QABUL QILDI:</b> {courier_name}\n"
            f"🕐 {accepted_time}"
        )
        try:
            await message.edit_text(
                new_text,
                parse_mode="HTML",
                reply_markup=None,
            )
        except Exception:
            pass

    await callback.answer(f"✅ #{order_id} buyurtma sizga biriktirildi!", show_alert=True)

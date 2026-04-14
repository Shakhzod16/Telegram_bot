from __future__ import annotations

import httpx
from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

router = Router()
BACKEND_URL = "http://localhost:8000/api/v1"


class SuperadminStates(StatesGroup):
    waiting_telegram_id = State()
    waiting_note = State()


def _headers_for_message(message: Message) -> dict[str, str]:
    telegram_id = message.from_user.id if message.from_user else 0
    return {"X-Telegram-Id": str(telegram_id)}


def _headers_for_callback(callback: CallbackQuery) -> dict[str, str]:
    telegram_id = callback.from_user.id if callback.from_user else 0
    return {"X-Telegram-Id": str(telegram_id)}


@router.message(F.text == "📊 Statistika")
async def show_stats(message: Message) -> None:
    try:
        headers = _headers_for_message(message)
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(f"{BACKEND_URL}/superadmin/stats", headers=headers)
        if resp.status_code != 200:
            await message.answer(f"❌ API xato {resp.status_code}: {resp.text}")
            return

        s = resp.json()
        text = (
            "📊 <b>Tizim Statistikasi:</b>\n\n"
            f"👥 Foydalanuvchilar: <b>{s.get('total_users', 0)}</b>\n"
            f"🛠 Adminlar: <b>{s.get('total_admins', 0)}</b>\n"
            f"📦 Mahsulotlar: <b>{s.get('total_products', 0)}</b>\n"
            f"📁 Kategoriyalar: <b>{s.get('total_categories', 0)}</b>\n"
            f"📋 Buyurtmalar: <b>{s.get('total_orders', 0)}</b>\n"
            f"💰 Daromad: <b>{s.get('total_revenue', 0):,.0f} so'm</b>\n\n"
            f"🗓 Bugun:\n"
            f"   Buyurtmalar: <b>{s.get('today_orders', 0)}</b>\n"
            f"   Daromad: <b>{s.get('today_revenue', 0):,.0f} so'm</b>"
        )
        await message.answer(text, parse_mode="HTML")
    except Exception as exc:
        await message.answer(f"❌ Xatolik: {exc}")


@router.message(F.text == "👤 Adminlar")
async def show_admins(message: Message) -> None:
    try:
        headers = _headers_for_message(message)
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(f"{BACKEND_URL}/superadmin/admins", headers=headers)
        if resp.status_code != 200:
            await message.answer(f"❌ API xato {resp.status_code}: {resp.text}")
            return

        admins = resp.json()
        if not admins:
            await message.answer("👤 Hozircha adminlar yo'q.")
            return

        text = "👤 <b>Adminlar ro'yxati:</b>\n\n"
        for admin in admins:
            text += (
                f"• <b>{admin['full_name']}</b>\n"
                f"  📱 {admin.get('phone') or '—'}\n"
                f"  📦 {admin.get('products_count', 0)} mahsulot | "
                f"📁 {admin.get('categories_count', 0)} kategoriya\n\n"
            )
        await message.answer(text, parse_mode="HTML")
    except Exception as exc:
        await message.answer(f"❌ Xatolik: {exc}")


@router.message(F.text == "📋 Whitelist")
async def whitelist_menu(message: Message) -> None:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Telefon qo'shish", callback_data="wl_add")],
            [InlineKeyboardButton(text="📋 Ro'yxatni ko'rish", callback_data="wl_list")],
        ]
    )
    await message.answer("📋 Whitelist boshqaruvi:", reply_markup=kb)


@router.callback_query(F.data == "wl_add")
async def wl_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.answer(
        "👤 Admin uchun Telegram ID yuboring:\n"
        "Masalan: 123456789\n"
        "(Telegram ID ni bilish uchun @userinfobot ga /start yuboring)",
    )
    await state.set_state(SuperadminStates.waiting_telegram_id)
    await callback.answer()


@router.message(StateFilter(SuperadminStates.waiting_telegram_id))
async def wl_receive_telegram_id(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer("❌ Faqat raqam kiriting!\nMasalan: 123456789")
        return

    telegram_id = int(text)
    await state.update_data(telegram_id=telegram_id)
    await message.answer(
        f"✅ Telegram ID: <code>{telegram_id}</code>\n\n"
        "📝 Izoh kiriting (o'tkazib yuborish uchun - yozing):",
        parse_mode="HTML",
    )
    await state.set_state(SuperadminStates.waiting_note)


@router.message(StateFilter(SuperadminStates.waiting_note))
async def wl_receive_note(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    telegram_id = data.get("telegram_id")
    if telegram_id is None:
        await message.answer("❌ Telegram ID topilmadi, qaytadan urinib ko'ring.")
        await state.clear()
        return

    note_text = (message.text or "").strip()
    note = None if note_text == "-" else note_text
    try:
        headers = _headers_for_message(message)
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{BACKEND_URL}/superadmin/whitelist",
                json={"telegram_id": telegram_id, "note": note},
                headers=headers,
            )
        if resp.status_code == 200:
            await message.answer(
                f"✅ Telegram ID <code>{telegram_id}</code> whitelist ga qo'shildi!",
                parse_mode="HTML",
            )
        else:
            await message.answer(f"❌ API xato {resp.status_code}: {resp.text}")
    except Exception as exc:
        await message.answer(f"❌ Xatolik: {exc}")
    await state.clear()


@router.callback_query(F.data == "wl_list")
async def wl_list_show(callback: CallbackQuery) -> None:
    try:
        headers = _headers_for_callback(callback)
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(f"{BACKEND_URL}/superadmin/whitelist", headers=headers)
        if resp.status_code != 200:
            await callback.message.answer(f"❌ API xato {resp.status_code}: {resp.text}")
            await callback.answer()
            return

        items = resp.json()
        if not items:
            await callback.message.answer("📋 Whitelist bo'sh.")
            await callback.answer()
            return

        text = "📋 <b>Whitelist:</b>\n\n"
        for item in items[:20]:
            status = "✅" if item["is_active"] else "❌"
            name = item.get("user_full_name") or "Ro'yxatdan o'tmagan"
            phone = item.get("user_phone") or "—"
            text += (
                f"{status} ID: <code>{item['telegram_id']}</code>\n"
                f"   👤 {name} | 📱 {phone}"
            )
            if item.get("note"):
                text += f"\n   📝 {item['note']}"
            text += "\n\n"
        await callback.message.answer(text, parse_mode="HTML")
    except Exception as exc:
        await callback.message.answer(f"❌ Xatolik: {exc}")
    await callback.answer()

from __future__ import annotations

import re

import httpx
from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

router = Router()
BACKEND_URL = "http://localhost:8000/api/v1"


class SuperadminStates(StatesGroup):
    waiting_phone = State()
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
            f"📅 Bugun:\n"
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
                f"  📱 {admin.get('phone', '—')}\n"
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
        "📱 Admin uchun telefon raqam yuboring:\n"
        "Format: <code>+998901234567</code>",
        parse_mode="HTML",
    )
    await state.set_state(SuperadminStates.waiting_phone)
    await callback.answer()


@router.message(StateFilter(SuperadminStates.waiting_phone))
async def wl_receive_phone(message: Message, state: FSMContext) -> None:
    phone = (message.text or "").strip()
    if not re.match(r"^\+998\d{9}$", phone):
        await message.answer(
            "❌ Noto'g'ri format!\nTo'g'ri: <code>+998901234567</code>",
            parse_mode="HTML",
        )
        return

    await state.update_data(phone=phone)
    await message.answer(
        f"✅ Telefon: <code>{phone}</code>\n\n"
        "📝 Izoh kiriting (o'tkazib yuborish uchun - yozing):",
        parse_mode="HTML",
    )
    await state.set_state(SuperadminStates.waiting_note)


@router.message(StateFilter(SuperadminStates.waiting_note))
async def wl_receive_note(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    phone = data.get("phone")
    if not phone:
        await message.answer("❌ Telefon topilmadi, qaytadan urinib ko'ring.")
        await state.clear()
        return

    note_text = (message.text or "").strip()
    note = None if note_text == "-" else note_text
    try:
        headers = _headers_for_message(message)
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{BACKEND_URL}/superadmin/whitelist",
                json={"phone": phone, "note": note},
                headers=headers,
            )
        if resp.status_code in {200, 201}:
            await message.answer(
                f"✅ <code>{phone}</code> whitelist ga qo'shildi!",
                parse_mode="HTML",
            )
        else:
            await message.answer(f"❌ API xato {resp.status_code}: {resp.text}")
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")
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
            text += f"{status} <code>{item['phone']}</code>"
            if item.get("note"):
                text += f" — {item['note']}"
            text += "\n"
        await callback.message.answer(text, parse_mode="HTML")
    except Exception as e:
        await callback.message.answer(f"❌ Xatolik: {e}")
    await callback.answer()

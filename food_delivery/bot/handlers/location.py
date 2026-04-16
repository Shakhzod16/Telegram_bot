from __future__ import annotations

import json
import logging
import os
from html import escape
from uuid import uuid4

import httpx
from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

router = Router()
logger = logging.getLogger(__name__)

BACKEND = os.getenv("BOT_BACKEND_INTERNAL_URL", "http://localhost:8000/api/v1").rstrip("/")


class OrderLocationStates(StatesGroup):
    waiting_location = State()
    waiting_note = State()


def location_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Lokatsiyamni yuborish", request_location=True)],
            [KeyboardButton(text="❌ Bekor qilish")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def _build_maps_url(lat: float | None, lon: float | None) -> str | None:
    if lat is None or lon is None:
        return None
    return f"https://maps.google.com/?q={lat},{lon}"


async def _ask_location(message: Message, state: FSMContext) -> None:
    await message.answer(
        "📍 <b>Yetkazish manzili</b>\n\n"
        "Telegram lokatsiyangizni yuboring.\n\n"
        "👇 Pastdagi tugmani bosing:",
        parse_mode="HTML",
        reply_markup=location_keyboard(),
    )
    await state.set_state(OrderLocationStates.waiting_location)


@router.callback_query(F.data == "checkout_with_location")
async def checkout_request_location(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(webapp_payload={"action": "request_location"})
    if callback.message is not None:
        await _ask_location(callback.message, state)
    await callback.answer()


@router.message(F.web_app_data)
async def handle_webapp_data(message: Message, state: FSMContext) -> None:
    try:
        payload = json.loads(message.web_app_data.data)
    except (TypeError, ValueError, json.JSONDecodeError):
        logger.warning("web_app_data_invalid_json")
        return

    if not isinstance(payload, dict):
        return

    action = str(payload.get("action") or "").strip()
    if action != "request_location":
        return

    checkout_comment = str(payload.get("checkout_comment") or "").strip()
    await state.update_data(
        webapp_payload=payload,
        checkout_comment=checkout_comment or None,
    )
    await _ask_location(message, state)


@router.message(
    F.text == "❌ Bekor qilish",
    StateFilter(OrderLocationStates.waiting_location, OrderLocationStates.waiting_note),
)
async def cancel_location(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=ReplyKeyboardRemove())


@router.message(F.location, StateFilter(OrderLocationStates.waiting_location))
async def receive_location(message: Message, state: FSMContext) -> None:
    lat = message.location.latitude
    lon = message.location.longitude
    address_text = f"📍 Lokatsiya: {lat:.6f}, {lon:.6f}"
    maps_url = _build_maps_url(lat, lon)

    await state.update_data(
        latitude=lat,
        longitude=lon,
        address=address_text,
        maps_url=maps_url,
    )

    maps_line = ""
    if maps_url:
        maps_line = f"🗺 <a href='{escape(maps_url)}'>Xaritada ko'rish</a>\n\n"

    await message.answer(
        "✅ Lokatsiya qabul qilindi!\n"
        f"{maps_line}"
        "📝 Qo'shimcha izoh kiriting\n"
        "(kirish, qavat, uy raqami va h.k.)\n"
        "O'tkazib yuborish uchun <b>-</b> yozing:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(OrderLocationStates.waiting_note)


@router.message(F.text, StateFilter(OrderLocationStates.waiting_location))
async def receive_manual_address(message: Message, state: FSMContext) -> None:
    manual_address = (message.text or "").strip()
    if len(manual_address) < 3:
        await message.answer("Manzil juda qisqa. Iltimos, aniqroq yozing yoki lokatsiya yuboring.")
        return

    await state.update_data(
        address=manual_address,
        latitude=None,
        longitude=None,
        maps_url=None,
    )
    await message.answer(
        "✅ Manzil qabul qilindi!\n\n"
        "📝 Qo'shimcha izoh kiriting\n"
        "(kirish, qavat, uy raqami va h.k.)\n"
        "O'tkazib yuborish uchun <b>-</b> yozing:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(OrderLocationStates.waiting_note)


@router.message(StateFilter(OrderLocationStates.waiting_note))
async def receive_note_and_order(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    checkout_comment = (data.get("checkout_comment") or "").strip()
    user_note_raw = (message.text or "").strip()
    note = ""
    if user_note_raw != "-":
        note = user_note_raw
    elif checkout_comment:
        note = checkout_comment

    lat = data.get("latitude")
    lon = data.get("longitude")
    address = str(data.get("address") or "").strip()
    maps_url = data.get("maps_url")
    if not maps_url:
        maps_url = _build_maps_url(lat, lon)

    if not address:
        await message.answer("❌ Manzil topilmadi. Qaytadan urinib ko'ring.")
        await state.clear()
        return

    if message.from_user is None:
        await message.answer("❌ Foydalanuvchi topilmadi.")
        await state.clear()
        return

    telegram_id = message.from_user.id
    headers = {"X-Telegram-Id": str(telegram_id)}

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            cart_resp = await client.get(f"{BACKEND}/cart", headers=headers)
            if cart_resp.status_code != 200:
                await message.answer("❌ Savatni tekshirib bo'lmadi. Qayta urinib ko'ring.")
                await state.clear()
                return

            cart_payload = cart_resp.json()
            if not isinstance(cart_payload, dict) or not cart_payload.get("items"):
                await message.answer("❌ Savat bo'sh!")
                await state.clear()
                return

            address_resp = await client.post(
                f"{BACKEND}/addresses",
                headers=headers,
                json={
                    "title": "Telegram lokatsiya",
                    "address_line": address,
                    "lat": lat,
                    "lng": lon,
                    "comment": note or None,
                    "is_default": False,
                },
            )
            if address_resp.status_code != 200:
                logger.warning("address_create_failed status=%s body=%s", address_resp.status_code, address_resp.text)
                await message.answer("❌ Manzilni saqlashda xatolik.")
                await state.clear()
                return

            address_payload = address_resp.json()
            address_id = int(address_payload["id"])
            idempotency_key = f"tg-loc-{telegram_id}-{uuid4().hex[:16]}"

            order_resp = await client.post(
                f"{BACKEND}/orders",
                headers=headers,
                json={
                    "address_id": address_id,
                    "comment": note or None,
                    "promo_code": None,
                    "idempotency_key": idempotency_key,
                    "latitude": lat,
                    "longitude": lon,
                    "maps_url": maps_url,
                },
            )

        if order_resp.status_code == 200:
            order = order_resp.json()
            order_id = order.get("id")
            total = float(order.get("total_amount", 0) or 0)
            await message.answer(
                f"✅ <b>Buyurtma #{order_id} qabul qilindi!</b>\n\n"
                f"📍 Manzil: {escape(address)}\n"
                f"💰 Jami: <b>{total:,.0f} so'm</b>\n\n"
                "🕐 Buyurtmangiz tayyorlanmoqda...\n"
                "Holati haqida xabar beramiz.",
                parse_mode="HTML",
            )
        else:
            logger.warning("order_create_failed status=%s body=%s", order_resp.status_code, order_resp.text)
            await message.answer("❌ Buyurtma yaratishda xatolik.")
    except Exception:
        logger.exception("receive_note_and_order_failed")
        await message.answer("❌ Server bilan xatolik")
    finally:
        await state.clear()

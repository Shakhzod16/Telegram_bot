from __future__ import annotations

import logging
import os
from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import httpx
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    WebAppInfo,
)

router = Router()
logger = logging.getLogger(__name__)

BACKEND_ROOT = os.getenv("BOT_BACKEND_INTERNAL_URL", "http://localhost:8000").rstrip("/")
WEBAPP_FALLBACK_URL = os.getenv("WEBAPP_URL", "")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "support_username").lstrip("@")
BASE_DIR = Path(__file__).resolve().parents[2]


class Reg(StatesGroup):
    lang = State()
    phone = State()
    location = State()


TEXTS: dict[str, dict[str, str]] = {
    "greeting": {
        "uz": "Assalomu alaykum <b>{name}</b>! FoodExpress botiga xush kelibsiz.",
        "ru": "Здравствуйте, <b>{name}</b>! Добро пожаловать в FoodExpress.",
        "en": "Hi <b>{name}</b>! Welcome to FoodExpress.",
    },
    "lang_prompt": {
        "uz": "Muloqot tilini tanlang:",
        "ru": "Выберите язык:",
        "en": "Select language:",
    },
    "phone_prompt": {
        "uz": "Telefon raqamingizni yuboring:",
        "ru": "Отправьте ваш номер телефона:",
        "en": "Send your phone number:",
    },
    "phone_btn": {
        "uz": "Raqamni yuborish",
        "ru": "Отправить номер",
        "en": "Send number",
    },
    "phone_invalid_owner": {
        "uz": "Faqat o'zingizning kontaktingizni yuboring.",
        "ru": "Отправьте именно свой контакт.",
        "en": "Please send your own contact.",
    },
    "reg_success": {
        "uz": "Ro'yxatdan muvaffaqiyatli o'tdingiz.",
        "ru": "Вы успешно зарегистрированы.",
        "en": "You are successfully registered.",
    },
    "reg_failed": {
        "uz": "Ro'yxatdan o'tishda xatolik bo'ldi. Qaytadan urinib ko'ring.",
        "ru": "Ошибка регистрации. Попробуйте снова.",
        "en": "Registration failed. Please try again.",
    },
    "already_reg": {
        "uz": "Xush kelibsiz, <b>{name}</b>.\nRolingiz: <b>{role}</b>",
        "ru": "С возвращением, <b>{name}</b>.\nВаша роль: <b>{role}</b>",
        "en": "Welcome back, <b>{name}</b>.\nYour role: <b>{role}</b>",
    },
    "role_user": {
        "uz": "Foydalanuvchi",
        "ru": "Пользователь",
        "en": "User",
    },
    "role_admin": {
        "uz": "Admin",
        "ru": "Админ",
        "en": "Admin",
    },
    "role_superadmin": {
        "uz": "Super admin",
        "ru": "Суперадмин",
        "en": "Super admin",
    },
    "location_prompt": {
        "uz": "Yetkazib berish manzilini yuboring yoki qo'lda kiriting:",
        "ru": "Отправьте геолокацию или введите адрес вручную:",
        "en": "Send your location or enter your address manually:",
    },
    "loc_send_btn": {
        "uz": "Lokatsiyani yuborish",
        "ru": "Отправить геолокацию",
        "en": "Send location",
    },
    "loc_manual_btn": {
        "uz": "Manzilni qo'lda yozish",
        "ru": "Ввести адрес вручную",
        "en": "Enter address manually",
    },
    "loc_manual_ask": {
        "uz": "Manzilni yozing (ko'cha, uy raqami, mo'ljal):",
        "ru": "Введите адрес (улица, дом, ориентир):",
        "en": "Type your address (street, house, landmark):",
    },
    "loc_saved": {
        "uz": "Manzil saqlandi.",
        "ru": "Адрес сохранен.",
        "en": "Address saved.",
    },
    "loc_invalid": {
        "uz": "Manzil aniq emas. Iltimos, to'liqroq yozing.",
        "ru": "Адрес слишком короткий. Уточните, пожалуйста.",
        "en": "Address is too short. Please provide more details.",
    },
    "loc_save_failed": {
        "uz": "Manzilni saqlab bo'lmadi. Qaytadan urinib ko'ring.",
        "ru": "Не удалось сохранить адрес. Попробуйте снова.",
        "en": "Could not save address. Please try again.",
    },
    "cancel_btn": {
        "uz": "Bekor qilish",
        "ru": "Отмена",
        "en": "Cancel",
    },
    "cancelled": {
        "uz": "Amal bekor qilindi.",
        "ru": "Действие отменено.",
        "en": "Action cancelled.",
    },
    "open_menu_btn": {
        "uz": "🍔 Menuni ochish",
        "ru": "🍔 Открыть меню",
        "en": "🍔 Open menu",
    },
    "open_menu_hint": {
        "uz": "Quyidagi tugma orqali menuni oching.",
        "ru": "Откройте меню кнопкой ниже.",
        "en": "Open menu with the button below.",
    },
    "profile_btn": {
        "uz": "👤 Profil",
        "ru": "👤 Профиль",
        "en": "👤 Profile",
    },
    "contact_btn": {
        "uz": "📞 Bog'lanish",
        "ru": "📞 Связаться",
        "en": "📞 Contact",
    },
    "contact_text": {
        "uz": "Qo'llab-quvvatlash: @{support}",
        "ru": "Поддержка: @{support}",
        "en": "Support: @{support}",
    },
    "order_type": {
        "uz": "Buyurtma turini tanlang:",
        "ru": "Выберите тип заказа:",
        "en": "Select order type:",
    },
    "delivery_btn": {
        "uz": "Yetkazib berish",
        "ru": "Доставка",
        "en": "Delivery",
    },
    "pickup_btn": {
        "uz": "Olib ketish",
        "ru": "Самовывоз",
        "en": "Pickup",
    },
}


ADMIN_BUTTONS = (
    "📦 Mahsulotlarim",
    "📁 Kategoriyalarim",
    "📋 Buyurtmalar",
    "⚙️ Sozlamalar",
    "🌐 WebApp",
)
SUPERADMIN_BUTTONS = (
    "📊 Statistika",
    "👤 Adminlar",
    "📋 Whitelist",
)


def t(key: str, lang: str = "uz", **kwargs: Any) -> str:
    table = TEXTS.get(key, {})
    value = table.get(lang) or table.get("uz", "")
    return value.format(**kwargs) if kwargs else value


def _all_values(key: str) -> set[str]:
    return {
        value.strip()
        for value in TEXTS.get(key, {}).values()
        if isinstance(value, str) and value.strip()
    }


CANCEL_TEXTS = _all_values("cancel_btn")
MANUAL_LOCATION_TEXTS = _all_values("loc_manual_btn")
CONTACT_TEXTS = _all_values("contact_btn")
OPEN_MENU_TEXTS = _all_values("open_menu_btn")
PROFILE_TEXTS = _all_values("profile_btn")
ORDER_TEXTS = {"🛒 Buyurtma berish", "Buyurtma berish", "Order", "Заказать"}

# Backward-compatible button aliases from older bot keyboards.
CONTACT_TEXTS.update({"📞 Aloqa", "Aloqa"})
OPEN_MENU_TEXTS.update({"🍔 Menu ochish", "Menu ochish", "Menu"})

NON_ADDRESS_TEXTS = set()
NON_ADDRESS_TEXTS.update(CANCEL_TEXTS)
NON_ADDRESS_TEXTS.update(MANUAL_LOCATION_TEXTS)
NON_ADDRESS_TEXTS.update(CONTACT_TEXTS)
NON_ADDRESS_TEXTS.update(OPEN_MENU_TEXTS)
NON_ADDRESS_TEXTS.update(PROFILE_TEXTS)
NON_ADDRESS_TEXTS.update(ORDER_TEXTS)
NON_ADDRESS_TEXTS.update(_all_values("phone_btn"))
NON_ADDRESS_TEXTS.update(ADMIN_BUTTONS)
NON_ADDRESS_TEXTS.update(SUPERADMIN_BUTTONS)


def _normalize_webapp_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    try:
        parsed = urlsplit(raw)
    except Exception:
        return raw
    path = parsed.path or ""
    if path in {"", "/"}:
        path = "/webapp/"
    elif path.rstrip("/") == "/webapp":
        path = "/webapp/"
    normalized = parsed._replace(path=path, query="", fragment="")
    return urlunsplit(normalized)


def _resolve_webapp_url() -> str:
    candidates = [
        BASE_DIR / "logs" / "runtime_webapp_url.txt",
        BASE_DIR / "runtime_webapp_url.txt",
    ]
    for path in candidates:
        try:
            if path.exists():
                value = path.read_text(encoding="utf-8").strip()
                if value:
                    return _normalize_webapp_url(value)
        except OSError:
            continue

    fallback = _normalize_webapp_url(WEBAPP_FALLBACK_URL)
    if fallback:
        return fallback
    return _normalize_webapp_url(f"{BACKEND_ROOT}/webapp/")


def _role_from_user(user: dict[str, Any] | None) -> str:
    if not user:
        return "user"
    if bool(user.get("is_superadmin")):
        return "superadmin"
    if bool(user.get("is_admin")):
        return "admin"
    return "user"


async def _api_request(
    method: str,
    path: str,
    *,
    headers: dict[str, str] | None = None,
    json_body: dict[str, Any] | None = None,
) -> httpx.Response | None:
    url = f"{BACKEND_ROOT}{path}"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=json_body,
            )
        return response
    except Exception:
        logger.exception("api_request_failed method=%s path=%s", method, path)
        return None


async def _get_user(telegram_id: int) -> dict[str, Any] | None:
    response = await _api_request("GET", f"/api/users/{telegram_id}")
    if response is None or response.status_code != 200:
        return None
    payload = response.json()
    if isinstance(payload, dict):
        return payload
    return None


async def _register_user(
    telegram_id: int,
    phone: str,
    name: str,
    lang: str,
) -> tuple[bool, dict[str, Any] | None]:
    response = await _api_request(
        "POST",
        "/api/users/register",
        json_body={
            "telegram_id": telegram_id,
            "phone": (phone or "").strip(),
            "name": (name or "").strip(),
            "lang": (lang or "uz").strip().lower(),
        },
    )
    if response is None:
        return False, None
    if response.status_code != 200:
        logger.warning("register_user_failed status=%s body=%s", response.status_code, response.text[:300])
        return False, None
    payload = response.json()
    if isinstance(payload, dict):
        return True, payload
    return True, None


async def _save_address(
    telegram_id: int,
    address: str,
    *,
    lat: float | None = None,
    lon: float | None = None,
) -> bool:
    response = await _api_request(
        "POST",
        "/api/addresses/save",
        json_body={
            "telegram_id": telegram_id,
            "address": (address or "").strip(),
            "lat": lat,
            "lon": lon,
        },
    )
    if response is None:
        return False
    if response.status_code != 200:
        logger.warning("save_address_failed status=%s body=%s", response.status_code, response.text[:300])
        return False
    return True


async def _has_saved_address(telegram_id: int) -> bool:
    response = await _api_request(
        "GET",
        "/api/v1/addresses",
        headers={"X-Telegram-Id": str(telegram_id)},
    )
    if response is None or response.status_code != 200:
        return False
    payload = response.json()
    return isinstance(payload, list) and len(payload) > 0


def _main_keyboard(lang: str, role: str) -> ReplyKeyboardMarkup:
    webapp_url = _resolve_webapp_url()
    menu_button = (
        KeyboardButton(
            text=t("open_menu_btn", lang),
            web_app=WebAppInfo(url=webapp_url),
        )
        if webapp_url
        else KeyboardButton(text=t("open_menu_btn", lang))
    )

    rows: list[list[KeyboardButton]] = [
        [menu_button, KeyboardButton(text=t("profile_btn", lang))],
        [KeyboardButton(text=t("contact_btn", lang))],
    ]

    if role in {"admin", "superadmin"}:
        rows.append(
            [
                KeyboardButton(text=ADMIN_BUTTONS[0]),
                KeyboardButton(text=ADMIN_BUTTONS[1]),
            ]
        )
        rows.append(
            [
                KeyboardButton(text=ADMIN_BUTTONS[2]),
                KeyboardButton(text=ADMIN_BUTTONS[3]),
            ]
        )
        rows.append([KeyboardButton(text=ADMIN_BUTTONS[4])])

    if role == "superadmin":
        rows.append(
            [
                KeyboardButton(text=SUPERADMIN_BUTTONS[0]),
                KeyboardButton(text=SUPERADMIN_BUTTONS[1]),
            ]
        )
        rows.append([KeyboardButton(text=SUPERADMIN_BUTTONS[2])])

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        is_persistent=True,
    )


def _location_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("loc_send_btn", lang), request_location=True)],
            [KeyboardButton(text=t("loc_manual_btn", lang))],
            [KeyboardButton(text=t("cancel_btn", lang))],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


async def _ask_location(message: Message, lang: str) -> None:
    await message.answer(
        t("location_prompt", lang),
        reply_markup=_location_keyboard(lang),
    )


async def _send_order_type(message: Message, lang: str) -> None:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("delivery_btn", lang), callback_data="order_delivery"),
                InlineKeyboardButton(text=t("pickup_btn", lang), callback_data="order_pickup"),
            ]
        ]
    )
    await message.answer(t("order_type", lang), reply_markup=kb)


async def _resolve_user_context(state: FSMContext, telegram_id: int) -> tuple[str, str]:
    data = await state.get_data()
    lang = str(data.get("lang") or "").strip().lower()
    role = str(data.get("role") or "").strip().lower()
    if lang and role:
        return lang, role

    user = await _get_user(telegram_id)
    if user:
        lang = (str(user.get("lang") or "uz").strip().lower() or "uz")
        role = _role_from_user(user)
    else:
        lang = "uz"
        role = "user"

    await state.update_data(lang=lang, role=role)
    return lang, role


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()

    if message.from_user is None:
        return

    telegram_id = message.from_user.id
    first_name = message.from_user.first_name or "Foydalanuvchi"
    safe_name = escape(first_name)

    user = await _get_user(telegram_id)
    if user is None:
        lang_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang_uz"),
                    InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
                    InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
                ]
            ]
        )
        await message.answer(t("greeting", "uz", name=safe_name), parse_mode="HTML")
        await message.answer(t("lang_prompt", "uz"), reply_markup=lang_kb)
        await state.set_state(Reg.lang)
        return

    lang = (str(user.get("lang") or "uz").strip().lower() or "uz")
    role = _role_from_user(user)
    await state.update_data(lang=lang, role=role)

    await message.answer(
        t("already_reg", lang, name=safe_name, role=t(f"role_{role}", lang)),
        parse_mode="HTML",
        reply_markup=_main_keyboard(lang, role),
    )

    if await _has_saved_address(telegram_id):
        await _send_order_type(message, lang)
    else:
        await _ask_location(message, lang)
        await state.set_state(Reg.location)


@router.callback_query(Reg.lang, F.data.in_({"lang_uz", "lang_ru", "lang_en"}))
async def choose_language(call: CallbackQuery, state: FSMContext) -> None:
    lang = (call.data or "lang_uz").split("_", 1)[1]
    await state.update_data(lang=lang)

    phone_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("phone_btn", lang), request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    if call.message:
        await call.message.edit_reply_markup()
        await call.message.answer(t("phone_prompt", lang), reply_markup=phone_kb)
    await state.set_state(Reg.phone)
    await call.answer()


@router.message(Reg.phone, F.contact)
async def handle_contact(message: Message, state: FSMContext) -> None:
    if message.from_user is None or message.contact is None:
        return

    lang = str((await state.get_data()).get("lang") or "uz")
    if message.contact.user_id and message.contact.user_id != message.from_user.id:
        await message.answer(t("phone_invalid_owner", lang))
        return

    phone = (message.contact.phone_number or "").strip()
    first_name = (message.from_user.first_name or "").strip()

    ok, payload = await _register_user(
        telegram_id=message.from_user.id,
        phone=phone,
        name=first_name,
        lang=lang,
    )
    if not ok:
        await message.answer(t("reg_failed", lang))
        return

    role = _role_from_user(payload)
    await state.update_data(lang=lang, role=role)

    await message.answer(
        t("reg_success", lang),
        reply_markup=_main_keyboard(lang, role),
    )
    await _ask_location(message, lang)
    await state.set_state(Reg.location)


@router.message(Reg.phone)
async def phone_fallback(message: Message, state: FSMContext) -> None:
    lang = str((await state.get_data()).get("lang") or "uz")
    await message.answer(t("phone_prompt", lang))


@router.message(Reg.location, F.text.func(lambda value: (value or "").strip() in CANCEL_TEXTS))
async def cancel_location(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        await state.clear()
        return
    lang, role = await _resolve_user_context(state, message.from_user.id)
    await message.answer(
        t("cancelled", lang),
        reply_markup=_main_keyboard(lang, role),
    )
    await state.clear()


@router.message(Reg.location, F.location)
async def handle_geo(message: Message, state: FSMContext) -> None:
    if message.from_user is None or message.location is None:
        return

    lang, role = await _resolve_user_context(state, message.from_user.id)
    lat = message.location.latitude
    lon = message.location.longitude

    if not await _save_address(message.from_user.id, "geo", lat=lat, lon=lon):
        await message.answer(t("loc_save_failed", lang))
        return

    await message.answer(
        t("loc_saved", lang),
        reply_markup=_main_keyboard(lang, role),
    )
    await _send_order_type(message, lang)
    await state.clear()


@router.message(Reg.location, F.text.func(lambda value: (value or "").strip() in MANUAL_LOCATION_TEXTS))
async def ask_manual_address(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    lang, _role = await _resolve_user_context(state, message.from_user.id)
    await message.answer(
        t("loc_manual_ask", lang),
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(Reg.location, Command("contact"))
async def contact_command_while_location(message: Message, state: FSMContext) -> None:
    await cmd_contact(message, state)


@router.message(Reg.location, Command("menu"))
async def menu_command_while_location(message: Message, state: FSMContext) -> None:
    await cmd_menu(message, state)


@router.message(Reg.location, F.text.func(lambda value: (value or "").strip() in CONTACT_TEXTS))
async def contact_while_location(message: Message, state: FSMContext) -> None:
    await cmd_contact(message, state)


@router.message(Reg.location, F.text.func(lambda value: (value or "").strip() in OPEN_MENU_TEXTS))
async def menu_while_location(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    lang, role = await _resolve_user_context(state, message.from_user.id)
    await message.answer(
        t("open_menu_hint", lang),
        reply_markup=_main_keyboard(lang, role),
    )
    await _send_order_type(message, lang)


@router.message(Reg.location, F.text.func(lambda value: (value or "").strip() in ORDER_TEXTS))
async def order_while_location(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    lang, _role = await _resolve_user_context(state, message.from_user.id)
    await _send_order_type(message, lang)


@router.message(Reg.location, F.text)
async def handle_manual_address(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return

    lang, role = await _resolve_user_context(state, message.from_user.id)
    address = (message.text or "").strip()
    if len(address) < 5 or address in NON_ADDRESS_TEXTS or address.startswith("/"):
        await message.answer(t("loc_invalid", lang))
        return

    if not await _save_address(message.from_user.id, address):
        await message.answer(t("loc_save_failed", lang))
        return

    await message.answer(
        t("loc_saved", lang),
        reply_markup=_main_keyboard(lang, role),
    )
    await _send_order_type(message, lang)
    await state.clear()


@router.callback_query(F.data == "order_delivery")
async def cb_delivery(call: CallbackQuery, state: FSMContext) -> None:
    if call.from_user is None:
        await call.answer()
        return
    lang, _role = await _resolve_user_context(state, call.from_user.id)
    if call.message:
        await call.message.edit_reply_markup()
        await _ask_location(call.message, lang)
    await state.set_state(Reg.location)
    await call.answer()


@router.callback_query(F.data == "order_pickup")
async def cb_pickup(call: CallbackQuery, state: FSMContext) -> None:
    if call.from_user is None:
        await call.answer()
        return
    lang, role = await _resolve_user_context(state, call.from_user.id)
    if call.message:
        await call.message.edit_reply_markup()
        await call.message.answer(
            t("open_menu_hint", lang),
            reply_markup=_main_keyboard(lang, role),
        )
    await state.clear()
    await call.answer()


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    user = await _get_user(message.from_user.id)
    if user is None:
        await cmd_start(message, state)
        return

    lang = str(user.get("lang") or "uz")
    role = _role_from_user(user)
    await state.update_data(lang=lang, role=role)
    await message.answer(
        t("open_menu_hint", lang),
        reply_markup=_main_keyboard(lang, role),
    )
    await _send_order_type(message, lang)


@router.message(Command("contact"))
async def cmd_contact(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        await message.answer(f"@{SUPPORT_USERNAME}")
        return
    lang, _role = await _resolve_user_context(state, message.from_user.id)
    await message.answer(t("contact_text", lang, support=SUPPORT_USERNAME))


@router.message(F.text.func(lambda value: (value or "").strip() in PROFILE_TEXTS))
async def profile_button(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return

    lang, _role = await _resolve_user_context(state, message.from_user.id)
    response = await _api_request(
        "GET",
        "/api/v1/profile",
        headers={"X-Telegram-Id": str(message.from_user.id)},
    )
    if response is None or response.status_code != 200:
        await message.answer("Profil ma'lumotlarini olib bo'lmadi.")
        return

    try:
        payload: Any = response.json()
    except ValueError:
        payload = {}
    if not isinstance(payload, dict):
        await message.answer("Profil ma'lumotlari topilmadi.")
        return

    full_name = escape(str(payload.get("full_name") or "Foydalanuvchi"))
    phone = escape(str(payload.get("phone") or "—"))
    user_lang = escape(str(payload.get("language") or lang))
    telegram_id = message.from_user.id

    if bool(payload.get("is_superadmin")):
        role_label = t("role_superadmin", lang)
    elif bool(payload.get("is_admin")):
        role_label = t("role_admin", lang)
    else:
        role_label = t("role_user", lang)

    await message.answer(
        "👤 <b>Profil</b>\n\n"
        f"Ism: <b>{full_name}</b>\n"
        f"Telegram ID: <code>{telegram_id}</code>\n"
        f"Rol: <b>{escape(role_label)}</b>\n"
        f"Telefon: <b>{phone}</b>\n"
        f"Til: <b>{user_lang}</b>",
        parse_mode="HTML",
    )


@router.message(F.text.func(lambda value: (value or "").strip() in CONTACT_TEXTS))
async def contact_button(message: Message, state: FSMContext) -> None:
    await cmd_contact(message, state)


@router.message(F.text.func(lambda value: (value or "").strip() in ORDER_TEXTS))
async def order_button(message: Message, state: FSMContext) -> None:
    await cmd_menu(message, state)


@router.message(F.text.func(lambda value: (value or "").strip() in OPEN_MENU_TEXTS))
async def menu_button(message: Message, state: FSMContext) -> None:
    await cmd_menu(message, state)

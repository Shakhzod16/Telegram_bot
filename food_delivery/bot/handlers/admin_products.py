from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import httpx
from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

from app.core.config import settings

router = Router()
logger = logging.getLogger(__name__)
BACKEND = "http://localhost:8000/api/v1"
BASE_DIR = Path(__file__).resolve().parents[2]


class ProductStates(StatesGroup):
    # Tahrirlash
    edit_choose_field = State()
    edit_name_uz = State()
    edit_price = State()
    edit_active = State()
    # O'chirish tasdiqi
    delete_confirm = State()


def _resolve_webapp_url() -> str:
    candidate_paths = [
        BASE_DIR / "logs" / "runtime_webapp_url.txt",
        BASE_DIR / "runtime_webapp_url.txt",
    ]
    for path in candidate_paths:
        try:
            if path.exists():
                url = path.read_text(encoding="utf-8").strip()
                if url:
                    return _normalize_webapp_url(url)
        except OSError:
            continue
    return _normalize_webapp_url(str(getattr(settings, "WEBAPP_URL", "")).strip())


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


def _admin_product_new_url() -> str:
    base = _resolve_webapp_url().rstrip("/")
    if not base:
        return ""
    return f"{base}/admin/products/new"


def _to_price(value: object) -> float:
    try:
        return float(str(value).replace(" ", "").replace(",", ""))
    except Exception:
        return 0.0


def products_list_keyboard(products: list) -> InlineKeyboardMarkup:
    """Mahsulotlar ro'yxati keyboard"""
    buttons = []
    for p in products:
        status = "✅" if p.get("is_active") else "❌"
        name = p.get("name_uz") or p.get("name_ru") or "Nomsiz"
        price = _to_price(p.get("base_price", 0))
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{status} {name} — {price:,.0f} so'm",
                    callback_data=f"prod_detail:{p['id']}",
                )
            ]
        )
    buttons.append(
        [
            InlineKeyboardButton(
                text="➕ Yangi mahsulot qo'shish",
                callback_data="prod_add_new",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_detail_keyboard(product_id: int, is_active: bool) -> InlineKeyboardMarkup:
    """Bitta mahsulot boshqaruv keyboard"""
    active_text = "🔴 O'chirish (deaktiv)" if is_active else "🟢 Yoqish (aktiv)"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Nomini o'zgartirish",
                    callback_data=f"prod_edit_name:{product_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💰 Narxini o'zgartirish",
                    callback_data=f"prod_edit_price:{product_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=active_text,
                    callback_data=f"prod_toggle_active:{product_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 O'chirish",
                    callback_data=f"prod_delete:{product_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Orqaga",
                    callback_data="prod_list_back",
                )
            ],
        ]
    )


# ─── MAHSULOTLAR RO'YXATI ────────────────────────────────────────────


@router.message(F.text == "📦 Mahsulotlarim")
async def my_products(message: Message) -> None:
    telegram_id = message.from_user.id
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND}/admin/products",
                headers={"X-Telegram-Id": str(telegram_id)},
            )
        if resp.status_code != 200:
            await message.answer(f"❌ Xatolik: {resp.text}")
            return

        products = resp.json()
        if not products:
            await message.answer(
                "📦 Sizda hozircha mahsulot yo'q.\n\n"
                "Mahsulot qo'shish uchun tugmani bosing:",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="➕ Mahsulot qo'shish",
                                callback_data="prod_add_new",
                            )
                        ]
                    ]
                ),
            )
            return

        await message.answer(
            f"📦 <b>Mahsulotlaringiz</b> ({len(products)} ta):\n\n"
            "Tahrirlash uchun mahsulotni tanlang:",
            parse_mode="HTML",
            reply_markup=products_list_keyboard(products),
        )

    except Exception as exc:
        logger.error("my_products: %s", exc)
        await message.answer("❌ Server bilan xatolik")


@router.callback_query(F.data == "prod_add_new")
async def open_product_add_webapp(callback: CallbackQuery) -> None:
    webapp_url = _admin_product_new_url()
    if callback.message is None:
        await callback.answer("Xabar topilmadi", show_alert=True)
        return

    if not webapp_url.startswith("https://"):
        await callback.message.answer(
            "❌ Admin WebApp URL topilmadi yoki HTTPS emas.\n"
            "Iltimos, serverni `python run_dev.py` bilan qayta ishga tushiring.",
        )
        await callback.answer()
        return

    await callback.message.answer(
        "➕ Mahsulot qo'shish formasini ochish uchun tugmani bosing:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🌐 Mahsulot qo'shish (WebApp)",
                        web_app=WebAppInfo(url=webapp_url),
                    )
                ]
            ]
        ),
    )
    await callback.answer()


@router.message(F.text == "🌐 WebApp")
async def open_admin_webapp(message: Message) -> None:
    base_webapp_url = _resolve_webapp_url().rstrip("/")
    admin_url = f"{base_webapp_url}/admin" if base_webapp_url else ""
    if not admin_url.startswith("https://"):
        await message.answer(
            "❌ WebApp URL topilmadi yoki HTTPS emas.\n"
            "Iltimos, serverni `python run_dev.py` bilan qayta ishga tushiring.",
        )
        return

    await message.answer(
        "🌐 Admin WebApp ochish:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Open Admin WebApp",
                        web_app=WebAppInfo(url=admin_url),
                    )
                ]
            ]
        ),
    )


@router.callback_query(F.data == "prod_list_back")
async def back_to_products(callback: CallbackQuery) -> None:
    telegram_id = callback.from_user.id
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND}/admin/products",
                headers={"X-Telegram-Id": str(telegram_id)},
            )
        products = resp.json()
        if callback.message:
            await callback.message.edit_text(
                f"📦 <b>Mahsulotlaringiz</b> ({len(products)} ta):",
                parse_mode="HTML",
                reply_markup=products_list_keyboard(products),
            )
    except Exception:
        await callback.answer("❌ Xatolik", show_alert=True)
    await callback.answer()


# ─── MAHSULOT DETAIL ─────────────────────────────────────────────────


@router.callback_query(F.data.startswith("prod_detail:"))
async def product_detail(callback: CallbackQuery) -> None:
    product_id = int((callback.data or "").split(":")[1])
    telegram_id = callback.from_user.id

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND}/admin/products/{product_id}",
                headers={"X-Telegram-Id": str(telegram_id)},
            )
        if resp.status_code == 404:
            await callback.answer("❌ Mahsulot topilmadi", show_alert=True)
            return
        if resp.status_code == 403:
            await callback.answer("❌ Bu mahsulot sizga tegishli emas", show_alert=True)
            return

        p = resp.json()
        name = p.get("name_uz") or p.get("name_ru") or "Nomsiz"
        status = "✅ Aktiv" if p.get("is_active") else "❌ Nofaol"
        price = _to_price(p.get("base_price", 0))
        weight = p.get("weight_grams", 0)

        text = (
            f"📦 <b>{name}</b>\n\n"
            f"💰 Narx: <b>{price:,.0f} so'm</b>\n"
            f"⚖️ Og'irlik: {weight} g\n"
            f"📊 Holat: {status}\n"
            f"🆔 ID: {product_id}"
        )

        if callback.message:
            await callback.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=product_detail_keyboard(product_id, p.get("is_active", True)),
            )

    except Exception as exc:
        logger.error("product_detail: %s", exc)
        await callback.answer("❌ Xatolik", show_alert=True)
    await callback.answer()


# ─── NOM TAHRIRLASH ──────────────────────────────────────────────────


@router.callback_query(F.data.startswith("prod_edit_name:"))
async def edit_name_start(callback: CallbackQuery, state: FSMContext) -> None:
    product_id = int((callback.data or "").split(":")[1])
    await state.update_data(product_id=product_id)
    if callback.message:
        await callback.message.answer("✏️ Yangi nomni kiriting (o'zbek tilida):")
    await state.set_state(ProductStates.edit_name_uz)
    await callback.answer()


@router.message(StateFilter(ProductStates.edit_name_uz))
async def edit_name_finish(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    product_id = data["product_id"]
    new_name = (message.text or "").strip()

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.put(
                f"{BACKEND}/admin/products/{product_id}",
                json={"name_uz": new_name},
                headers={"X-Telegram-Id": str(message.from_user.id)},
            )
        if resp.status_code == 200:
            await message.answer(
                f"✅ Nom yangilandi: <b>{new_name}</b>",
                parse_mode="HTML",
            )
        else:
            await message.answer(f"❌ Xatolik: {resp.text}")
    except Exception as exc:
        await message.answer(f"❌ Server xatolik: {exc}")

    await state.clear()


# ─── NARX TAHRIRLASH ─────────────────────────────────────────────────


@router.callback_query(F.data.startswith("prod_edit_price:"))
async def edit_price_start(callback: CallbackQuery, state: FSMContext) -> None:
    product_id = int((callback.data or "").split(":")[1])
    await state.update_data(product_id=product_id)
    if callback.message:
        await callback.message.answer(
            "💰 Yangi narxni kiriting (so'mda, faqat raqam):\n"
            "Masalan: 35000"
        )
    await state.set_state(ProductStates.edit_price)
    await callback.answer()


@router.message(StateFilter(ProductStates.edit_price))
async def edit_price_finish(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    product_id = data["product_id"]

    try:
        price = float((message.text or "").strip().replace(" ", "").replace(",", ""))
    except ValueError:
        await message.answer("❌ Faqat raqam kiriting!\nMasalan: 35000")
        return

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.put(
                f"{BACKEND}/admin/products/{product_id}",
                json={"base_price": price},
                headers={"X-Telegram-Id": str(message.from_user.id)},
            )
        if resp.status_code == 200:
            await message.answer(
                f"✅ Narx yangilandi: <b>{price:,.0f} so'm</b>",
                parse_mode="HTML",
            )
        else:
            await message.answer(f"❌ Xatolik: {resp.text}")
    except Exception as exc:
        await message.answer(f"❌ Server xatolik: {exc}")

    await state.clear()


# ─── AKTIV/NOFAOL TOGGLE ────────────────────────────────────────────


@router.callback_query(F.data.startswith("prod_toggle_active:"))
async def toggle_active(callback: CallbackQuery) -> None:
    product_id = int((callback.data or "").split(":")[1])
    telegram_id = callback.from_user.id

    try:
        # Avval hozirgi holatni ol
        async with httpx.AsyncClient() as client:
            get_resp = await client.get(
                f"{BACKEND}/admin/products/{product_id}",
                headers={"X-Telegram-Id": str(telegram_id)},
            )
        if get_resp.status_code != 200:
            await callback.answer("❌ Mahsulot topilmadi", show_alert=True)
            return

        current = get_resp.json()
        new_status = not current.get("is_active", True)

        async with httpx.AsyncClient() as client:
            resp = await client.put(
                f"{BACKEND}/admin/products/{product_id}",
                json={"is_active": new_status},
                headers={"X-Telegram-Id": str(telegram_id)},
            )

        if resp.status_code == 200:
            status_text = "✅ Aktiv" if new_status else "❌ Nofaol"
            await callback.answer(
                f"Holat o'zgartirildi: {status_text}",
                show_alert=True,
            )
            # Sahifani yangilash
            p = resp.json()
            name = p.get("name_uz") or "Mahsulot"
            price = _to_price(p.get("base_price", 0))
            weight = p.get("weight_grams", 0)
            text = (
                f"📦 <b>{name}</b>\n\n"
                f"💰 Narx: <b>{price:,.0f} so'm</b>\n"
                f"⚖️ Og'irlik: {weight} g\n"
                f"📊 Holat: {status_text}\n"
                f"🆔 ID: {product_id}"
            )
            if callback.message:
                await callback.message.edit_text(
                    text,
                    parse_mode="HTML",
                    reply_markup=product_detail_keyboard(product_id, new_status),
                )
        else:
            await callback.answer("❌ Xatolik", show_alert=True)

    except Exception as exc:
        logger.error("toggle_active: %s", exc)
        await callback.answer("❌ Server xatolik", show_alert=True)


# ─── MAHSULOT O'CHIRISH ──────────────────────────────────────────────


@router.callback_query(F.data.startswith("prod_delete:"))
async def delete_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    product_id = int((callback.data or "").split(":")[1])
    await state.update_data(product_id=product_id)

    if callback.message:
        await callback.message.answer(
            f"🗑 <b>Mahsulotni o'chirmoqchimisiz?</b>\n\n"
            f"ID: {product_id}\n\n"
            f"⚠️ Bu amalni qaytarib bo'lmaydi!",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✅ Ha, o'chirish",
                            callback_data=f"prod_delete_yes:{product_id}",
                        ),
                        InlineKeyboardButton(
                            text="❌ Bekor qilish",
                            callback_data=f"prod_detail:{product_id}",
                        ),
                    ]
                ]
            ),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("prod_delete_yes:"))
async def delete_execute(callback: CallbackQuery, state: FSMContext) -> None:
    product_id = int((callback.data or "").split(":")[1])
    telegram_id = callback.from_user.id

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{BACKEND}/admin/products/{product_id}",
                headers={"X-Telegram-Id": str(telegram_id)},
            )

        if callback.message:
            if resp.status_code == 200:
                await callback.message.edit_text(
                    f"✅ Mahsulot #{product_id} muvaffaqiyatli o'chirildi!"
                )
            elif resp.status_code == 403:
                await callback.message.edit_text(
                    "❌ Bu mahsulot sizga tegishli emas!"
                )
            elif resp.status_code == 404:
                await callback.message.edit_text(
                    "❌ Mahsulot topilmadi!"
                )
            else:
                await callback.message.edit_text(
                    f"❌ Xatolik: {resp.text}"
                )

    except Exception as exc:
        logger.error("delete_execute: %s", exc)
        await callback.answer("❌ Server xatolik", show_alert=True)

    await state.clear()
    await callback.answer()

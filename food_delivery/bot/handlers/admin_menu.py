from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx
from aiogram import F, Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from app.core.config import settings

router = Router()
BACKEND = "http://localhost:8000/api/v1"
BASE_DIR = Path(__file__).resolve().parents[2]


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


def _append_tg_user_id(url: str, telegram_id: int | None) -> str:
    raw = (url or "").strip()
    if not raw or telegram_id is None:
        return raw
    try:
        tid = str(int(telegram_id))
    except (TypeError, ValueError):
        return raw
    try:
        parsed = urlsplit(raw)
        query_pairs = [
            (key, value)
            for key, value in parse_qsl(parsed.query, keep_blank_values=True)
            if key != "tg_user_id"
        ]
        query_pairs.append(("tg_user_id", tid))
        normalized = parsed._replace(query=urlencode(query_pairs))
        return urlunsplit(normalized)
    except Exception:
        joiner = "&" if "?" in raw else "?"
        return f"{raw}{joiner}tg_user_id={tid}"


def _admin_orders_url(telegram_id: int | None = None) -> str:
    base = _resolve_webapp_url().rstrip("/")
    if not base:
        return ""
    return _append_tg_user_id(f"{base}/admin/orders", telegram_id)


def _safe_text(resp: httpx.Response) -> str:
    text = (resp.text or "").strip()
    if not text:
        return f"HTTP {resp.status_code}"
    return text[:300]


def _as_float(value: Any) -> float:
    try:
        return float(str(value).replace(" ", "").replace(",", ""))
    except Exception:
        return 0.0


def _status_label(status: str) -> str:
    mapping = {
        "pending": "Yangi",
        "in_progress": "Jarayonda",
        "delivered": "Yetkazilgan",
        "cancelled": "Bekor qilingan",
    }
    return mapping.get((status or "").lower(), status or "Noma'lum")


def _status_emoji(status: str) -> str:
    mapping = {
        "pending": "🟡",
        "in_progress": "🔵",
        "delivered": "🟢",
        "cancelled": "🔴",
    }
    return mapping.get((status or "").lower(), "⚪")


def _format_datetime(value: str | None) -> str:
    if not value:
        return "—"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.strftime("%d.%m %H:%M")
    except Exception:
        return value


@router.message(F.text == "📁 Kategoriyalarim")
async def my_categories(message: Message) -> None:
    telegram_id = message.from_user.id if message.from_user else 0
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND}/admin/categories",
                headers={"X-Telegram-Id": str(telegram_id)},
            )
        if resp.status_code != 200:
            await message.answer(f"❌ Kategoriyalarni olishda xatolik: {_safe_text(resp)}")
            return

        categories = resp.json()
        if not isinstance(categories, list) or not categories:
            await message.answer("📁 Sizda hozircha kategoriya yo'q.")
            return

        lines = [f"📁 <b>Kategoriyalarim</b> ({len(categories)} ta):", ""]
        for category in categories[:40]:
            name = category.get("name_uz") or category.get("name_ru") or "Nomsiz"
            status = "✅" if category.get("is_active", True) else "❌"
            cid = category.get("id", "—")
            sort = category.get("sort_order", 0)
            lines.append(f"{status} <b>{name}</b> • ID: <code>{cid}</code> • sort: {sort}")

        if len(categories) > 40:
            lines.append("")
            lines.append(f"... va yana {len(categories) - 40} ta kategoriya")

        await message.answer("\n".join(lines), parse_mode="HTML")
    except Exception as exc:  # noqa: BLE001
        await message.answer(f"❌ Server xatoligi: {exc}")


@router.message(F.text == "📋 Buyurtmalar")
async def my_admin_orders(message: Message) -> None:
    telegram_id = message.from_user.id if message.from_user else 0
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND}/admin/orders?page=1&size=30",
                headers={"X-Telegram-Id": str(telegram_id)},
            )
        if resp.status_code != 200:
            await message.answer(f"❌ Buyurtmalarni olishda xatolik: {_safe_text(resp)}")
            return

        payload = resp.json() if isinstance(resp.json(), dict) else {}
        items = payload.get("items", []) if isinstance(payload, dict) else []
        total = int(payload.get("total", 0)) if isinstance(payload, dict) else 0

        if not items:
            await message.answer("📋 Hozircha buyurtmalar yo'q.")
            return

        counts = {"pending": 0, "in_progress": 0, "delivered": 0, "cancelled": 0}
        for item in items:
            status = str(item.get("status", "")).lower()
            if status in counts:
                counts[status] += 1

        lines = [
            "📋 <b>Buyurtmalar</b>",
            f"Jami: <b>{total}</b>",
            f"🟡 Yangi: <b>{counts['pending']}</b>  •  🔵 Jarayonda: <b>{counts['in_progress']}</b>",
            f"🟢 Yetkazilgan: <b>{counts['delivered']}</b>  •  🔴 Bekor: <b>{counts['cancelled']}</b>",
            "",
            "<b>So'nggi buyurtmalar:</b>",
        ]

        for order in items[:10]:
            oid = order.get("id", "—")
            status = str(order.get("status", ""))
            total_amount = _as_float(order.get("total_amount", 0))
            created_at = _format_datetime(order.get("created_at"))
            lines.append(
                f"{_status_emoji(status)} <b>#{oid}</b> {_status_label(status)} • {total_amount:,.0f} so'm • {created_at}"
            )

        admin_orders_url = _admin_orders_url(telegram_id)
        kb = None
        if admin_orders_url.startswith("https://"):
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🌐 Buyurtmalarni WebApp'da ochish",
                            web_app=WebAppInfo(url=admin_orders_url),
                        )
                    ]
                ]
            )

        await message.answer("\n".join(lines), parse_mode="HTML", reply_markup=kb)
    except Exception as exc:  # noqa: BLE001
        await message.answer(f"❌ Server xatoligi: {exc}")


@router.message(F.text == "👤 Profil")
async def show_profile(message: Message) -> None:
    telegram_id = message.from_user.id if message.from_user else 0
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND}/profile",
                headers={"X-Telegram-Id": str(telegram_id)},
            )
        if resp.status_code != 200:
            await message.answer(f"❌ Profilni olishda xatolik: {_safe_text(resp)}")
            return

        profile = resp.json() if isinstance(resp.json(), dict) else {}
        full_name = profile.get("full_name") or "Foydalanuvchi"
        username = profile.get("username")
        phone = profile.get("phone")
        language = profile.get("language") or "uz"
        is_admin = bool(profile.get("is_admin"))
        is_superadmin = bool(profile.get("is_superadmin"))
        is_active = bool(profile.get("is_active", True))

        if is_superadmin:
            role = "Superadmin"
        elif is_admin:
            role = "Admin"
        else:
            role = "Foydalanuvchi"

        lines = [
            "👤 <b>Profil</b>",
            "",
            f"Ism: <b>{full_name}</b>",
            f"Telegram ID: <code>{telegram_id}</code>",
            f"Rol: <b>{role}</b>",
            f"Holat: {'✅ Faol' if is_active else '❌ Nofaol'}",
            f"Til: <b>{language}</b>",
        ]
        if username:
            lines.append(f"Username: <b>@{username}</b>")
        if phone:
            lines.append(f"Telefon: <b>{phone}</b>")

        await message.answer("\n".join(lines), parse_mode="HTML")
    except Exception as exc:  # noqa: BLE001
        await message.answer(f"❌ Server xatoligi: {exc}")

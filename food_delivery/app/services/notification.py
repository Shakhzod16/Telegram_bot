from __future__ import annotations

import json
from datetime import datetime
from html import escape
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.models.order import Order

logger = get_logger(__name__)


class NotificationService:
    async def send_order_confirmation(self, telegram_id: int, order: Order) -> None:
        text = self._format_order_message(order)
        await self._send_telegram_message(telegram_id, text)

    async def send_status_update(self, telegram_id: int, status: str) -> None:
        messages = {
            "in_progress": "🚴 Buyurtmangiz yo'lda!",
            "delivered": "🎉 Buyurtma yetkazildi! Marhamat!",
            "cancelled": "❌ Buyurtma bekor qilindi.",
        }
        msg = messages.get(status)
        if not msg:
            return
        await self._send_telegram_message(telegram_id, msg)

    async def notify_courier_group(self, order: Order) -> bool:
        """
        Send newly created order details into configured courier group.
        """
        if not settings.courier_group_id:
            return False

        items_text_parts: list[str] = []
        for item in order.items:
            snapshot = item.snapshot_json or {}
            name = (
                snapshot.get("product_name_uz")
                or snapshot.get("product_name")
                or "Mahsulot"
            )
            variant = (
                snapshot.get("variant_name_uz")
                or snapshot.get("variant_name")
                or ""
            )
            variant_str = f" ({variant})" if variant else ""
            items_text_parts.append(
                f"  • {name}{variant_str} × {item.quantity} — {int(item.total_price):,} so'm"
            )
        items_text = "\n".join(items_text_parts) if items_text_parts else "  • Mahsulotlar topilmadi"

        address_text = "Manzil ko'rsatilmagan"
        manual_text = (getattr(order, "delivery_address_text", None) or "").strip()
        if manual_text:
            address_text = manual_text

        user = order.user
        user_name = "Noma'lum"
        user_phone = "Telefon yo'q"
        if user:
            first_name = user.first_name or ""
            last_name = user.last_name or ""
            full_name = (first_name + " " + last_name).strip()
            user_name = full_name or "Noma'lum"
            user_phone = user.phone or "Telefon yo'q"

        created_at = order.created_at
        if isinstance(created_at, datetime):
            created_at_text = created_at.strftime("%H:%M — %d.%m.%Y")
        else:
            created_at_text = "vaqt noma'lum"

        text = (
            f"🆕 <b>YANGI BUYURTMA #{order.id}</b>\n"
            f"{'━' * 28}\n\n"
            f"📦 <b>Buyurtma tarkibi:</b>\n"
            f"{items_text}\n\n"
            f"{'─' * 28}\n"
            f"🛍 Jami:      <b>{int(order.subtotal):,} so'm</b>\n"
            f"🚚 Yetkazish: <b>{int(order.delivery_fee):,} so'm</b>\n"
        )

        if order.discount and order.discount > 0:
            text += f"🎁 Chegirma:  <b>-{int(order.discount):,} so'm</b>\n"

        text += (
            f"💰 <b>TO'LOV: {int(order.total_amount):,} so'm</b>  ({order.payment_method})\n\n"
            f"{'━' * 28}\n"
            f"👤 <b>Mijoz:</b> {user_name}\n"
            f"📱 <b>Tel:</b> {user_phone}\n"
            f"📍 <b>Manzil:</b>\n  {address_text}\n"
        )

        if order.comment:
            text += f"\n💬 <b>Izoh:</b> {order.comment}\n"

        text += f"\n⏰ {created_at_text}"

        latitude = getattr(order, "latitude", None)
        longitude = getattr(order, "longitude", None)

        map_url = (getattr(order, "maps_url", None) or "").strip()
        if not map_url and latitude is not None and longitude is not None:
            map_url = f"https://maps.google.com/?q={latitude},{longitude}"
        if not map_url:
            map_url = "https://maps.google.com"

        call_url = "https://t.me"
        if user_phone != "Telefon yo'q":
            call_url = f"tel:{user_phone}"

        keyboard: dict[str, Any] = {
            "inline_keyboard": [
                [
                    {"text": "✅ Qabul qildim", "callback_data": f"courier_accept_{order.id}"},
                    {"text": "🗺 Xaritada ko'r", "url": escape(map_url, quote=True)},
                ],
                [
                    {"text": "📞 Mijozga qo'ng'iroq", "url": call_url},
                ],
            ]
        }

        sent = await self._send_message(
            chat_id=int(settings.courier_group_id),
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        if sent and latitude is not None and longitude is not None:
            await self._send_location(
                chat_id=int(settings.courier_group_id),
                latitude=float(latitude),
                longitude=float(longitude),
            )
        return sent

    def _format_order_message(self, order: Order) -> str:
        lines: list[str] = [
            "✅ Buyurtma qabul qilindi!",
            "",
            f"📋 Buyurtma #{order.id}",
            "━━━━━━━━━━━━━━━━",
        ]
        for it in order.items:
            name = (it.snapshot_json or {}).get("product_name", "Mahsulot")
            lines.append(f"🍽 {name} x{it.quantity} — {it.total_price:,.0f} so'm")
        lines.append("━━━━━━━━━━━━━━━━")
        lines.append(f"Jami: {order.subtotal:,.0f} so'm")
        lines.append(f"Yetkazish: {order.delivery_fee:,.0f} so'm")
        lines.append(f"💰 To'lash: {order.total_amount:,.0f} so'm (naqd)")
        lines.append("")
        lines.append("📍 Manzil: yetkaziladi")
        lines.append("⏱ Taxminiy vaqt: 30-45 daqiqa")
        return "\n".join(lines)

    async def _send_telegram_message(self, telegram_id: int, text: str) -> None:
        await self._send_message(chat_id=telegram_id, text=text, parse_mode=None)

    async def _send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str | None = "HTML",
        reply_markup: dict[str, Any] | None = None,
    ) -> bool:
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup is not None:
            payload["reply_markup"] = json.dumps(reply_markup, ensure_ascii=False)

        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code >= 400:
                    logger.warning(
                        "telegram_send_failed %s %s",
                        response.status_code,
                        response.text[:500],
                    )
                    return False
                return True
        except Exception as exc:
            logger.warning("telegram_send_error %s", str(exc))
            return False

    async def _send_location(
        self,
        *,
        chat_id: int,
        latitude: float,
        longitude: float,
    ) -> bool:
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "latitude": latitude,
            "longitude": longitude,
        }
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendLocation"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code >= 400:
                    logger.warning(
                        "telegram_send_location_failed %s %s",
                        response.status_code,
                        response.text[:500],
                    )
                    return False
                return True
        except Exception as exc:
            logger.warning("telegram_send_location_error %s", str(exc))
            return False

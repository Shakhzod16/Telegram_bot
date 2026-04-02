# -*- coding: utf-8 -*-
from __future__ import annotations

from telegram import Bot

from backend.models import Order
from utils.logger import get_logger


class NotificationService:
    def __init__(self, bot_token: str, admin_chat_id: int) -> None:
        self.bot_token = bot_token
        self.admin_chat_id = admin_chat_id
        self.log = get_logger("backend.services.notification")

    @staticmethod
    def _location_map_link(order: Order) -> str | None:
        if order.latitude is None or order.longitude is None:
            return None
        return f"https://maps.google.com/?q={order.latitude},{order.longitude}"

    async def notify_user(self, telegram_user_id: int, message: str) -> None:
        if not self.bot_token or not telegram_user_id:
            return
        try:
            async with Bot(self.bot_token) as bot:
                await bot.send_message(chat_id=telegram_user_id, text=message)
        except Exception as exc:  # pragma: no cover
            self.log.error("notify_user_failed user_id=%s error=%s", telegram_user_id, str(exc))

    async def notify_admin(self, order: Order) -> None:
        if not self.bot_token or not self.admin_chat_id:
            return
        if not order.user:
            return

        lines = [
            f"New order #{order.id}",
            f"User: {order.user.first_name or '-'}",
            f"Phone: {order.user.phone or '-'}",
            f"Total: {order.total_amount} UZS",
            f"Location: {order.location_label or '-'}",
            "",
            "Items:",
        ]
        for item in order.items:
            lines.append(f"- {item.product_name} x{item.quantity} = {item.total_price}")

        maps = self._location_map_link(order)
        if maps:
            lines.extend(["", maps])

        try:
            async with Bot(self.bot_token) as bot:
                await bot.send_message(chat_id=self.admin_chat_id, text="\n".join(lines))
        except Exception as exc:  # pragma: no cover
            self.log.error("notify_admin_failed order_id=%s error=%s", order.id, str(exc))

    async def notify_status_change(self, order: Order, telegram_user_id: int) -> None:
        await self.notify_user(telegram_user_id, f"Order #{order.id} status: {order.status}")

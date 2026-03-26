# -*- coding: utf-8 -*-
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from config import settings
from database.models import Database
from utils.keyboards import main_menu_keyboard
from utils.texts import status_text, t


db = Database(settings.database_path)


def _history_message(language: str, orders: list[dict]) -> str:
    lines = [t("history_title", language), ""]
    for order in orders:
        emoji = {
            "DELIVERED": "✅",
            "CANCELLED": "❌",
            "PAID": "💳",
            "DELIVERING": "🚚",
            "IN_PROGRESS": "🍳",
        }.get(order["status"], "⏳")
        lines.append(
            f"{emoji} #{order['id']} — {order['created_at'][:10]} — "
            f"{order['total_amount']:,} so'm — {status_text(order['status'], language)}"
        )
    return "\n".join(lines)


async def order_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_message or not update.effective_user:
        return

    user = db.get_user(update.effective_user.id)
    language = user["language"] if user else "en"
    orders = db.get_user_orders(update.effective_user.id, limit=5)

    if not orders:
        await update.effective_message.reply_text(
            t("history_empty", language),
            reply_markup=main_menu_keyboard(language),
        )
        return

    await update.effective_message.reply_text(
        _history_message(language, orders),
        reply_markup=main_menu_keyboard(language),
    )


def register_history_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("history", order_history))
    application.add_handler(
        MessageHandler(filters.Regex(r"^📜"), order_history),
        group=10,
    )

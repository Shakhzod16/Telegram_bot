# -*- coding: utf-8 -*-
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from config import settings
from database.models import Database
from bot.keyboards import main_menu_keyboard
from utils.texts import LANGUAGE_CODES, status_text, t


db = Database(settings.database_path)


def _history_message(language: str, orders: list[dict]) -> str:
    lines = [t("history_title", language), ""]
    for order in orders:
        status_value = str(order["status"]).upper()
        emoji = {
            "DELIVERED": "OK",
            "CANCELLED": "X",
            "PAID": "$",
            "DELIVERING": "->",
            "IN_PROGRESS": "...",
            "PREPARING": "...",
            "CONFIRMED": "+",
        }.get(status_value, "...")
        lines.append(
            f"{emoji} #{order['id']} - {order['created_at'][:10]} - "
            f"{order['total_amount']:,} so'm - {status_text(status_value, language)}"
        )
    return "\n".join(lines)


def _reorder_url(order_id: int) -> str:
    delimiter = "&" if "?" in settings.web_app_url else "?"
    return f"{settings.web_app_url}{delimiter}reorder_order_id={order_id}"


def _reorder_keyboard(language: str, orders: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for order in orders:
        rows.append(
            [
                InlineKeyboardButton(
                    t("history_reorder_button", language, order_id=str(order["id"])),
                    web_app=WebAppInfo(url=_reorder_url(int(order["id"]))),
                )
            ]
        )
    return InlineKeyboardMarkup(rows)


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
    await update.effective_message.reply_text(
        t("history_reorder_title", language),
        reply_markup=_reorder_keyboard(language, orders),
    )


async def history_button_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    labels = {t("history_button", language) for language in LANGUAGE_CODES}
    if (update.message.text or "").strip() not in labels:
        return
    await order_history(update, context)


def register_history_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("history", order_history))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, history_button_entry),
        group=10,
    )

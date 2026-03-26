# -*- coding: utf-8 -*-
import json

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from config import settings
from database.models import Database
from utils.keyboards import main_menu_keyboard
from utils.texts import status_text, t


db = Database(settings.database_path)


def _format_order(summary: dict, language: str) -> str:
    lines = [
        t("order_received", language),
        t("order_status", language, status=status_text(summary["status"], language)),
        t("location_label", language, location=summary["location_label"] or "-"),
        "",
        t("order_items", language),
    ]
    for item in summary["items"]:
        lines.append(f"- {item['name']} x{item['quantity']} = {item['total_price']} so'm")
    lines.append("")
    lines.append(t("order_total", language, amount=str(summary["total_amount"])))
    if summary["payments"]:
        lines.append(t("payment_ready", language))
        for payment in summary["payments"]:
            lines.append(f"{payment['provider'].upper()}: {payment['status']}")
    return "\n".join(lines)


def _format_direct_payload(payload: dict, language: str) -> str:
    items = payload.get("items", [])
    total = payload.get("total", 0)

    lines = [
        t("order_received", language),
        "",
        t("order_items", language),
    ]
    for item in items:
        name = item.get("name", "Item")
        quantity = item.get("quantity", 1)
        line_total = item.get("total_price") or item.get("price") or 0
        lines.append(f"- {name} x{quantity} = {line_total} so'm")
    lines.append("")
    lines.append(t("order_total", language, amount=str(total)))
    return "\n".join(lines)


async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.web_app_data or not update.effective_user:
        return

    user = db.get_user(update.effective_user.id)
    language = user["language"] if user else "en"

    try:
        payload = json.loads(update.message.web_app_data.data)
    except json.JSONDecodeError:
        await update.message.reply_text(
            t("error_generic", language),
            reply_markup=main_menu_keyboard(language),
        )
        return

    order_id = payload.get("order_id")
    if not order_id:
        items = payload.get("items", [])
        if not items:
            await update.message.reply_text(
                t("empty_cart", language),
                reply_markup=main_menu_keyboard(language),
            )
            return
        await update.message.reply_text(
            _format_direct_payload(payload, language),
            reply_markup=main_menu_keyboard(language),
        )
        return

    summary = db.get_order_summary(int(order_id))
    await update.message.reply_text(
        _format_order(summary, language),
        reply_markup=main_menu_keyboard(language),
    )

    if settings.admin_chat_id:
        admin_lines = [
            f"📦 New order #{summary['order_id']}",
            f"User: {summary['user']['name']} ({summary['user']['phone']})",
            f"City: {summary['user']['city']}",
            f"Total: {summary['total_amount']} UZS",
            f"Status: {summary['status']}",
        ]
        for item in summary["items"]:
            admin_lines.append(f"- {item['name']} x{item['quantity']}")
        if summary["maps_url"]:
            admin_lines.append(summary["maps_url"])
        await context.bot.send_message(settings.admin_chat_id, "\n".join(admin_lines))


def register_webapp_handlers(application: Application) -> None:
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))

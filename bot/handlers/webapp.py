# -*- coding: utf-8 -*-
import json

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from config import settings
from database.models import Database
from bot.keyboards import main_menu_keyboard
from utils.logger import get_logger
from utils.texts import status_text, t


db = Database(settings.database_path)
logger = get_logger("bot.webapp")


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
        name = item.get("name", t("frontend_address_label_default", language))
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
        logger.error("Invalid WebApp payload user_id=%s", update.effective_user.id, exc_info=True)
        await update.message.reply_text(
            t("error_generic", language),
            reply_markup=main_menu_keyboard(language),
        )
        return

    logger.info(
        "WebApp payload received user_id=%s has_order_id=%s",
        update.effective_user.id,
        bool(payload.get("order_id")),
    )
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
    if summary["payments"]:
        providers = ",".join(payment["provider"] for payment in summary["payments"])
        logger.info("Payment update for order_id=%s providers=%s", order_id, providers)
    logger.info("Order summary sent to user order_id=%s user_id=%s", order_id, update.effective_user.id)
    await update.message.reply_text(
        _format_order(summary, language),
        reply_markup=main_menu_keyboard(language),
    )

    if settings.admin_chat_id:
        admin_lines = [
            t("bot_admin_new_order", "en", order_id=str(summary["order_id"])),
            t("bot_admin_user", "en", name=summary["user"]["name"], phone=summary["user"]["phone"]),
            t("bot_admin_city", "en", city=summary["user"]["city"]),
            t("bot_admin_total", "en", amount=str(summary["total_amount"])),
            t("bot_admin_status", "en", status=summary["status"]),
        ]
        for item in summary["items"]:
            admin_lines.append(f"- {item['name']} x{item['quantity']}")
        if summary["maps_url"]:
            admin_lines.append(summary["maps_url"])
        logger.info("Admin notified about order order_id=%s", summary["order_id"])
        await context.bot.send_message(settings.admin_chat_id, "\n".join(admin_lines))


def register_webapp_handlers(application: Application) -> None:
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))

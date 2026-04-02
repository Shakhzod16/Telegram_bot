# -*- coding: utf-8 -*-
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from config import settings
from database.models import MANAGEABLE_ORDER_STATUSES, Database
from utils.texts import status_text, t


db = Database(settings.database_path)


def _is_admin(user_id: int | None) -> bool:
    return bool(user_id and settings.admin_chat_id and user_id == settings.admin_chat_id)


async def _notify_status_change(context: ContextTypes.DEFAULT_TYPE, order_id: int, status: str) -> None:
    summary = db.get_order_summary(order_id)
    language = summary["user"]["language"]
    await context.bot.send_message(
        chat_id=summary["user"]["id"],
        text=t("status_changed", language, order_id=str(order_id), status=status_text(status, language)),
    )


async def admin_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_message or not update.effective_user:
        return
    if not _is_admin(update.effective_user.id):
        await update.effective_message.reply_text(t("admin_only", "en"))
        return

    orders = db.get_recent_orders(limit=10)
    if not orders:
        await update.effective_message.reply_text(t("admin_no_orders", "en"))
        return

    lines = [t("admin_orders_title", "en"), ""]
    keyboard = []
    for order in orders:
        lines.append(
            f"#{order['id']} - {order['user_name']} - {order['total_amount']:,} so'm - {order['status']}"
        )
        keyboard.append(
            [
                InlineKeyboardButton(
                    t("admin_order_manage", "en", order_id=str(order["id"])),
                    callback_data=f"admin_order_{order['id']}",
                )
            ]
        )

    await update.effective_message.reply_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def admin_order_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.from_user:
        return
    if not _is_admin(query.from_user.id):
        await query.answer(t("admin_forbidden", "en"), show_alert=True)
        return

    order_id = int((query.data or "").split("_")[-1])
    summary = db.get_order_summary(order_id)
    keyboard = [
        [InlineKeyboardButton(t("admin_confirm", "en"), callback_data=f"status_{order_id}_CONFIRMED")],
        [InlineKeyboardButton(t("admin_preparing", "en"), callback_data=f"status_{order_id}_IN_PROGRESS")],
        [InlineKeyboardButton(t("admin_delivering", "en"), callback_data=f"status_{order_id}_DELIVERING")],
        [InlineKeyboardButton(t("admin_delivered", "en"), callback_data=f"status_{order_id}_DELIVERED")],
        [InlineKeyboardButton(t("admin_cancel", "en"), callback_data=f"status_{order_id}_CANCELLED")],
    ]
    items = "\n".join(f"- {item['name']} x{item['quantity']}" for item in summary["items"])
    text = t(
        "admin_order_detail",
        "en",
        order_id=str(order_id),
        name=summary["user"]["name"] or "-",
        phone=summary["user"]["phone"] or "-",
        city=summary["user"]["city"] or "-",
        address=summary["location_label"] or "-",
        amount=f"{summary['total_amount']:,}",
        status=status_text(summary["status"], "en"),
        items=items or "-",
    )
    await query.answer()
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_status_change(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.from_user:
        return
    if not _is_admin(query.from_user.id):
        await query.answer(t("admin_forbidden", "en"), show_alert=True)
        return

    _, order_id_raw, status = (query.data or "").split("_", 2)
    order_id = int(order_id_raw)
    if status not in MANAGEABLE_ORDER_STATUSES:
        await query.answer(t("admin_invalid_status", "en"), show_alert=True)
        return

    db.update_order_status(order_id, status)
    await _notify_status_change(context, order_id, status)
    await query.answer(t("admin_updated", "en"))
    await query.edit_message_reply_markup(reply_markup=None)
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=t("status_action_success", "en", order_id=str(order_id)),
    )


def register_admin_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("orders", admin_orders))
    application.add_handler(CallbackQueryHandler(admin_order_detail, pattern=r"^admin_order_\d+$"))
    application.add_handler(CallbackQueryHandler(handle_status_change, pattern=r"^status_\d+_[A-Z_]+$"))

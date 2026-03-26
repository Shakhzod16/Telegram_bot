# -*- coding: utf-8 -*-
from telegram import ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from config import settings
from database.models import Database
from utils.keyboards import LANGUAGE_BUTTONS, language_keyboard, main_menu_keyboard, phone_keyboard
from utils.texts import LANGUAGE_CODES, t


db = Database(settings.database_path)

LANGUAGE, NAME, PHONE, CITY = range(4)


def get_user_language(user_id: int) -> str:
    user = db.get_user(user_id)
    return user["language"] if user else "en"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.effective_message or not update.effective_user:
        return ConversationHandler.END

    user = db.get_user(update.effective_user.id)
    if user and user.get("name") and user.get("phone") and user.get("city"):
        context.user_data["profile"] = user
        language = user["language"]
        await update.effective_message.reply_text(
            "\n".join(
                [
                    t("welcome_back", language, name=user["name"]),
                    t(
                        "profile_summary",
                        language,
                        name=user["name"],
                        phone=user["phone"],
                        city=user["city"],
                    ),
                ]
            ),
            reply_markup=main_menu_keyboard(language),
        )
        return ConversationHandler.END

    context.user_data.clear()
    await update.effective_message.reply_text(
        t("choose_language", "en"),
        reply_markup=language_keyboard("en"),
    )
    return LANGUAGE


async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.effective_message or not update.effective_user:
        return ConversationHandler.END

    language = get_user_language(update.effective_user.id)
    await update.effective_message.reply_text(
        t("choose_language", language),
        reply_markup=language_keyboard(language),
    )
    context.user_data["changing_language"] = True
    return LANGUAGE


async def receive_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.effective_user:
        return LANGUAGE

    language = LANGUAGE_BUTTONS.get((update.message.text or "").strip())
    if language not in LANGUAGE_CODES:
        await update.message.reply_text(
            t("choose_language", "en"),
            reply_markup=language_keyboard("en"),
        )
        return LANGUAGE

    user = db.get_user(update.effective_user.id)
    if context.user_data.get("changing_language") and user:
        updated_user = db.upsert_user(update.effective_user.id, language=language)
        context.user_data["profile"] = updated_user
        context.user_data.pop("changing_language", None)
        await update.message.reply_text(
            t("language_changed", language),
            reply_markup=main_menu_keyboard(language),
        )
        return ConversationHandler.END

    context.user_data["profile"] = {"language": language}
    await update.message.reply_text(
        t("ask_name", language),
        reply_markup=ReplyKeyboardRemove(),
    )
    return NAME


async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return NAME

    profile = context.user_data.setdefault("profile", {"language": "en"})
    language = profile["language"]
    name = (update.message.text or "").strip()
    if not name:
        await update.message.reply_text(t("invalid_name", language))
        return NAME

    profile["name"] = name
    await update.message.reply_text(
        t("ask_phone", language),
        reply_markup=phone_keyboard(language),
    )
    return PHONE


async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return PHONE

    profile = context.user_data.setdefault("profile", {"language": "en"})
    language = profile["language"]
    if not update.message.contact:
        await update.message.reply_text(
            t("invalid_phone", language),
            reply_markup=phone_keyboard(language),
        )
        return PHONE

    profile["phone"] = update.message.contact.phone_number
    await update.message.reply_text(
        t("ask_city", language),
        reply_markup=ReplyKeyboardRemove(),
    )
    return CITY


async def prompt_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return PHONE

    language = context.user_data.get("profile", {}).get("language", "en")
    await update.message.reply_text(
        t("invalid_phone", language),
        reply_markup=phone_keyboard(language),
    )
    return PHONE


async def receive_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.effective_user:
        return CITY

    profile = context.user_data.setdefault("profile", {"language": "en"})
    language = profile["language"]
    city = (update.message.text or "").strip()
    if not city:
        await update.message.reply_text(t("invalid_city", language))
        return CITY

    profile["city"] = city
    saved = db.upsert_user(
        update.effective_user.id,
        name=profile["name"],
        phone=profile["phone"],
        city=profile["city"],
        language=language,
    )
    context.user_data["profile"] = saved

    await update.message.reply_text(
        "\n".join(
            [
                t("onboarding_complete", language),
                t(
                    "profile_summary",
                    language,
                    name=saved["name"],
                    phone=saved["phone"],
                    city=saved["city"],
                ),
            ]
        ),
        reply_markup=main_menu_keyboard(language),
    )
    await update.message.reply_text(
        t("menu_hint", language),
        reply_markup=main_menu_keyboard(language),
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_message and update.effective_user:
        language = get_user_language(update.effective_user.id)
        user = db.get_user(update.effective_user.id)
        await update.effective_message.reply_text(
            t("cancelled", language),
            reply_markup=main_menu_keyboard(language) if user else ReplyKeyboardRemove(),
        )
    return ConversationHandler.END


async def persistent_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return

    user = db.get_user(update.effective_user.id)
    if not user or context.user_data.get("changing_language"):
        return

    text = (update.message.text or "").strip()
    ignored_prefixes = ("🌐", "🍔", "📜")
    if update.message.web_app_data or any(text.startswith(prefix) for prefix in ignored_prefixes):
        return

    await update.message.reply_text(
        t("menu_hint", user["language"]),
        reply_markup=main_menu_keyboard(user["language"]),
    )


def register_onboarding_handlers(application: Application) -> None:
    application.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler("start", start),
                MessageHandler(filters.Regex(r"^🌐"), change_language),
            ],
            states={
                LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_language)],
                NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
                PHONE: [
                    MessageHandler(filters.CONTACT, receive_phone),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, prompt_contact),
                ],
                CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_city)],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
            allow_reentry=True,
        )
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, persistent_menu),
        group=90,
    )

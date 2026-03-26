# -*- coding: utf-8 -*-
import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes

from bot.handlers.admin import register_admin_handlers
from bot.handlers.history import register_history_handlers
from bot.handlers.onboarding import db, get_user_language, register_onboarding_handlers
from bot.handlers.webapp import register_webapp_handlers
from config import settings
from utils.texts import t


def configure_logging() -> None:
    logging.basicConfig(
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.getLogger(__name__).exception("Unhandled bot exception.", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        language = get_user_language(update.effective_user.id) if update.effective_user else "en"
        await update.effective_message.reply_text(t("error_generic", language))


def main() -> None:
    configure_logging()
    db.init()
    application = ApplicationBuilder().token(settings.bot_token).build()
    register_onboarding_handlers(application)
    register_webapp_handlers(application)
    register_history_handlers(application)
    register_admin_handlers(application)
    application.add_error_handler(error_handler)
    application.run_polling()


if __name__ == "__main__":
    main()

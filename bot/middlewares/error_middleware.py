# -*- coding: utf-8 -*-
from telegram import Update
from telegram.ext import Application, ContextTypes

from utils.logger import get_logger
from utils.texts import t


logger = get_logger("bot.error_middleware")


async def handle_bot_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Unhandled bot exception.", exc_info=context.error)
    if not isinstance(update, Update):
        return
    if not update.effective_message:
        return

    language = "en"
    if update.effective_user:
        try:
            from bot.handlers.onboarding import get_user_language

            language = get_user_language(update.effective_user.id)
        except Exception:
            logger.error("Failed to resolve user language from onboarding DB.", exc_info=True)

    await update.effective_message.reply_text(t("error_generic", language))


def register_error_middleware(application: Application) -> None:
    application.add_error_handler(handle_bot_error)

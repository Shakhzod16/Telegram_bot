# -*- coding: utf-8 -*-
from telegram.ext import ApplicationBuilder

from bot.handlers.admin import register_admin_handlers
from bot.handlers.history import register_history_handlers
from bot.handlers.onboarding import db, register_onboarding_handlers
from bot.handlers.webapp import register_webapp_handlers
from bot.middlewares.error_middleware import register_error_middleware
from config import settings
from utils.logger import get_logger, setup_logging


logger = get_logger("bot.main")


def main() -> None:
    setup_logging(settings.environment, settings.log_level)
    logger.info("Bot startup mode=%s", settings.bot_mode)
    db.init()
    application = ApplicationBuilder().token(settings.bot_token).build()
    register_onboarding_handlers(application)
    register_webapp_handlers(application)
    register_history_handlers(application)
    register_admin_handlers(application)
    register_error_middleware(application)

    if settings.bot_mode == "webhook":
        if not settings.webhook_url:
            raise RuntimeError("WEBHOOK_URL is required when BOT_MODE=webhook.")
        url_path = settings.webhook_path.lstrip("/")
        webhook_url = f"{settings.webhook_url.rstrip('/')}/{url_path}"
        application.run_webhook(
            listen=settings.webhook_listen,
            port=settings.webhook_port,
            url_path=url_path,
            webhook_url=webhook_url,
            drop_pending_updates=True,
            secret_token=settings.webhook_secret or None,
        )
        logger.info("Bot started in webhook mode.")
        return

    logger.info("Bot started in polling mode.")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

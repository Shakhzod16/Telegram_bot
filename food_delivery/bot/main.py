import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.core.config import settings
from bot.handlers.courier import router as courier_router
from bot.handlers.notifications import router as notifications_router
from bot.handlers.start import router as start_router
from bot.handlers.superadmin import router as superadmin_router
from bot.middlewares.logging import LoggingMiddleware

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    bot = Bot(
        settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.update.middleware(LoggingMiddleware())
    dp.include_router(superadmin_router)
    dp.include_router(start_router)
    dp.include_router(notifications_router)
    dp.include_router(courier_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

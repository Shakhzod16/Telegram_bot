import asyncio
import logging
import os
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import MenuButtonWebApp, WebAppInfo

from app.core.config import settings
from bot.handlers.admin_products import router as admin_products_router
from bot.handlers.admin_settings import router as admin_settings_router
from bot.handlers.courier import router as courier_router
from bot.handlers.notifications import router as notifications_router
from bot.handlers.start import router as start_router
from bot.handlers.superadmin import router as superadmin_router
from bot.middlewares.logging import LoggingMiddleware

logging.basicConfig(level=logging.INFO)


def _resolve_webapp_url() -> str:
    base_dir = Path(__file__).resolve().parents[1]
    candidates = [
        Path("runtime_webapp_url.txt"),
        Path("logs/runtime_webapp_url.txt"),
        base_dir / "runtime_webapp_url.txt",
        base_dir / "logs" / "runtime_webapp_url.txt",
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            value = path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if value.lower().startswith("https://"):
            return value
    env_url = os.getenv("WEBAPP_URL") or str(getattr(settings, "WEBAPP_URL", "")).strip()
    return env_url


async def _sync_chat_menu_button(bot: Bot) -> None:
    webapp_url = _resolve_webapp_url().strip()
    if not webapp_url.lower().startswith("https://"):
        logging.warning("Skip set_chat_menu_button: WEBAPP_URL is not https (%s)", webapp_url)
        return
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="Open App",
                web_app=WebAppInfo(url=webapp_url),
            )
        )
        logging.info("Chat menu button synced to %s", webapp_url)
    except Exception as exc:  # noqa: BLE001
        logging.warning("set_chat_menu_button failed: %s", exc)


async def main() -> None:
    bot = Bot(
        settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.update.middleware(LoggingMiddleware())
    dp.include_router(admin_settings_router)
    dp.include_router(admin_products_router)
    dp.include_router(superadmin_router)
    dp.include_router(start_router)
    dp.include_router(notifications_router)
    dp.include_router(courier_router)
    await _sync_chat_menu_button(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

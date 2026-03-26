# -*- coding: utf-8 -*-
from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


@dataclass(slots=True)
class Settings:
    bot_token: str
    web_app_url: str
    admin_chat_id: int
    database_path: str
    backend_host: str
    backend_port: int
    click_payment_url_template: str
    payme_payment_url_template: str
    payme_merchant_api_url: str
    click_secret_key: str
    payme_key: str
    webapp_init_data_ttl_seconds: int
    log_level: str

    @classmethod
    def from_env(cls) -> "Settings":
        bot_token = os.getenv("BOT_TOKEN", "").strip()
        web_app_url = os.getenv("WEB_APP_URL", "").strip()

        if not bot_token:
            raise RuntimeError("BOT_TOKEN is required in the .env file.")
        if not web_app_url:
            raise RuntimeError("WEB_APP_URL is required in the .env file.")

        admin_chat_id_raw = os.getenv("ADMIN_CHAT_ID", "0").strip()
        backend_port_raw = os.getenv("BACKEND_PORT", "8000").strip()
        init_data_ttl_raw = os.getenv("WEBAPP_INIT_DATA_TTL_SECONDS", "86400").strip()

        return cls(
            bot_token=bot_token,
            web_app_url=web_app_url,
            admin_chat_id=int(admin_chat_id_raw) if admin_chat_id_raw.isdigit() else 0,
            database_path=os.getenv("DATABASE_PATH", "food_delivery.db").strip() or "food_delivery.db",
            backend_host=os.getenv("BACKEND_HOST", "127.0.0.1").strip() or "127.0.0.1",
            backend_port=int(backend_port_raw) if backend_port_raw.isdigit() else 8000,
            click_payment_url_template=os.getenv(
                "CLICK_PAYMENT_URL_TEMPLATE",
                "https://my.click.uz/services/pay?service_id={provider}&merchant_id={order_id}&amount={amount}",
            ).strip(),
            payme_payment_url_template=os.getenv(
                "PAYME_PAYMENT_URL_TEMPLATE",
                "https://checkout.paycom.uz/{provider}?id={order_id}&amount={amount}",
            ).strip(),
            payme_merchant_api_url=os.getenv(
                "PAYME_MERCHANT_API_URL",
                "https://checkout.paycom.uz/api",
            ).strip(),
            click_secret_key=os.getenv("CLICK_SECRET_KEY", "").strip(),
            payme_key=os.getenv("PAYME_KEY", "").strip(),
            webapp_init_data_ttl_seconds=(
                int(init_data_ttl_raw) if init_data_ttl_raw.isdigit() else 86400
            ),
            log_level=os.getenv("LOG_LEVEL", "INFO").strip() or "INFO",
        )


settings = Settings.from_env()

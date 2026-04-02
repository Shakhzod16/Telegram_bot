# -*- coding: utf-8 -*-
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_csv(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        return value
    return [item.strip() for item in str(value).split(",") if item.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: str = Field(default="development", alias="ENVIRONMENT")

    bot_token: str = Field(alias="BOT_TOKEN")
    web_app_url: str = Field(alias="WEB_APP_URL")

    bot_mode: str = Field(default="polling", alias="BOT_MODE")
    webhook_url: str = Field(default="", alias="WEBHOOK_URL")
    webhook_listen: str = Field(default="0.0.0.0", alias="WEBHOOK_LISTEN")
    webhook_port: int = Field(default=8443, alias="WEBHOOK_PORT")
    webhook_path: str = Field(default="/telegram/webhook", alias="WEBHOOK_PATH")
    webhook_secret: str = Field(default="", alias="WEBHOOK_SECRET")

    admin_chat_id: int = Field(default=0, alias="ADMIN_CHAT_ID")
    admin_api_key: str = Field(default="", alias="ADMIN_API_KEY")
    admin_ids: list[int] = Field(default_factory=list, alias="ADMIN_IDS")

    database_url: str = Field(default="sqlite+aiosqlite:///./backend.db", alias="DATABASE_URL")
    database_path: str = Field(default="food_delivery.db", alias="DATABASE_PATH")

    backend_host: str = Field(default="127.0.0.1", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")
    api_base_url: str = Field(default="http://127.0.0.1:8000", alias="API_BASE_URL")
    frontend_origin: str = Field(default="http://127.0.0.1:8000", alias="FRONTEND_ORIGIN")
    cors_origins: list[str] = Field(default_factory=list, alias="CORS_ORIGINS")

    click_service_id: str = Field(default="", alias="CLICK_SERVICE_ID")
    click_merchant_id: str = Field(default="", alias="CLICK_MERCHANT_ID")
    click_secret_key: str = Field(default="", alias="CLICK_SECRET_KEY")

    payme_merchant_id: str = Field(default="", alias="PAYME_MERCHANT_ID")
    payme_key: str = Field(default="", alias="PAYME_KEY")
    payme_checkout_url: str = Field(default="https://checkout.paycom.uz", alias="PAYME_CHECKOUT_URL")
    payme_merchant_api_url: str = Field(default="https://checkout.paycom.uz/api", alias="PAYME_MERCHANT_API_URL")

    webapp_init_data_ttl_seconds: int = Field(default=86400, alias="WEBAPP_INIT_DATA_TTL_SECONDS")
    cache_ttl_seconds: int = Field(default=60, alias="PRODUCTS_CACHE_TTL_SECONDS")
    log_level: str = Field(default="", alias="LOG_LEVEL")

    click_payment_url_template: str = Field(
        default="https://my.click.uz/services/pay?service_id={provider}&merchant_id={order_id}&amount={amount}",
        alias="CLICK_PAYMENT_URL_TEMPLATE",
    )
    payme_payment_url_template: str = Field(
        default="https://checkout.paycom.uz/{provider}?id={order_id}&amount={amount}",
        alias="PAYME_PAYMENT_URL_TEMPLATE",
    )

    @field_validator("admin_ids", mode="before")
    @classmethod
    def _validate_admin_ids(cls, value: str | list[int] | None) -> list[int]:
        if value is None:
            return []
        if isinstance(value, list):
            return [int(item) for item in value if str(item).strip()]
        return [int(item) for item in _parse_csv(str(value))]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _validate_cors_origins(cls, value: str | list[str] | None) -> list[str]:
        if value is None:
            return []
        return _parse_csv(value)

    @model_validator(mode="after")
    def _derive_defaults(self) -> "Settings":
        if not self.webhook_path.startswith("/"):
            self.webhook_path = f"/{self.webhook_path}"
        if not self.cors_origins:
            self.cors_origins = [self.frontend_origin]
        if not self.log_level:
            self.log_level = "DEBUG" if self.environment.lower() == "development" else "INFO"
        return self

    @property
    def database_url_sync(self) -> str:
        if self.database_url.startswith("sqlite+aiosqlite://"):
            return self.database_url.replace("sqlite+aiosqlite://", "sqlite://", 1)
        return self.database_url


settings = Settings()

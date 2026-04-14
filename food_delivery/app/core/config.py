from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        enable_decoding=False,
    )

    # Telegram
    telegram_bot_token: str = Field(validation_alias="TELEGRAM_BOT_TOKEN")
    telegram_bot_username: str = Field(default="", validation_alias="TELEGRAM_BOT_USERNAME")
    webapp_url: str = Field(default="http://localhost:8000/webapp", validation_alias="WEBAPP_URL")

    # Security
    secret_key: str = Field(validation_alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", validation_alias="ALGORITHM")
    access_token_expire_minutes: int = Field(default=10080, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    # Database
    database_url: str = Field(validation_alias="DATABASE_URL")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")

    # App settings
    debug: bool = Field(default=True, validation_alias="DEBUG")
    dev_mode: bool = Field(default=True, validation_alias="DEV_MODE")
    backend_url: str = Field(default="http://localhost:8000", validation_alias="BACKEND_URL")
    min_order_amount: int = Field(default=15000, validation_alias="MIN_ORDER_AMOUNT")
    delivery_fee: int = Field(default=5000, validation_alias="DELIVERY_FEE")

    # Admin
    admin_telegram_ids: list[int] = Field(default_factory=list, validation_alias="ADMIN_TELEGRAM_IDS")
    superadmin_telegram_ids: list[int] = Field(default_factory=list, validation_alias="SUPERADMIN_TELEGRAM_IDS")
    courier_group_id: int | None = Field(default=None, validation_alias="COURIER_GROUP_ID")

    # Optional runtime settings used by existing services.
    cart_ttl_seconds: int = Field(default=7 * 24 * 3600, validation_alias="CART_TTL_SECONDS")
    cart_sync_idle_seconds: int = Field(default=30 * 60, validation_alias="CART_SYNC_IDLE_SECONDS")
    otp_ttl_seconds: int = Field(default=300, validation_alias="OTP_TTL_SECONDS")

    @field_validator("admin_telegram_ids", mode="before")
    @classmethod
    def parse_admin_telegram_ids(cls, value: Any) -> list[int]:
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [int(item.strip()) for item in value.split(",") if item.strip()]
        if isinstance(value, (list, tuple, set)):
            return [int(item) for item in value]
        return [int(value)]

    @field_validator("superadmin_telegram_ids", mode="before")
    @classmethod
    def parse_superadmin_telegram_ids(cls, value: Any) -> list[int]:
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [int(item.strip()) for item in value.split(",") if item.strip()]
        if isinstance(value, (list, tuple, set)):
            return [int(item) for item in value]
        return [int(value)]

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug_flag(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return True
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "on", "dev", "debug", "development"}:
            return True
        if text in {"0", "false", "no", "off", "prod", "production", "release"}:
            return False
        return bool(value)

    @field_validator("dev_mode", mode="before")
    @classmethod
    def parse_dev_mode_flag(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return True
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "on", "dev", "debug", "development"}:
            return True
        if text in {"0", "false", "no", "off", "prod", "production", "release"}:
            return False
        return bool(value)

    @property
    def admin_telegram_id_set(self) -> set[int]:
        return set(self.admin_telegram_ids)

    # Backwards-compatible uppercase access for existing modules.
    @property
    def TELEGRAM_BOT_TOKEN(self) -> str:
        return self.telegram_bot_token

    @property
    def TELEGRAM_BOT_USERNAME(self) -> str:
        return self.telegram_bot_username

    @property
    def WEBAPP_URL(self) -> str:
        return self.webapp_url

    @property
    def SECRET_KEY(self) -> str:
        return self.secret_key

    @property
    def ALGORITHM(self) -> str:
        return self.algorithm

    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        return self.access_token_expire_minutes

    @property
    def DATABASE_URL(self) -> str:
        return self.database_url

    @property
    def REDIS_URL(self) -> str:
        return self.redis_url

    @property
    def DEBUG(self) -> bool:
        return self.debug

    @property
    def DEV_MODE(self) -> bool:
        return self.dev_mode

    @property
    def BACKEND_URL(self) -> str:
        return self.backend_url

    @property
    def MIN_ORDER_AMOUNT(self) -> int:
        return self.min_order_amount

    @property
    def DELIVERY_FEE(self) -> int:
        return self.delivery_fee

    @property
    def ADMIN_TELEGRAM_IDS(self) -> str:
        return ",".join(str(item) for item in self.admin_telegram_ids)

    @property
    def SUPERADMIN_TELEGRAM_IDS(self) -> list[int]:
        return list(self.superadmin_telegram_ids)

    @property
    def COURIER_GROUP_ID(self) -> int | None:
        return self.courier_group_id

    @property
    def CART_TTL_SECONDS(self) -> int:
        return self.cart_ttl_seconds

    @property
    def CART_SYNC_IDLE_SECONDS(self) -> int:
        return self.cart_sync_idle_seconds

    @property
    def OTP_TTL_SECONDS(self) -> int:
        return self.otp_ttl_seconds


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

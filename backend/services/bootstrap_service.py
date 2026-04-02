# -*- coding: utf-8 -*-
from __future__ import annotations

import time
from typing import Any

from backend.models import Product, User
from backend.repositories.address_repo import AddressRepository
from backend.repositories.product_repo import ProductRepository
from backend.repositories.user_repo import UserRepository
from utils.texts import frontend_texts

DEFAULT_PRODUCTS: list[dict[str, Any]] = [
    {
        "category": "burger",
        "name_uz": "Classic Burger",
        "name_ru": "Classic Burger",
        "name_en": "Classic Burger",
        "description_uz": "Mol go'shti, sous va yangi sabzavotlar.",
        "description_ru": "Р“РѕРІСЏРґРёРЅР°, СЃРѕСѓСЃ Рё СЃРІРµР¶РёРµ РѕРІРѕС‰Рё.",
        "description_en": "Beef patty, signature sauce, fresh vegetables.",
        "price": 32000,
        "image_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=900&q=80",
    },
    {
        "category": "lavash",
        "name_uz": "Lavash Beef",
        "name_ru": "Р›Р°РІР°С€ СЃ РіРѕРІСЏРґРёРЅРѕР№",
        "name_en": "Lavash Beef",
        "description_uz": "Yumshoq lavash ichida go'sht va sabzavot.",
        "description_ru": "РњСЏРіРєРёР№ Р»Р°РІР°С€ СЃ РјСЏСЃРѕРј Рё РѕРІРѕС‰Р°РјРё.",
        "description_en": "Soft lavash wrap with beef and veggies.",
        "price": 36000,
        "image_url": "https://images.unsplash.com/photo-1619740455993-9e612b1af08d?auto=format&fit=crop&w=900&q=80",
    },
    {
        "category": "drinks",
        "name_uz": "Cola",
        "name_ru": "РљРѕР»Р°",
        "name_en": "Cola",
        "description_uz": "Sovuq gazlangan ichimlik.",
        "description_ru": "РҐРѕР»РѕРґРЅС‹Р№ РіР°Р·РёСЂРѕРІР°РЅРЅС‹Р№ РЅР°РїРёС‚РѕРє.",
        "description_en": "Cold sparkling drink.",
        "price": 12000,
        "image_url": "https://images.unsplash.com/photo-1629203851122-3726ecdf080e?auto=format&fit=crop&w=900&q=80",
    },
    {
        "category": "combo",
        "name_uz": "Combo Set",
        "name_ru": "РљРѕРјР±Рѕ РЅР°Р±РѕСЂ",
        "name_en": "Combo Set",
        "description_uz": "Burger, fri va ichimlik.",
        "description_ru": "Р‘СѓСЂРіРµСЂ, С„СЂРё Рё РЅР°РїРёС‚РѕРє.",
        "description_en": "Burger, fries and drink.",
        "price": 59000,
        "image_url": "https://images.unsplash.com/photo-1571091718767-18b5b1457add?auto=format&fit=crop&w=900&q=80",
    },
]


class BootstrapService:
    _cache: dict[str, Any] = {"expires_at": 0.0, "data": {}}

    def __init__(
        self,
        user_repo: UserRepository,
        product_repo: ProductRepository,
        address_repo: AddressRepository,
        cache_ttl_seconds: int,
    ) -> None:
        self.user_repo = user_repo
        self.product_repo = product_repo
        self.address_repo = address_repo
        self.cache_ttl_seconds = cache_ttl_seconds

    @staticmethod
    def _product_view(row: Product, language: str) -> dict[str, Any]:
        lang = language if language in {"uz", "ru", "en"} else "en"
        return {
            "id": row.id,
            "category": row.category,
            "price": row.price,
            "image_url": row.image_url,
            "name": getattr(row, f"name_{lang}"),
            "description": getattr(row, f"description_{lang}"),
        }

    async def seed_products_if_needed(self) -> None:
        count = await self.product_repo.count_all()
        if count:
            return
        for item in DEFAULT_PRODUCTS:
            await self.product_repo.create(item)
        await self.product_repo.session.commit()

    async def get_or_create_user(self, telegram_user: dict) -> User:
        tg_id = int(telegram_user["id"])
        existing = await self.user_repo.get_by_telegram_id(tg_id)
        if existing:
            existing.first_name = telegram_user.get("first_name", existing.first_name or "")
            existing.last_name = telegram_user.get("last_name", existing.last_name or "")
            existing.username = telegram_user.get("username", existing.username or "")
            await self.user_repo.session.flush()
            return existing

        created = await self.user_repo.create(
            {
                "telegram_user_id": tg_id,
                "first_name": telegram_user.get("first_name", ""),
                "last_name": telegram_user.get("last_name", ""),
                "username": telegram_user.get("username", ""),
                "language": telegram_user.get("language_code", "en"),
            }
        )
        return created

    async def list_products(self, language: str) -> list[dict[str, Any]]:
        now = time.time()
        cached = self._cache["data"].get(language)
        if cached and now < self._cache["expires_at"]:
            return cached

        rows = await self.product_repo.get_all(active_only=True)
        mapped = [self._product_view(row, language) for row in rows]
        self._cache["data"][language] = mapped
        self._cache["expires_at"] = now + self.cache_ttl_seconds
        return mapped

    async def bootstrap_payload(self, telegram_user: dict) -> dict[str, Any]:
        user = await self.get_or_create_user(telegram_user)
        products = await self.list_products(user.language)
        addresses = await self.address_repo.list_by_user(user.id)
        return {
            "user": {
                "id": user.id,
                "user_id": user.telegram_user_id,
                "first_name": user.first_name,
                "language": user.language,
            },
            "products": products,
            "texts": frontend_texts(user.language),
            "saved_addresses": [
                {
                    "id": address.id,
                    "user_id": address.user_id,
                    "label": address.label,
                    "address_text": address.address_text,
                    "latitude": float(address.latitude) if address.latitude is not None else None,
                    "longitude": float(address.longitude) if address.longitude is not None else None,
                    "is_default": bool(address.is_default),
                }
                for address in addresses
            ],
        }

from __future__ import annotations

import asyncio
import sys
import zlib
from datetime import time
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.branch import Branch
from app.models.category import Category
from app.models.product import Product, ProductModifier, ProductVariant
from app.models.promo import Promo
from app.models.user import User

BRANCHES: list[dict] = [
    {
        "name": "Yunusobod filiali",
        "lat": 41.3111,
        "lng": 69.2797,
        "radius_km": 5.0,
        "address": "Yunusobod tumani, Toshkent",
        "phone": "+998901112233",
        "open_time": time(10, 0),
        "close_time": time(22, 0),
        "delivery_fee": 5000,
        "is_active": True,
    },
    {
        "name": "Chilonzor filiali",
        "lat": 41.2995,
        "lng": 69.2401,
        "radius_km": 5.0,
        "address": "Chilonzor tumani, Toshkent",
        "phone": "+998901234567",
        "open_time": time(10, 0),
        "close_time": time(22, 0),
        "delivery_fee": 5000,
        "is_active": True,
    },
]

CATEGORIES: list[dict] = [
    {"name_uz": "Burgerlar", "name_ru": "Бургеры", "sort_order": 1, "is_active": True},
    {"name_uz": "Salatlar", "name_ru": "Салаты", "sort_order": 2, "is_active": True},
    {"name_uz": "Ichimliklar", "name_ru": "Напитки", "sort_order": 3, "is_active": True},
    {"name_uz": "Desertlar", "name_ru": "Десерты", "sort_order": 4, "is_active": True},
    {"name_uz": "Setlar", "name_ru": "Сеты", "sort_order": 5, "is_active": True},
]

PRODUCTS_BY_CATEGORY: dict[str, list[dict]] = {
    "Burgerlar": [
        {
            "name_uz": "Classic Burger",
            "name_ru": "Классический бургер",
            "description_uz": "Mol go'shti kotleti, pishloq va sabzavotlar.",
            "description_ru": "Говяжья котлета, сыр и свежие овощи.",
            "base_price": Decimal("26000"),
            "weight_grams": 290,
            "image_url": None,
            "variants": [
                {"name_uz": "Kichik", "name_ru": "Маленький", "price": Decimal("23000"), "weight_grams": 240, "is_default": False},
                {"name_uz": "O'rta", "name_ru": "Средний", "price": Decimal("26000"), "weight_grams": 290, "is_default": True},
                {"name_uz": "Katta", "name_ru": "Большой", "price": Decimal("32000"), "weight_grams": 360, "is_default": False},
            ],
            "modifiers": [
                {"name_uz": "Qo'shimcha pishloq", "name_ru": "Доп. сыр", "price_delta": Decimal("4000"), "is_required": False},
                {"name_uz": "Jalapeno", "name_ru": "Халапеньо", "price_delta": Decimal("3000"), "is_required": False},
            ],
        },
        {
            "name_uz": "Cheese Burger",
            "name_ru": "Чизбургер",
            "description_uz": "Ikki qavat pishloqli yumshoq burger.",
            "description_ru": "Нежный бургер с двойным сыром.",
            "base_price": Decimal("30000"),
            "weight_grams": 310,
            "image_url": None,
            "variants": [
                {"name_uz": "Kichik", "name_ru": "Маленький", "price": Decimal("27000"), "weight_grams": 260, "is_default": False},
                {"name_uz": "O'rta", "name_ru": "Средний", "price": Decimal("30000"), "weight_grams": 310, "is_default": True},
                {"name_uz": "Katta", "name_ru": "Большой", "price": Decimal("37000"), "weight_grams": 390, "is_default": False},
            ],
            "modifiers": [
                {"name_uz": "Bekon", "name_ru": "Бекон", "price_delta": Decimal("6000"), "is_required": False},
                {"name_uz": "Qo'shimcha sous", "name_ru": "Доп. соус", "price_delta": Decimal("2000"), "is_required": False},
            ],
        },
        {
            "name_uz": "Double Burger",
            "name_ru": "Двойной бургер",
            "description_uz": "Ikki kotletli to'yimli burger.",
            "description_ru": "Сытный бургер с двумя котлетами.",
            "base_price": Decimal("36000"),
            "weight_grams": 360,
            "image_url": None,
            "variants": [
                {"name_uz": "Kichik", "name_ru": "Маленький", "price": Decimal("33000"), "weight_grams": 320, "is_default": False},
                {"name_uz": "O'rta", "name_ru": "Средний", "price": Decimal("36000"), "weight_grams": 360, "is_default": True},
                {"name_uz": "Katta", "name_ru": "Большой", "price": Decimal("43000"), "weight_grams": 430, "is_default": False},
            ],
            "modifiers": [
                {"name_uz": "Piyoz halqasi", "name_ru": "Луковые кольца", "price_delta": Decimal("3500"), "is_required": False},
                {"name_uz": "Achchiq sous", "name_ru": "Острый соус", "price_delta": Decimal("2500"), "is_required": False},
            ],
        },
        {
            "name_uz": "Chicken Burger",
            "name_ru": "Куриный бургер",
            "description_uz": "Tovuq filesi va yangi salat bilan.",
            "description_ru": "Куриное филе со свежим салатом.",
            "base_price": Decimal("28000"),
            "weight_grams": 300,
            "image_url": None,
            "variants": [
                {"name_uz": "Kichik", "name_ru": "Маленький", "price": Decimal("25000"), "weight_grams": 250, "is_default": False},
                {"name_uz": "O'rta", "name_ru": "Средний", "price": Decimal("28000"), "weight_grams": 300, "is_default": True},
                {"name_uz": "Katta", "name_ru": "Большой", "price": Decimal("34000"), "weight_grams": 370, "is_default": False},
            ],
            "modifiers": [
                {"name_uz": "Qo'shimcha tovuq", "name_ru": "Доп. курица", "price_delta": Decimal("7000"), "is_required": False},
                {"name_uz": "Marinad bodring", "name_ru": "Марин. огурец", "price_delta": Decimal("1500"), "is_required": False},
            ],
        },
    ],
    "Salatlar": [
        {
            "name_uz": "Sezar salat",
            "name_ru": "Салат Цезарь",
            "description_uz": "Tovuq va parmesanli klassik salat.",
            "description_ru": "Классический салат с курицей и пармезаном.",
            "base_price": Decimal("22000"),
            "weight_grams": 240,
            "image_url": None,
            "variants": [
                {"name_uz": "Kichik", "name_ru": "Маленький", "price": Decimal("19000"), "weight_grams": 190, "is_default": False},
                {"name_uz": "O'rta", "name_ru": "Средний", "price": Decimal("22000"), "weight_grams": 240, "is_default": True},
                {"name_uz": "Katta", "name_ru": "Большой", "price": Decimal("28000"), "weight_grams": 310, "is_default": False},
            ],
            "modifiers": [
                {"name_uz": "Qo'shimcha parmesan", "name_ru": "Доп. пармезан", "price_delta": Decimal("3000"), "is_required": False},
            ],
        },
        {
            "name_uz": "Grek salat",
            "name_ru": "Греческий салат",
            "description_uz": "Feta pishlog'i va zaytun bilan.",
            "description_ru": "С сыром фета и оливками.",
            "base_price": Decimal("20000"),
            "weight_grams": 220,
            "image_url": None,
            "variants": [
                {"name_uz": "Kichik", "name_ru": "Маленький", "price": Decimal("17000"), "weight_grams": 180, "is_default": False},
                {"name_uz": "O'rta", "name_ru": "Средний", "price": Decimal("20000"), "weight_grams": 220, "is_default": True},
                {"name_uz": "Katta", "name_ru": "Большой", "price": Decimal("26000"), "weight_grams": 290, "is_default": False},
            ],
            "modifiers": [
                {"name_uz": "Qo'shimcha zaytun", "name_ru": "Доп. оливки", "price_delta": Decimal("2500"), "is_required": False},
            ],
        },
        {
            "name_uz": "Tuna salat",
            "name_ru": "Салат с тунцом",
            "description_uz": "Tuna, makkajo'xori va ko'katlar.",
            "description_ru": "Тунец, кукуруза и зелень.",
            "base_price": Decimal("24000"),
            "weight_grams": 250,
            "image_url": None,
            "variants": [
                {"name_uz": "Kichik", "name_ru": "Маленький", "price": Decimal("21000"), "weight_grams": 200, "is_default": False},
                {"name_uz": "O'rta", "name_ru": "Средний", "price": Decimal("24000"), "weight_grams": 250, "is_default": True},
                {"name_uz": "Katta", "name_ru": "Большой", "price": Decimal("30000"), "weight_grams": 320, "is_default": False},
            ],
            "modifiers": [
                {"name_uz": "Qo'shimcha tuna", "name_ru": "Доп. тунец", "price_delta": Decimal("5000"), "is_required": False},
            ],
        },
        {
            "name_uz": "Vitaminsalat",
            "name_ru": "Витаминный салат",
            "description_uz": "Yangi karam va sabzi aralashmasi.",
            "description_ru": "Свежая капуста и морковь.",
            "base_price": Decimal("15000"),
            "weight_grams": 210,
            "image_url": None,
            "variants": [
                {"name_uz": "Kichik", "name_ru": "Маленький", "price": Decimal("15000"), "weight_grams": 170, "is_default": True},
                {"name_uz": "O'rta", "name_ru": "Средний", "price": Decimal("18000"), "weight_grams": 210, "is_default": False},
                {"name_uz": "Katta", "name_ru": "Большой", "price": Decimal("23000"), "weight_grams": 280, "is_default": False},
            ],
            "modifiers": [
                {"name_uz": "Limon sous", "name_ru": "Лимонный соус", "price_delta": Decimal("1000"), "is_required": False},
            ],
        },
    ],
    "Ichimliklar": [
        {
            "name_uz": "Cola",
            "name_ru": "Кола",
            "description_uz": "Gazli ichimlik.",
            "description_ru": "Газированный напиток.",
            "base_price": Decimal("16000"),
            "weight_grams": 500,
            "image_url": None,
            "variants": [
                {"name_uz": "Kichik", "name_ru": "Маленький", "price": Decimal("16000"), "weight_grams": 330, "is_default": False},
                {"name_uz": "O'rta", "name_ru": "Средний", "price": Decimal("18000"), "weight_grams": 500, "is_default": True},
                {"name_uz": "Katta", "name_ru": "Большой", "price": Decimal("22000"), "weight_grams": 1000, "is_default": False},
            ],
            "modifiers": [],
        },
        {
            "name_uz": "Fanta",
            "name_ru": "Фанта",
            "description_uz": "Apelsin ta'mli ichimlik.",
            "description_ru": "Напиток со вкусом апельсина.",
            "base_price": Decimal("16000"),
            "weight_grams": 500,
            "image_url": None,
            "variants": [
                {"name_uz": "Kichik", "name_ru": "Маленький", "price": Decimal("16000"), "weight_grams": 330, "is_default": False},
                {"name_uz": "O'rta", "name_ru": "Средний", "price": Decimal("18000"), "weight_grams": 500, "is_default": True},
                {"name_uz": "Katta", "name_ru": "Большой", "price": Decimal("22000"), "weight_grams": 1000, "is_default": False},
            ],
            "modifiers": [],
        },
        {
            "name_uz": "Sharbat",
            "name_ru": "Сок",
            "description_uz": "Tabiiy mevali sharbat.",
            "description_ru": "Натуральный фруктовый сок.",
            "base_price": Decimal("18000"),
            "weight_grams": 500,
            "image_url": None,
            "variants": [
                {"name_uz": "Kichik", "name_ru": "Маленький", "price": Decimal("18000"), "weight_grams": 300, "is_default": False},
                {"name_uz": "O'rta", "name_ru": "Средний", "price": Decimal("21000"), "weight_grams": 500, "is_default": True},
                {"name_uz": "Katta", "name_ru": "Большой", "price": Decimal("26000"), "weight_grams": 1000, "is_default": False},
            ],
            "modifiers": [],
        },
        {
            "name_uz": "Moxito",
            "name_ru": "Мохито",
            "description_uz": "Yalpizli sovuq ichimlik.",
            "description_ru": "Освежающий напиток с мятой.",
            "base_price": Decimal("22000"),
            "weight_grams": 450,
            "image_url": None,
            "variants": [
                {"name_uz": "Kichik", "name_ru": "Маленький", "price": Decimal("22000"), "weight_grams": 300, "is_default": False},
                {"name_uz": "O'rta", "name_ru": "Средний", "price": Decimal("25000"), "weight_grams": 450, "is_default": True},
                {"name_uz": "Katta", "name_ru": "Большой", "price": Decimal("30000"), "weight_grams": 700, "is_default": False},
            ],
            "modifiers": [],
        },
    ],
    "Desertlar": [
        {
            "name_uz": "Cheesecake",
            "name_ru": "Чизкейк",
            "description_uz": "Yengil pishloqli desert.",
            "description_ru": "Нежный сырный десерт.",
            "base_price": Decimal("28000"),
            "weight_grams": 180,
            "image_url": None,
            "variants": [
                {"name_uz": "Kichik", "name_ru": "Маленький", "price": Decimal("24000"), "weight_grams": 130, "is_default": False},
                {"name_uz": "O'rta", "name_ru": "Средний", "price": Decimal("28000"), "weight_grams": 180, "is_default": True},
                {"name_uz": "Katta", "name_ru": "Большой", "price": Decimal("34000"), "weight_grams": 250, "is_default": False},
            ],
            "modifiers": [
                {"name_uz": "Qulupnay siropi", "name_ru": "Клубничный сироп", "price_delta": Decimal("2500"), "is_required": False},
            ],
        },
        {
            "name_uz": "Brownie",
            "name_ru": "Брауни",
            "description_uz": "Shokoladli yumshoq pirog.",
            "description_ru": "Шоколадный мягкий пирог.",
            "base_price": Decimal("24000"),
            "weight_grams": 170,
            "image_url": None,
            "variants": [
                {"name_uz": "Kichik", "name_ru": "Маленький", "price": Decimal("21000"), "weight_grams": 130, "is_default": False},
                {"name_uz": "O'rta", "name_ru": "Средний", "price": Decimal("24000"), "weight_grams": 170, "is_default": True},
                {"name_uz": "Katta", "name_ru": "Большой", "price": Decimal("29000"), "weight_grams": 230, "is_default": False},
            ],
            "modifiers": [
                {"name_uz": "Vanilli muzqaymoq", "name_ru": "Ванильное мороженое", "price_delta": Decimal("4000"), "is_required": False},
            ],
        },
        {
            "name_uz": "Napoleon",
            "name_ru": "Наполеон",
            "description_uz": "Qavat-qavat kremli tort.",
            "description_ru": "Слоёный торт с кремом.",
            "base_price": Decimal("26000"),
            "weight_grams": 180,
            "image_url": None,
            "variants": [
                {"name_uz": "Kichik", "name_ru": "Маленький", "price": Decimal("23000"), "weight_grams": 140, "is_default": False},
                {"name_uz": "O'rta", "name_ru": "Средний", "price": Decimal("26000"), "weight_grams": 180, "is_default": True},
                {"name_uz": "Katta", "name_ru": "Большой", "price": Decimal("32000"), "weight_grams": 250, "is_default": False},
            ],
            "modifiers": [],
        },
        {
            "name_uz": "Tiramisu",
            "name_ru": "Тирамису",
            "description_uz": "Qahva ta'mli italyan deserti.",
            "description_ru": "Итальянский десерт с кофейным вкусом.",
            "base_price": Decimal("30000"),
            "weight_grams": 190,
            "image_url": None,
            "variants": [
                {"name_uz": "Kichik", "name_ru": "Маленький", "price": Decimal("27000"), "weight_grams": 150, "is_default": False},
                {"name_uz": "O'rta", "name_ru": "Средний", "price": Decimal("30000"), "weight_grams": 190, "is_default": True},
                {"name_uz": "Katta", "name_ru": "Большой", "price": Decimal("36000"), "weight_grams": 260, "is_default": False},
            ],
            "modifiers": [],
        },
    ],
    "Setlar": [
        {
            "name_uz": "Family Set",
            "name_ru": "Семейный сет",
            "description_uz": "Katta oila uchun to'liq to'plam.",
            "description_ru": "Большой сет для всей семьи.",
            "base_price": Decimal("78000"),
            "weight_grams": 1400,
            "image_url": None,
            "variants": [
                {"name_uz": "Kichik", "name_ru": "Маленький", "price": Decimal("62000"), "weight_grams": 1000, "is_default": False},
                {"name_uz": "O'rta", "name_ru": "Средний", "price": Decimal("78000"), "weight_grams": 1400, "is_default": True},
                {"name_uz": "Katta", "name_ru": "Большой", "price": Decimal("80000"), "weight_grams": 1800, "is_default": False},
            ],
            "modifiers": [
                {"name_uz": "Qo'shimcha fri", "name_ru": "Доп. фри", "price_delta": Decimal("8000"), "is_required": False},
            ],
        },
        {
            "name_uz": "Office Set",
            "name_ru": "Офисный сет",
            "description_uz": "4 kishilik qulay tushlik seti.",
            "description_ru": "Удобный ланч-сет на 4 персоны.",
            "base_price": Decimal("65000"),
            "weight_grams": 1200,
            "image_url": None,
            "variants": [
                {"name_uz": "Kichik", "name_ru": "Маленький", "price": Decimal("52000"), "weight_grams": 900, "is_default": False},
                {"name_uz": "O'rta", "name_ru": "Средний", "price": Decimal("65000"), "weight_grams": 1200, "is_default": True},
                {"name_uz": "Katta", "name_ru": "Большой", "price": Decimal("76000"), "weight_grams": 1600, "is_default": False},
            ],
            "modifiers": [
                {"name_uz": "Qo'shimcha cola", "name_ru": "Доп. кола", "price_delta": Decimal("12000"), "is_required": False},
            ],
        },
        {
            "name_uz": "Party Set",
            "name_ru": "Пати сет",
            "description_uz": "Do'stlar davrasi uchun maxsus set.",
            "description_ru": "Специальный сет для компании друзей.",
            "base_price": Decimal("72000"),
            "weight_grams": 1300,
            "image_url": None,
            "variants": [
                {"name_uz": "Kichik", "name_ru": "Маленький", "price": Decimal("58000"), "weight_grams": 980, "is_default": False},
                {"name_uz": "O'rta", "name_ru": "Средний", "price": Decimal("72000"), "weight_grams": 1300, "is_default": True},
                {"name_uz": "Katta", "name_ru": "Большой", "price": Decimal("79000"), "weight_grams": 1700, "is_default": False},
            ],
            "modifiers": [
                {"name_uz": "Achchiq souslar", "name_ru": "Острые соусы", "price_delta": Decimal("5000"), "is_required": False},
            ],
        },
        {
            "name_uz": "Kids Set",
            "name_ru": "Детский сет",
            "description_uz": "Bolalar uchun yumshoq ta'mli set.",
            "description_ru": "Сет для детей с мягким вкусом.",
            "base_price": Decimal("45000"),
            "weight_grams": 900,
            "image_url": None,
            "variants": [
                {"name_uz": "Kichik", "name_ru": "Маленький", "price": Decimal("38000"), "weight_grams": 700, "is_default": False},
                {"name_uz": "O'rta", "name_ru": "Средний", "price": Decimal("45000"), "weight_grams": 900, "is_default": True},
                {"name_uz": "Katta", "name_ru": "Большой", "price": Decimal("54000"), "weight_grams": 1200, "is_default": False},
            ],
            "modifiers": [
                {"name_uz": "Shirinlik qo'shish", "name_ru": "Добавить десерт", "price_delta": Decimal("6000"), "is_required": False},
            ],
        },
    ],
}

PROMOS: list[dict] = [
    {
        "code": "FIRST10",
        "discount_type": "percent",
        "discount_value": Decimal("10"),
        "min_order_amount": Decimal("30000"),
        "max_uses": 1000,
        "is_active": True,
    },
    {
        "code": "SUMMER20",
        "discount_type": "percent",
        "discount_value": Decimal("20"),
        "min_order_amount": Decimal("50000"),
        "max_uses": None,
        "is_active": True,
    },
    {
        "code": "FIXED5000",
        "discount_type": "fixed",
        "discount_value": Decimal("5000"),
        "min_order_amount": Decimal("25000"),
        "max_uses": None,
        "is_active": True,
    },
]


def _pick_image_query(name: str, category_name: str) -> str:
    n = (name or "").lower()
    c = (category_name or "").lower()

    if "burger" in n or "burger" in c:
        return "burger,fast food,meal"
    if any(word in n for word in ("salat", "sezar", "grek", "tuna", "vitamin")) or "salat" in c:
        return "salad,fresh food,bowl"
    if any(word in n for word in ("cola", "fanta", "sharbat", "moxito", "ichimlik")) or "ichimlik" in c:
        return "soft drink,beverage,cold drink"
    if any(word in n for word in ("cheesecake", "brownie", "napoleon", "tiramisu", "desert")) or "desert" in c:
        return "dessert,cake,sweet"
    if "set" in n or "setlar" in c:
        return "food platter,combo meal,party food"
    return "food,dish,restaurant"


def _build_product_image_url(name: str, category_name: str) -> str:
    query = _pick_image_query(name, category_name)
    sig = zlib.crc32(f"{category_name}:{name}".encode("utf-8")) % 100000
    return f"https://source.unsplash.com/1200x900/?{quote(query, safe=',')}&sig={sig}"


async def _upsert_branch(session: AsyncSession, payload: dict) -> Branch:
    branch = await session.scalar(select(Branch).where(Branch.name == payload["name"]))
    if branch is None:
        branch = Branch(**payload)
        session.add(branch)
        await session.flush()
        return branch
    for key, value in payload.items():
        setattr(branch, key, value)
    await session.flush()
    return branch


async def _upsert_category(session: AsyncSession, payload: dict) -> Category:
    category = await session.scalar(select(Category).where(Category.name_uz == payload["name_uz"]))
    if category is None:
        category = Category(**payload)
        session.add(category)
        await session.flush()
        return category
    for key, value in payload.items():
        setattr(category, key, value)
    await session.flush()
    return category


async def _upsert_product(session: AsyncSession, category_id: int, payload: dict) -> Product:
    product = await session.scalar(
        select(Product).where(Product.category_id == category_id, Product.name_uz == payload["name_uz"])
    )
    product_data = {
        "category_id": category_id,
        "name_uz": payload["name_uz"],
        "name_ru": payload["name_ru"],
        "description_uz": payload.get("description_uz"),
        "description_ru": payload.get("description_ru"),
        "base_price": payload["base_price"],
        "weight_grams": payload.get("weight_grams"),
        "image_url": payload.get("image_url") or _build_product_image_url(payload["name_uz"], payload.get("category_name", "")),
        "is_active": True,
    }
    if product is None:
        product = Product(**product_data)
        session.add(product)
        await session.flush()
        return product
    for key, value in product_data.items():
        setattr(product, key, value)
    await session.flush()
    return product


async def _upsert_variant(session: AsyncSession, product_id: int, payload: dict) -> ProductVariant:
    variant = await session.scalar(
        select(ProductVariant).where(ProductVariant.product_id == product_id, ProductVariant.name_uz == payload["name_uz"])
    )
    variant_data = {
        "product_id": product_id,
        "name_uz": payload["name_uz"],
        "name_ru": payload["name_ru"],
        "price": payload["price"],
        "weight_grams": payload.get("weight_grams"),
        "is_default": bool(payload.get("is_default", False)),
    }
    if variant is None:
        variant = ProductVariant(**variant_data)
        session.add(variant)
        await session.flush()
        return variant
    for key, value in variant_data.items():
        setattr(variant, key, value)
    await session.flush()
    return variant


async def _upsert_modifier(session: AsyncSession, product_id: int, payload: dict) -> ProductModifier:
    modifier = await session.scalar(
        select(ProductModifier).where(
            ProductModifier.product_id == product_id,
            ProductModifier.name_uz == payload["name_uz"],
        )
    )
    modifier_data = {
        "product_id": product_id,
        "name_uz": payload["name_uz"],
        "name_ru": payload["name_ru"],
        "price_delta": payload["price_delta"],
        "is_required": bool(payload.get("is_required", False)),
    }
    if modifier is None:
        modifier = ProductModifier(**modifier_data)
        session.add(modifier)
        await session.flush()
        return modifier
    for key, value in modifier_data.items():
        setattr(modifier, key, value)
    await session.flush()
    return modifier


async def _upsert_promo(session: AsyncSession, payload: dict) -> Promo:
    code = payload["code"].upper().strip()
    promo = await session.scalar(select(Promo).where(Promo.code == code))
    promo_data = {
        "code": code,
        "discount_type": payload["discount_type"],
        "discount_value": payload["discount_value"],
        "min_order_amount": payload["min_order_amount"],
        "max_uses": payload.get("max_uses"),
        "is_active": bool(payload.get("is_active", True)),
    }
    if promo is None:
        promo = Promo(**promo_data, used_count=0)
        session.add(promo)
        await session.flush()
        return promo
    for key, value in promo_data.items():
        setattr(promo, key, value)
    await session.flush()
    return promo


async def _upsert_admin_user(session: AsyncSession) -> User:
    admin_telegram_id = settings.admin_telegram_ids[0] if settings.admin_telegram_ids else 123456789
    user = await session.scalar(select(User).where(User.telegram_id == admin_telegram_id))
    if user is None:
        user = User(
            telegram_id=admin_telegram_id,
            first_name="Admin",
            language="uz",
            is_admin=True,
            is_active=True,
        )
        session.add(user)
        await session.flush()
        return user

    user.first_name = "Admin"
    user.is_admin = True
    user.is_active = True
    if not user.language:
        user.language = "uz"
    await session.flush()
    return user


async def main() -> None:
    async with AsyncSessionLocal() as session:
        for payload in BRANCHES:
            await _upsert_branch(session, payload)

        categories_by_name: dict[str, Category] = {}
        for payload in CATEGORIES:
            category = await _upsert_category(session, payload)
            categories_by_name[category.name_uz] = category

        for category_name, products in PRODUCTS_BY_CATEGORY.items():
            category = categories_by_name.get(category_name)
            if category is None:
                continue
            for product_payload in products:
                payload_with_category = dict(product_payload)
                payload_with_category["category_name"] = category_name
                product = await _upsert_product(session, category.id, payload_with_category)
                for variant_payload in product_payload.get("variants", []):
                    await _upsert_variant(session, product.id, variant_payload)
                for modifier_payload in product_payload.get("modifiers", []):
                    await _upsert_modifier(session, product.id, modifier_payload)

        for promo_payload in PROMOS:
            await _upsert_promo(session, promo_payload)

        admin_user = await _upsert_admin_user(session)
        await session.commit()

        branch_count = int((await session.scalar(select(func.count()).select_from(Branch))) or 0)
        category_count = int((await session.scalar(select(func.count()).select_from(Category))) or 0)
        product_count = int((await session.scalar(select(func.count()).select_from(Product))) or 0)
        promo_count = int((await session.scalar(select(func.count()).select_from(Promo))) or 0)
        print(
            "Seed complete:",
            f"branches={branch_count}",
            f"categories={category_count}",
            f"products={product_count}",
            f"promos={promo_count}",
            f"admin_telegram_id={admin_user.telegram_id}",
        )


if __name__ == "__main__":
    asyncio.run(main())

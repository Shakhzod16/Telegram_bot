# -*- coding: utf-8 -*-
import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path


ORDER_STATUSES = (
    "CREATED",
    "CONFIRMED",
    "IN_PROGRESS",
    "DELIVERING",
    "DELIVERED",
    "PAID",
    "CANCELLED",
)

MANAGEABLE_ORDER_STATUSES = (
    "CONFIRMED",
    "IN_PROGRESS",
    "DELIVERING",
    "DELIVERED",
    "CANCELLED",
)

DEFAULT_PRODUCTS = [
    {
        "category": "burger",
        "name_uz": "Classic Burger",
        "name_ru": "Классический бургер",
        "name_en": "Classic Burger",
        "description_uz": "Mol go'shti, sous va yangi sabzavotlar.",
        "description_ru": "Говядина, соус и свежие овощи.",
        "description_en": "Beef patty, signature sauce, fresh vegetables.",
        "price": 32000,
        "image_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=900&q=80",
    },
    {
        "category": "burger",
        "name_uz": "Cheese Burger",
        "name_ru": "Чизбургер",
        "name_en": "Cheese Burger",
        "description_uz": "Ikki qavatli pishloq va mol go'shti kotleti.",
        "description_ru": "Двойной сыр и котлета из говядины.",
        "description_en": "Double cheese with a juicy beef patty.",
        "price": 38000,
        "image_url": "https://images.unsplash.com/photo-1550317138-10000687a72b?auto=format&fit=crop&w=900&q=80",
    },
    {
        "category": "pizza",
        "name_uz": "Pepperoni Pizza",
        "name_ru": "Пицца Пепперони",
        "name_en": "Pepperoni Pizza",
        "description_uz": "Pepperoni, mozzarella va pomidor sousi.",
        "description_ru": "Пепперони, моцарелла и томатный соус.",
        "description_en": "Pepperoni, mozzarella and tomato sauce.",
        "price": 69000,
        "image_url": "https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=900&q=80",
    },
    {
        "category": "pizza",
        "name_uz": "BBQ Chicken Pizza",
        "name_ru": "Пицца BBQ с курицей",
        "name_en": "BBQ Chicken Pizza",
        "description_uz": "BBQ tovuq, piyoz va mozzarella.",
        "description_ru": "Курица BBQ, лук и моцарелла.",
        "description_en": "BBQ chicken, onion and mozzarella.",
        "price": 74000,
        "image_url": "https://images.unsplash.com/photo-1541745537411-b8046dc6d66c?auto=format&fit=crop&w=900&q=80",
    },
    {
        "category": "drinks",
        "name_uz": "Cola",
        "name_ru": "Кола",
        "name_en": "Cola",
        "description_uz": "Sovuq gazlangan ichimlik.",
        "description_ru": "Холодный газированный напиток.",
        "description_en": "Cold sparkling drink.",
        "price": 12000,
        "image_url": "https://images.unsplash.com/photo-1629203851122-3726ecdf080e?auto=format&fit=crop&w=900&q=80",
    },
    {
        "category": "drinks",
        "name_uz": "Fresh Lemonade",
        "name_ru": "Свежий лимонад",
        "name_en": "Fresh Lemonade",
        "description_uz": "Tabiiy limonad yalpiz bilan.",
        "description_ru": "Натуральный лимонад с мятой.",
        "description_en": "Fresh lemonade with mint.",
        "price": 18000,
        "image_url": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?auto=format&fit=crop&w=900&q=80",
    },
]


class Database:
    def __init__(self, path: str) -> None:
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def init(self) -> None:
        with closing(self.connect()) as connection:
            cursor = connection.cursor()
            cursor.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    name TEXT,
                    phone TEXT,
                    city TEXT,
                    language TEXT NOT NULL DEFAULT 'en',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    name_uz TEXT NOT NULL,
                    name_ru TEXT NOT NULL,
                    name_en TEXT NOT NULL,
                    description_uz TEXT NOT NULL,
                    description_ru TEXT NOT NULL,
                    description_en TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    image_url TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'CREATED',
                    total_amount INTEGER NOT NULL,
                    currency TEXT NOT NULL DEFAULT 'UZS',
                    location_label TEXT,
                    latitude REAL,
                    longitude REAL,
                    source TEXT NOT NULL DEFAULT 'webapp',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );

                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price INTEGER NOT NULL,
                    total_price INTEGER NOT NULL,
                    product_snapshot_json TEXT NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders(id),
                    FOREIGN KEY (product_id) REFERENCES products(id)
                );

                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    provider TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    payment_url TEXT,
                    external_id TEXT,
                    raw_payload TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders(id)
                );
                """
            )
            self._ensure_seed_products(cursor)
            connection.commit()

    def _ensure_seed_products(self, cursor: sqlite3.Cursor) -> None:
        count = cursor.execute("SELECT COUNT(*) AS count FROM products").fetchone()["count"]
        if count:
            return

        cursor.executemany(
            """
            INSERT INTO products (
                category, name_uz, name_ru, name_en,
                description_uz, description_ru, description_en,
                price, image_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    item["category"],
                    item["name_uz"],
                    item["name_ru"],
                    item["name_en"],
                    item["description_uz"],
                    item["description_ru"],
                    item["description_en"],
                    item["price"],
                    item["image_url"],
                )
                for item in DEFAULT_PRODUCTS
            ],
        )

    def upsert_user(
        self,
        user_id: int,
        *,
        language: str,
        name: str | None = None,
        phone: str | None = None,
        city: str | None = None,
    ) -> dict:
        now = datetime.now(UTC).isoformat()
        with closing(self.connect()) as connection:
            existing = connection.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            if existing:
                connection.execute(
                    """
                    UPDATE users
                    SET name = COALESCE(?, name),
                        phone = COALESCE(?, phone),
                        city = COALESCE(?, city),
                        language = ?,
                        updated_at = ?
                    WHERE user_id = ?
                    """,
                    (name, phone, city, language, now, user_id),
                )
            else:
                connection.execute(
                    """
                    INSERT INTO users (user_id, name, phone, city, language, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, name, phone, city, language, now, now),
                )
            connection.commit()
        return self.get_user(user_id)

    def get_user(self, user_id: int) -> dict | None:
        with closing(self.connect()) as connection:
            row = connection.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else None

    def list_products(self, language: str) -> list[dict]:
        safe_language = language if language in {"uz", "ru", "en"} else "en"
        with closing(self.connect()) as connection:
            rows = connection.execute(
                """
                SELECT id, category, price, image_url,
                       name_uz, name_ru, name_en,
                       description_uz, description_ru, description_en
                FROM products
                WHERE is_active = 1
                ORDER BY category, id
                """
            ).fetchall()
        return [
            {
                "id": row["id"],
                "category": row["category"],
                "price": row["price"],
                "image_url": row["image_url"],
                "name": row[f"name_{safe_language}"],
                "description": row[f"description_{safe_language}"],
            }
            for row in rows
        ]

    def _product_rows(self, product_ids: list[int]) -> dict[int, dict]:
        if not product_ids:
            return {}
        placeholders = ",".join("?" for _ in product_ids)
        with closing(self.connect()) as connection:
            rows = connection.execute(
                f"SELECT * FROM products WHERE id IN ({placeholders}) AND is_active = 1",
                tuple(product_ids),
            ).fetchall()
        return {row["id"]: dict(row) for row in rows}

    def create_order(
        self,
        *,
        user_id: int,
        language: str,
        items: list[dict],
        location_label: str | None,
        latitude: float | None,
        longitude: float | None,
    ) -> dict:
        rows = self._product_rows([int(item["product_id"]) for item in items])
        if not rows:
            raise ValueError("No valid products were provided.")

        secure_items: list[dict] = []
        total_amount = 0
        safe_language = language if language in {"uz", "ru", "en"} else "en"
        for item in items:
            product_id = int(item["product_id"])
            quantity = max(1, int(item["quantity"]))
            product = rows.get(product_id)
            if not product:
                raise ValueError(f"Product {product_id} is not available.")

            unit_price = int(product["price"])
            line_total = unit_price * quantity
            total_amount += line_total
            secure_items.append(
                {
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "total_price": line_total,
                    "snapshot": {
                        "id": product_id,
                        "category": product["category"],
                        "name": product[f"name_{safe_language}"],
                        "price": unit_price,
                    },
                }
            )

        now = datetime.now(UTC).isoformat()
        with closing(self.connect()) as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO orders (
                    user_id, status, total_amount, location_label, latitude, longitude, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, "CREATED", total_amount, location_label, latitude, longitude, now, now),
            )
            order_id = cursor.lastrowid
            cursor.executemany(
                """
                INSERT INTO order_items (
                    order_id, product_id, quantity, unit_price, total_price, product_snapshot_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        order_id,
                        item["product_id"],
                        item["quantity"],
                        item["unit_price"],
                        item["total_price"],
                        json.dumps(item["snapshot"], ensure_ascii=False),
                    )
                    for item in secure_items
                ],
            )
            connection.commit()
        return self.get_order(order_id)

    def get_order(self, order_id: int) -> dict:
        with closing(self.connect()) as connection:
            order = connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
            if not order:
                raise ValueError("Order not found.")
            items = connection.execute(
                "SELECT * FROM order_items WHERE order_id = ? ORDER BY id",
                (order_id,),
            ).fetchall()
        result = dict(order)
        result["items"] = [
            {
                **json.loads(row["product_snapshot_json"]),
                "quantity": row["quantity"],
                "unit_price": row["unit_price"],
                "total_price": row["total_price"],
            }
            for row in items
        ]
        return result

    def create_payment(self, *, order_id: int, provider: str, amount: int, payment_url: str) -> dict:
        now = datetime.now(UTC).isoformat()
        with closing(self.connect()) as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO payments (order_id, provider, amount, status, payment_url, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (order_id, provider, amount, "PENDING", payment_url, now, now),
            )
            payment_id = cursor.lastrowid
            cursor.execute(
                "UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
                ("CREATED", now, order_id),
            )
            connection.commit()
        return self.get_payment(payment_id)

    def get_payment(self, payment_id: int) -> dict:
        with closing(self.connect()) as connection:
            row = connection.execute("SELECT * FROM payments WHERE id = ?", (payment_id,)).fetchone()
        if not row:
            raise ValueError("Payment not found.")
        return dict(row)

    def update_payment_status(
        self,
        *,
        provider: str,
        payment_id: int | None,
        status: str,
        raw_payload: dict,
        external_id: str | None = None,
    ) -> dict:
        now = datetime.now(UTC).isoformat()
        normalized_status = "PAID" if status.upper() == "PAID" else status.upper()
        with closing(self.connect()) as connection:
            if payment_id is not None:
                row = connection.execute(
                    "SELECT * FROM payments WHERE id = ? AND provider = ?",
                    (payment_id, provider),
                ).fetchone()
            else:
                row = connection.execute(
                    "SELECT * FROM payments WHERE external_id = ? AND provider = ?",
                    (external_id, provider),
                ).fetchone()
            if not row:
                raise ValueError("Payment not found.")

            connection.execute(
                """
                UPDATE payments
                SET status = ?, external_id = COALESCE(?, external_id), raw_payload = ?, updated_at = ?
                WHERE id = ?
                """,
                (normalized_status, external_id, json.dumps(raw_payload, ensure_ascii=False), now, row["id"]),
            )
            if normalized_status == "PAID":
                connection.execute(
                    "UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
                    ("PAID", now, row["order_id"]),
                )
            connection.commit()
        return self.get_payment(row["id"])

    def update_order_status(self, order_id: int, status: str) -> dict:
        normalized_status = status.upper()
        if normalized_status not in ORDER_STATUSES:
            raise ValueError("Invalid order status.")

        now = datetime.now(UTC).isoformat()
        with closing(self.connect()) as connection:
            row = connection.execute("SELECT id FROM orders WHERE id = ?", (order_id,)).fetchone()
            if not row:
                raise ValueError("Order not found.")
            connection.execute(
                "UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
                (normalized_status, now, order_id),
            )
            connection.commit()
        return self.get_order(order_id)

    def get_recent_orders(self, limit: int = 10) -> list[dict]:
        with closing(self.connect()) as connection:
            rows = connection.execute(
                """
                SELECT o.id, o.user_id, o.total_amount, o.status, o.created_at, u.name AS user_name
                FROM orders o
                JOIN users u ON u.user_id = o.user_id
                ORDER BY o.id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_user_orders(self, user_id: int, limit: int = 5) -> list[dict]:
        with closing(self.connect()) as connection:
            rows = connection.execute(
                """
                SELECT id, total_amount, status, created_at
                FROM orders
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_order_summary(self, order_id: int) -> dict:
        with closing(self.connect()) as connection:
            order = connection.execute(
                """
                SELECT o.*, u.name, u.phone, u.city, u.language, u.user_id
                FROM orders o
                JOIN users u ON u.user_id = o.user_id
                WHERE o.id = ?
                """,
                (order_id,),
            ).fetchone()
            if not order:
                raise ValueError("Order not found.")

            items = connection.execute(
                "SELECT product_snapshot_json, quantity, unit_price, total_price FROM order_items WHERE order_id = ?",
                (order_id,),
            ).fetchall()
            payments = connection.execute(
                "SELECT provider, status, payment_url FROM payments WHERE order_id = ? ORDER BY id DESC",
                (order_id,),
            ).fetchall()

        maps_url = None
        if order["latitude"] is not None and order["longitude"] is not None:
            maps_url = f"https://maps.google.com/?q={order['latitude']},{order['longitude']}"

        return {
            "order_id": order["id"],
            "status": order["status"],
            "total_amount": order["total_amount"],
            "location_label": order["location_label"],
            "maps_url": maps_url,
            "user": {
                "id": order["user_id"],
                "name": order["name"],
                "phone": order["phone"],
                "city": order["city"],
                "language": order["language"],
            },
            "items": [
                {
                    **json.loads(row["product_snapshot_json"]),
                    "quantity": row["quantity"],
                    "unit_price": row["unit_price"],
                    "total_price": row["total_price"],
                }
                for row in items
            ],
            "payments": [dict(payment) for payment in payments],
        }

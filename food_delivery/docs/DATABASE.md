# Database Sxema va Qoidalar

## Aloqalar (Relationships)

```
users (1) ──── (N) addresses
users (1) ──── (1) carts
users (1) ──── (N) orders
carts (1) ──── (N) cart_items
cart_items (N) ──── (1) products
orders (1) ──── (N) order_items
orders (N) ──── (1) addresses
orders (N) ──── (1) branches
products (1) ──── (N) product_variants
products (1) ──── (N) product_modifiers
categories (1) ──── (N) products
```

## Indekslar

```sql
-- users
CREATE INDEX idx_users_telegram_id ON users(telegram_id);

-- products
CREATE INDEX idx_products_category_id ON products(category_id);
CREATE INDEX idx_products_is_active ON products(is_active);

-- orders
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE UNIQUE INDEX idx_orders_idempotency ON orders(idempotency_key);

-- cart_items
CREATE INDEX idx_cart_items_cart_id ON cart_items(cart_id);
```

## snapshot_json nima uchun?

`cart_items.snapshot_json` va `order_items.snapshot_json` — buyurtma paytidagi mahsulot ma'lumotlarining nusxasi.

**Sabab:** Agar mahsulot narxi keyinroq o'zgarsa, eski buyurtmalar to'g'ri narxda ko'rinishi kerak.

```json
{
  "product_name_uz": "Classic Burger",
  "product_name_ru": "Классик Бургер",
  "variant_name_uz": "O'rta",
  "unit_price": "35000.00",
  "weight_grams": 300,
  "image_url": "/static/images/classic.jpg"
}
```

## Migration qoidalari

- Har migration faqat bitta logik o'zgarish
- `downgrade()` funksiyasi to'liq yoziladi
- Production da avtomatik migrate bo'lmaydi

## Soft delete

`users`, `products`, `categories` jadvallarida `is_active` field bor.
Hech narsa haqiqatda o'chirilmaydi — faqat `is_active=False` qilinadi.

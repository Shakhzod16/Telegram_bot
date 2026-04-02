# 06 — Database Roadmap

> **Hozirgi holat:** `database/models.py` va `backend/models.py` mavjud — ayrim jadvallar bor.
> **Maqsad:** Yetishmayotgan jadvallar va fieldlar qo'shish.

---

## 6.1 Jadvallar Holati

| Jadval | Holat | Sprint |
|--------|-------|--------|
| `users` | 🟡 Mavjud — to'ldirish kerak | Sprint 1 |
| `categories` | ✅ Mavjud | — |
| `products` | ✅ Mavjud | — |
| `cart_items` | 🟡 Mavjud — tekshirish kerak | Sprint 1 |
| `orders` | 🟡 Mavjud — field qo'shish kerak | Sprint 1-2 |
| `order_items` | ✅ Mavjud | — |
| `order_status_history` | ❌ Yo'q | Sprint 2 |
| `payments` | 🟡 Mavjud — to'ldirish kerak | Sprint 2 |
| `addresses` | ❌ Yo'q | Sprint 3 |
| `promo_codes` | ❌ Yo'q | Sprint 3 |
| `promo_code_uses` | ❌ Yo'q | Sprint 3 |
| `referrals` | ❌ Yo'q | Sprint 3 |
| `branches` | ❌ Yo'q | Future |
| `notifications` | ❌ Yo'q | Future |

---

## 6.2 Jadvallar Tafsiloti

### `users`
```sql
CREATE TABLE users (
    id              INTEGER PRIMARY KEY,
    telegram_id     BIGINT UNIQUE NOT NULL,     -- Telegram user ID
    full_name       VARCHAR(255),
    phone           VARCHAR(20) UNIQUE,         -- +998XXXXXXXXX formatda
    city            VARCHAR(100),
    language        VARCHAR(10) DEFAULT 'uz',   -- uz / ru / en
    referral_code   VARCHAR(20) UNIQUE,         -- ❌ qo'shish kerak
    bonus_balance   INTEGER DEFAULT 0,           -- ❌ qo'shish kerak (so'm)
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);
```

**Qo'shish kerak:**
- [ ] `referral_code` — unique short UUID
- [ ] `bonus_balance` — referral/promo bonus
- [ ] `is_active` — ban qilish imkoni

---

### `categories`
```sql
CREATE TABLE categories (
    id          INTEGER PRIMARY KEY,
    name_uz     VARCHAR(255) NOT NULL,
    name_ru     VARCHAR(255),
    name_en     VARCHAR(255),
    image_url   TEXT,
    sort_order  INTEGER DEFAULT 0,
    is_active   BOOLEAN DEFAULT TRUE
);
```
✅ Asosiy maydonlar mavjud bo'lishi kerak. Tekshiring.

---

### `products`
```sql
CREATE TABLE products (
    id              INTEGER PRIMARY KEY,
    category_id     INTEGER REFERENCES categories(id),
    name_uz         VARCHAR(255) NOT NULL,
    name_ru         VARCHAR(255),
    name_en         VARCHAR(255),
    description_uz  TEXT,
    description_ru  TEXT,
    price           INTEGER NOT NULL,           -- so'm da
    image_url       TEXT,
    is_available    BOOLEAN DEFAULT TRUE,
    sort_order      INTEGER DEFAULT 0,
    created_at      TIMESTAMP DEFAULT NOW()
);
```
✅ Asosiy mavjud. `is_available` borligini tekshiring.

---

### `cart_items`
```sql
CREATE TABLE cart_items (
    id          INTEGER PRIMARY KEY,
    user_id     INTEGER REFERENCES users(id),
    product_id  INTEGER REFERENCES products(id),
    quantity    INTEGER DEFAULT 1 CHECK (quantity > 0),
    added_at    TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, product_id)              -- bir mahsulot bir marta
);
```

**Tekshirish:**
- [ ] `UNIQUE(user_id, product_id)` constraint bormi?
- [ ] `quantity > 0` check bormi?

---

### `orders`
```sql
CREATE TABLE orders (
    id                  INTEGER PRIMARY KEY,
    user_id             INTEGER REFERENCES users(id),
    address_id          INTEGER REFERENCES addresses(id),   -- ❌ qo'shish kerak
    promo_code_id       INTEGER REFERENCES promo_codes(id), -- ❌ qo'shish kerak
    status              VARCHAR(20) DEFAULT 'PENDING',
    payment_method      VARCHAR(20) DEFAULT 'CLICK',        -- ❌ qo'shish kerak
    subtotal            INTEGER NOT NULL,
    delivery_fee        INTEGER DEFAULT 0,
    discount_amount     INTEGER DEFAULT 0,                   -- ❌ qo'shish kerak
    total_amount        INTEGER NOT NULL,
    notes               TEXT,
    delivery_address    TEXT,
    latitude            FLOAT,
    longitude           FLOAT,
    estimated_delivery_at TIMESTAMP,                         -- ❌ qo'shish kerak
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);
```

**Qo'shish kerak:**
- [ ] `payment_method` — CLICK / PAYME / CASH
- [ ] `discount_amount` — promo chegirma
- [ ] `address_id` FK (addresses yaratilgandan keyin)
- [ ] `promo_code_id` FK (promo_codes yaratilgandan keyin)
- [ ] `estimated_delivery_at`

---

### `order_items`
```sql
CREATE TABLE order_items (
    id              INTEGER PRIMARY KEY,
    order_id        INTEGER REFERENCES orders(id),
    product_id      INTEGER REFERENCES products(id),
    quantity        INTEGER NOT NULL,
    price_at_order  INTEGER NOT NULL    -- buyurtma paytidagi narx
);
```
✅ `price_at_order` borligini tekshiring — muhim!

---

### `order_status_history` ❌ Yaratish kerak
```sql
CREATE TABLE order_status_history (
    id          INTEGER PRIMARY KEY,
    order_id    INTEGER REFERENCES orders(id) NOT NULL,
    old_status  VARCHAR(20),
    new_status  VARCHAR(20) NOT NULL,
    changed_by  VARCHAR(100),   -- "admin" yoki user telegram_id
    notes       TEXT,
    changed_at  TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_order_status_history_order_id 
ON order_status_history(order_id);
```

- [ ] Migration: `add_order_status_history`
- [ ] `OrderStatusHistory` model yaratish

---

### `payments`
```sql
CREATE TABLE payments (
    id                  INTEGER PRIMARY KEY,
    order_id            INTEGER UNIQUE REFERENCES orders(id),  -- UNIQUE!
    payment_method      VARCHAR(20) NOT NULL,
    amount              INTEGER NOT NULL,
    status              VARCHAR(20) DEFAULT 'PENDING',
    transaction_id      VARCHAR(255),
    provider_data       JSON,               -- Click/Payme response
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);
```

**Tekshirish va qo'shish:**
- [ ] `order_id UNIQUE` — idempotency uchun
- [ ] `provider_data JSON` — Click/Payme to'liq response saqlash

---

### `addresses` ❌ Yaratish kerak
```sql
CREATE TABLE addresses (
    id              INTEGER PRIMARY KEY,
    user_id         INTEGER REFERENCES users(id) NOT NULL,
    label           VARCHAR(100),      -- "Uy", "Ish", "Do'st uy"
    address_text    TEXT NOT NULL,
    latitude        FLOAT,
    longitude       FLOAT,
    is_default      BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_addresses_user_id ON addresses(user_id);
```

- [ ] Migration: `add_addresses_table`
- [ ] `Address` model yaratish
- [ ] Max 5 ta check — service levelda

---

### `promo_codes` ❌ Yaratish kerak
```sql
CREATE TABLE promo_codes (
    id                  INTEGER PRIMARY KEY,
    code                VARCHAR(50) UNIQUE NOT NULL,
    type                VARCHAR(20) NOT NULL,    -- 'percent' yoki 'fixed'
    value               FLOAT NOT NULL,           -- 10 (%) yoki 5000 (so'm)
    min_order_amount    INTEGER DEFAULT 0,
    max_uses            INTEGER DEFAULT 1,
    used_count          INTEGER DEFAULT 0,
    expires_at          TIMESTAMP,
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMP DEFAULT NOW()
);
```

---

### `promo_code_uses` ❌ Yaratish kerak
```sql
CREATE TABLE promo_code_uses (
    id              INTEGER PRIMARY KEY,
    promo_code_id   INTEGER REFERENCES promo_codes(id),
    user_id         INTEGER REFERENCES users(id),
    order_id        INTEGER REFERENCES orders(id),
    used_at         TIMESTAMP DEFAULT NOW(),
    UNIQUE(promo_code_id, user_id)          -- bir user bir kodni bir marta
);
```

---

### `referrals` ❌ Yaratish kerak
```sql
CREATE TABLE referrals (
    id              INTEGER PRIMARY KEY,
    referrer_id     INTEGER REFERENCES users(id),   -- taklif qilgan
    referred_id     INTEGER UNIQUE REFERENCES users(id),  -- taklif qilingan
    bonus_given     BOOLEAN DEFAULT FALSE,
    bonus_amount    INTEGER DEFAULT 0,
    created_at      TIMESTAMP DEFAULT NOW()
);
```

---

### `branches` (Future)
```sql
-- Sprint 4+ da qo'shiladi
CREATE TABLE branches (
    id              INTEGER PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    address         TEXT,
    phone           VARCHAR(20),
    latitude        FLOAT,
    longitude       FLOAT,
    is_active       BOOLEAN DEFAULT TRUE,
    working_hours   JSON    -- {"mon": "09:00-22:00", ...}
);
```

---

### `notifications` (Future)
```sql
-- Sprint 4+ da qo'shiladi
CREATE TABLE notifications (
    id          INTEGER PRIMARY KEY,
    user_id     INTEGER REFERENCES users(id),
    order_id    INTEGER REFERENCES orders(id),
    type        VARCHAR(50),    -- 'order_status', 'promo', 'general'
    title       VARCHAR(255),
    message     TEXT,
    is_sent     BOOLEAN DEFAULT FALSE,
    sent_at     TIMESTAMP,
    created_at  TIMESTAMP DEFAULT NOW()
);
```

---

## 6.3 Muhim Indexlar

```sql
-- Ishlash tezligi uchun
CREATE UNIQUE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE UNIQUE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_cart_items_user_id ON cart_items(user_id);
CREATE UNIQUE INDEX idx_payments_order_id ON payments(order_id);
CREATE UNIQUE INDEX idx_promo_code_uses_user ON promo_code_uses(promo_code_id, user_id);
CREATE UNIQUE INDEX idx_referrals_referred ON referrals(referred_id);
```

---

## 6.4 Migration Plan

```bash
# Sprint 1
alembic revision --autogenerate -m "001_initial_tables"
# users, categories, products, cart_items, orders, order_items, payments

alembic revision --autogenerate -m "002_add_missing_user_fields"
# users.referral_code, users.bonus_balance

alembic revision --autogenerate -m "003_add_order_payment_method"
# orders.payment_method, orders.discount_amount, orders.estimated_delivery_at

# Sprint 2
alembic revision --autogenerate -m "004_add_order_status_history"
# order_status_history jadval

alembic revision --autogenerate -m "005_payments_unique_order"
# payments.order_id UNIQUE constraint

# Sprint 3
alembic revision --autogenerate -m "006_add_addresses"
# addresses jadval

alembic revision --autogenerate -m "007_add_promo_system"
# promo_codes, promo_code_uses

alembic revision --autogenerate -m "008_add_referral_system"
# referrals jadval, users.bonus_balance (agar 002 da qo'shilmagan bo'lsa)

# Future
alembic revision --autogenerate -m "009_add_branches"
alembic revision --autogenerate -m "010_add_notifications"
```

---

## 6.5 Migration Checklist

### Sprint 1
- [ ] `001_initial_tables` — `alembic upgrade head` xatosiz
- [ ] `002_add_missing_user_fields` — `users` jadval to'liq
- [ ] `003_add_order_payment_method` — `orders` jadval to'liq

### Sprint 2
- [ ] `004_add_order_status_history` — jadval yaratilgan
- [ ] `005_payments_unique_order` — UNIQUE constraint qo'shilgan

### Sprint 3
- [ ] `006_add_addresses` — jadval yaratilgan
- [ ] `007_add_promo_system` — 2 jadval yaratilgan
- [ ] `008_add_referral_system` — jadval yaratilgan

---

[← Business Rules](./05_business_rules.md) | [Keyingi: API Roadmap →](./07_api_roadmap.md)

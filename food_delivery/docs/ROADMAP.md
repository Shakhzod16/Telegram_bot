# Loyiha Roadmap — Telegram Food Delivery WebApp

## Umumiy holat

| Phase | Nomi | Holat | Muddat |
|-------|------|-------|--------|
| 1 | Foundation | ⬜ Boshlanmagan | 1-hafta |
| 2 | Auth + Catalog | ⬜ Boshlanmagan | 1-hafta |
| 3 | Cart + Address | ⬜ Boshlanmagan | 1-hafta |
| 4 | Checkout + Orders | ⬜ Boshlanmagan | 1-hafta |
| 5 | Profile + Admin | ⬜ Boshlanmagan | 1-hafta |

---

## PHASE 1 — Foundation (1-hafta)

### Maqsad
Loyihaning asosi: papkalar, docker, migrations, bot va backend ishga tushadi.

### Vazifalar

#### Loyiha tuzilmasi
- [ ] `food_delivery/` asosiy papka yaratildi
- [ ] `app/`, `bot/`, `tests/`, `docs/`, `scripts/`, `alembic/` papkalar yaratildi
- [ ] `docker-compose.yml` yozildi (postgres + redis)
- [ ] `requirements.txt` yozildi (barcha kutubxonalar)
- [ ] `.env.example` yozildi
- [ ] `.env` real tokenlar bilan to'ldirildi
- [ ] `.gitignore` yozildi
- [ ] `run_dev.py` yozildi

#### Backend asosi
- [ ] `app/core/config.py` — pydantic-settings bilan
- [ ] `app/core/logging.py` — JSON structured logging
- [ ] `app/core/exceptions.py` — custom exceptions + middleware
- [ ] `app/db/session.py` — async SQLAlchemy engine
- [ ] `app/main.py` — FastAPI app, routerlar ulanadi
- [ ] `GET /health` endpoint ishlaydi

#### Database
- [ ] `alembic.ini` konfiguratsiya
- [ ] `alembic/env.py` async support bilan
- [ ] `app/models/user.py` modeli yozildi
- [ ] `alembic/versions/001_create_users.py` migration yozildi
- [ ] `alembic upgrade head` muvaffaqiyatli ishladi

#### Bot asosi
- [ ] `bot/main.py` — Aiogram 3.x dispatcher
- [ ] `bot/handlers/start.py` — `/start` handler
- [ ] `bot/keyboards/main.py` — WebApp ochuvchi tugma
- [ ] Bot `/start` ga javob beradi
- [ ] WebApp tugmasi ishlaydi

#### Tekshirish
- [ ] `docker-compose up -d db redis` muvaffaqiyatli
- [ ] `uvicorn app.main:app --reload` muvaffaqiyatli
- [ ] `python -m bot.main` muvaffaqiyatli
- [ ] `GET /health` → `{"status": "ok"}` qaytaradi
- [ ] Bot `/start` → xabar + tugma ko'rsatadi

---

## PHASE 2 — Auth + Catalog (2-hafta)

### Maqsad
Foydalanuvchi autentifikatsiyasi va mahsulotlar katalogi.

### Vazifalar

#### Authentication
- [ ] `app/core/security.py` — HMAC-SHA256 initData verify
- [ ] `app/core/security.py` — JWT create/decode
- [ ] `app/api/deps.py` — `get_current_user` dependency
- [ ] `app/repositories/user.py` — user CRUD
- [ ] `app/schemas/auth.py` — request/response sxemalar
- [ ] `app/services/auth.py` — auth business logic
- [ ] `POST /api/v1/auth/telegram/init` ishlaydi
- [ ] Invalid initData → 401 qaytaradi
- [ ] Rate limiting: 5 req/min per IP

#### Katalog modellari
- [ ] `app/models/category.py`
- [ ] `app/models/product.py` (variants + modifiers bilan)
- [ ] `alembic/versions/002_create_catalog.py` migration
- [ ] `alembic upgrade head` muvaffaqiyatli

#### Katalog API
- [ ] `app/repositories/product.py` — catalog queries
- [ ] `app/schemas/catalog.py` — Category, Product, Variant sxemalar
- [ ] `app/services/catalog.py` — business logic
- [ ] `GET /api/v1/categories` ishlaydi
- [ ] `GET /api/v1/products` — pagination, filter ishlaydi
- [ ] `GET /api/v1/products/{id}` — variants bilan ishlaydi

#### Seed data
- [ ] `scripts/seed.py` yozildi
- [ ] 5 kategoriya yaratildi
- [ ] 20 mahsulot (har kategoriyada 4 ta) yaratildi
- [ ] Har mahsulotda 2-3 variant yaratildi
- [ ] `python scripts/seed.py` muvaffaqiyatli ishladi

#### WebApp — Home ekrani
- [ ] `app/webapp/templates/base.html` — Telegram SDK bilan
- [ ] `app/webapp/templates/index.html` — catalog UI
- [ ] `app/webapp/static/js/api.js` — central fetch wrapper
- [ ] `app/webapp/static/js/auth.js` — initData → JWT
- [ ] `app/webapp/static/js/catalog.js` — categories + products
- [ ] Category slider ko'rsatiladi
- [ ] Product cardlar ko'rsatiladi
- [ ] Product detail bottom sheet ishlaydi
- [ ] Loading skeleton ishlaydi

#### Tekshirish
- [ ] WebApp ochilganda JWT olinadi
- [ ] Kategoriyalar to'g'ri ko'rsatiladi
- [ ] Mahsulotlar filterlash ishlaydi
- [ ] Unauthorized request → 401

---

## PHASE 3 — Cart + Address (3-hafta)

### Maqsad
Savat va manzil boshqaruvi.

### Vazifalar

#### Cart (Redis-first)
- [ ] `app/models/cart.py` — carts + cart_items
- [ ] `alembic/versions/003_create_cart.py` migration
- [ ] `app/services/cart.py` — Redis CRUD operatsiyalar
- [ ] `GET /api/v1/cart` ishlaydi
- [ ] `POST /api/v1/cart/items` ishlaydi
- [ ] `PATCH /api/v1/cart/items/{id}` ishlaydi
- [ ] `DELETE /api/v1/cart/items/{id}` ishlaydi
- [ ] `DELETE /api/v1/cart/clear` ishlaydi
- [ ] Cart badge WebApp navbar da yangilanadi
- [ ] Cart TTL 7 kun Redis da

#### Address moduli
- [ ] `app/models/address.py` + `app/models/branch.py`
- [ ] `alembic/versions/004_create_addresses.py` migration
- [ ] `app/services/address.py` — delivery zone check
- [ ] `GET /api/v1/addresses` ishlaydi
- [ ] `POST /api/v1/addresses` ishlaydi
- [ ] `PATCH /api/v1/addresses/{id}` ishlaydi
- [ ] `DELETE /api/v1/addresses/{id}` ishlaydi
- [ ] Delivery zone check ishlaydi (radius km)

#### WebApp — Cart va Address ekranlar
- [ ] `app/webapp/templates/cart.html`
- [ ] `app/webapp/static/js/cart.js`
- [ ] Cart items list ishlaydi
- [ ] Quantity +/- ishlaydi
- [ ] Subtotal, delivery fee, total hisob ishlaydi
- [ ] Empty cart state ishlaydi
- [ ] `app/webapp/templates/address.html`
- [ ] Address forma ishlaydi
- [ ] "Joylashuvimni aniqlash" (geolocation) ishlaydi
- [ ] Address modal birinchi kirishda chiqadi

#### Tekshirish
- [ ] Redis da cart ma'lumotlari to'g'ri saqlanadi
- [ ] Cart count badge real vaqtda yangilanadi
- [ ] Geolocation ruxsat so'rovi ishlaydi
- [ ] Default address to'g'ri tanlanadi

---

## PHASE 4 — Checkout + Orders (4-hafta)

### Maqsad
Buyurtma berish va buyurtmalar tarixi.

### Vazifalar

#### Checkout
- [ ] `app/models/order.py` — orders + order_items + promos
- [ ] `alembic/versions/005_create_orders.py` migration
- [ ] `app/services/checkout.py` — idempotent logic
- [ ] `POST /api/v1/checkout/preview` ishlaydi
- [ ] `POST /api/v1/orders` ishlaydi
- [ ] Narx DB dan qayta verify qilinadi
- [ ] Idempotency key duplikatni bloklaydi
- [ ] Min order amount tekshiriladi
- [ ] Branch open/close tekshiriladi
- [ ] Promo kod qo'llaniladi

#### Orders API
- [ ] `app/repositories/order.py`
- [ ] `app/services/order.py`
- [ ] `GET /api/v1/orders` — paginated ishlaydi
- [ ] `GET /api/v1/orders/{id}` ishlaydi
- [ ] `POST /api/v1/orders/{id}/cancel` ishlaydi
- [ ] `POST /api/v1/orders/{id}/repeat` ishlaydi

#### Bot notifications
- [ ] `bot/handlers/notifications.py`
- [ ] `app/services/notification.py`
- [ ] Order yaratilganda bot xabar yuboradi
- [ ] Status o'zgarishida bot xabar yuboradi
- [ ] Xabar formati to'g'ri (emoji, narxlar, manzil)

#### WebApp ekranlar
- [ ] `app/webapp/templates/checkout.html`
- [ ] `app/webapp/templates/orders.html`
- [ ] `app/webapp/templates/order_detail.html`
- [ ] Checkout forma ishlaydi
- [ ] Status badge ranglari to'g'ri
- [ ] "Qayta buyurtma" tugmasi ishlaydi

#### Tekshirish
- [ ] To'liq order flow: catalog → cart → checkout → bot xabar
- [ ] Duplicate buyurtma bloklanadi
- [ ] Bot xabar formati to'g'ri

---

## PHASE 5 — Profile + Admin + Tests (5-hafta)

### Maqsad
Profil, admin panel va testlar.

### Vazifalar

#### Profile
- [ ] `GET /api/v1/profile` ishlaydi
- [ ] `PATCH /api/v1/profile` ishlaydi
- [ ] `app/webapp/templates/profile.html`
- [ ] Language switch (uz/ru) ishlaydi
- [ ] Saved addresses ro'yxati ishlaydi

#### Admin panel
- [ ] Admin middleware (is_admin check)
- [ ] Products CRUD admin endpointlar
- [ ] Categories CRUD admin endpointlar
- [ ] Branches CRUD admin endpointlar
- [ ] Promos CRUD admin endpointlar
- [ ] Orders board (`GET /api/v1/admin/orders`)
- [ ] Status o'zgartirish (`PATCH /api/v1/admin/orders/{id}/status`)
- [ ] `app/webapp/templates/admin/orders.html`
- [ ] Admin orders board 30s auto-refresh

#### Tests
- [ ] `tests/conftest.py` — fixtures
- [ ] `tests/test_auth.py` — 3+ test
- [ ] `tests/test_cart.py` — 5+ test
- [ ] `tests/test_checkout.py` — 5+ test
- [ ] `tests/test_catalog.py` — 3+ test
- [ ] `pytest` muvaffaqiyatli o'tadi

#### Deploy tayyorligi
- [ ] `.env.example` to'liq
- [ ] `docker-compose.yml` production config
- [ ] Health check endpoint
- [ ] Graceful shutdown
- [ ] README.md yozildi

---

## Status belgilari

| Belgi | Ma'no |
|-------|-------|
| ⬜ | Boshlanmagan |
| 🔄 | Jarayonda |
| ✅ | Tugallangan |
| ❌ | Xato/blok |

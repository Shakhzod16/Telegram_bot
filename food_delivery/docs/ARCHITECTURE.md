# Arxitektura — Telegram Food Delivery WebApp

## Umumiy ko'rinish

```
[Telegram App]
     |
     | WebApp open
     ↓
[Telegram WebApp (HTML/JS)]
     |
     | HTTP + JWT
     ↓
[FastAPI Backend]
     |
     ├── [PostgreSQL] — asosiy ma'lumotlar
     ├── [Redis]      — cart, sessions, rate limit
     └── [Aiogram Bot] ← bot xabarlar
```

## Loyiha strukturasi

```
food_delivery/
├── app/              ← FastAPI backend
│   ├── api/          ← HTTP endpointlar (faqat request/response)
│   ├── core/         ← config, security, logging, exceptions
│   ├── db/           ← database session
│   ├── models/       ← SQLAlchemy ORM modellari
│   ├── repositories/ ← DB so'rovlari (faqat CRUD)
│   ├── schemas/      ← Pydantic v2 sxemalar
│   ├── services/     ← business logic (FAQAT shu yerda)
│   └── webapp/       ← Jinja2 templates + static files
├── bot/              ← Aiogram bot
│   ├── handlers/     ← xabarlar, commandalar
│   ├── keyboards/    ← tugmalar
│   └── middlewares/  ← logging, auth
├── alembic/          ← DB migrations
├── tests/            ← pytest
└── scripts/          ← seed, utilities
```

## Layer arxitekturasi

```
HTTP Request
    ↓
[API Layer] — faqat: request validatsiya, response format, HTTP status
    ↓
[Service Layer] — business logic, qarorlar, validatsiyalar
    ↓
[Repository Layer] — faqat DB/Redis operatsiyalar
    ↓
[Database/Redis]
```

### Qoida: har layer faqat o'zining ishi

| Layer | Qiladi | Qilmaydi |
|-------|--------|----------|
| API | Request olish, response qaytarish | Hisoblash, DB so'rash |
| Service | Business logic | HTTP status, DB so'rash |
| Repository | DB/Redis CRUD | Business logic |

## Cart arxitekturasi (Redis-first)

```
User add to cart
      ↓
[CartService]
      |
      ├── Redis HSET cart:{user_id} → {item_json}
      ├── Redis SETEX cart_count:{user_id} → {count}
      └── Background: sync to PostgreSQL every 30min

User checkout
      ↓
[CheckoutService]
      |
      ├── Redis dan cart o'qish
      ├── DB dan narxlarni verify
      ├── Transaction: order write + cart clear
      └── Redis cart delete
```

## Auth oqimi

```
WebApp ochiladi
      ↓
Telegram.WebApp.initData → backendga yuboriladi
      ↓
[SecurityService.verify_init_data()]
  HMAC-SHA256(BOT_TOKEN, data_check_string) == hash?
      |
    YES ↓
  User topiladi yoki yaratiladi
      ↓
  JWT token qaytariladi (expire: 7 kun)
      ↓
  Barcha keyingi so'rovlarda: Authorization: Bearer {jwt}
```

## Order status oqimi

```
draft → pending → confirmed → preparing → ready → on_the_way → delivered
                     ↓
                 cancelled (faqat pending dan)
```

## Xavfsizlik

| Xatar | Himoya |
|-------|--------|
| Fake initData | HMAC-SHA256 verify |
| Client narx manipulation | Checkout da DB narxi qayta verify |
| Duplicate order | Idempotency key (UUID) |
| Brute force | Redis rate limit |
| Admin access | is_admin DB field + middleware |
| SQL injection | SQLAlchemy ORM parametrlar |

## Technology tanlov sabablari

| Texnologiya | Sabab |
|-------------|-------|
| FastAPI | Async, type hints, avtomatik docs |
| Aiogram 3.x | Zamonaviy async Telegram bot framework |
| SQLAlchemy async | ORM + async support |
| Redis | Cart uchun ultra-fast, TTL support |
| Pydantic v2 | Tez validatsiya, type-safe |
| Vanilla JS | Framework yo'q = kichik bundle, tez WebApp |

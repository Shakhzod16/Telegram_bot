# 07 — API Endpoint Roadmap

> **Hozirgi holat:** Barcha endpoint lar `backend/main.py` da. Routerlarga bo'lish kerak.
> **Maqsad:** Har endpoint uchun to'liq tafsilot + holat ko'rsatish.

---

## Endpoint Holatlari

| Belgi | Ma'no |
|-------|-------|
| ✅ | Hozir ishlaydi |
| 🟡 | Bor lekin to'liq emas |
| ❌ | Hali yo'q |

---

## Auth / Bootstrap

| Method | Path | Maqsad | Auth | Admin | Holat |
|--------|------|--------|------|-------|-------|
| `POST` | `/bootstrap` | WebApp initData verify + user/products/texts qaytarish | No | No | ✅ (`main.py:247`) |
| `POST` | `/auth/telegram` | Bot orqali user register/login | No | No | 🟡 (onboarding da qilinadi) |

### `POST /bootstrap` — hozir ishlaydi ✅
```python
# backend/main.py:247 — mavjud
# Request: { "init_data": "..." }
# Response: { "user": {...}, "products": [...], "categories": [...], "texts": {...} }
# Yaxshilash kerak: initData HMAC verify (hozir yo'q?)
```

- [x] Endpoint ishlaydi
- [ ] initData HMAC verify qo'shilgan
- [ ] Response schema typed

---

## Users

| Method | Path | Maqsad | Auth | Admin | Holat |
|--------|------|--------|------|-------|-------|
| `GET` | `/users/me` | Hozirgi user ma'lumoti | Yes | No | ❌ |
| `PATCH` | `/users/me` | Profil yangilash | Yes | No | ❌ |
| `GET` | `/users/me/referral` | Referral kod va statistika | Yes | No | ❌ |

### `GET /users/me` — yaratish kerak ❌
```python
# backend/routers/users.py
@router.get("/users/me", response_model=UserRead)
async def get_me(telegram_id: int, repo: UserRepository = Depends()):
    user = await repo.get_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(404, "Foydalanuvchi topilmadi")
    return user
```

- [ ] Endpoint yaratilgan
- [ ] `UserRead` schema mavjud
- [ ] Test yozilgan

---

## Menu (Categories & Products)

| Method | Path | Maqsad | Auth | Admin | Holat |
|--------|------|--------|------|-------|-------|
| `GET` | `/categories` | Barcha aktiv kategoriyalar | No | No | ✅ (bootstrap da) |
| `GET` | `/products` | Mahsulotlar (filter: category_id) | No | No | ✅ (bootstrap da) |
| `GET` | `/products/{id}` | Mahsulot detail | No | No | ❌ |

### `GET /products?category_id=1` — bootstrap da bor ✅
```python
# Hozir bootstrap da barcha mahsulotlar qaytariladi
# Alohida endpoint kerak: pagination va filter uchun
```

- [x] Mahsulotlar qaytariladi (bootstrap orqali)
- [ ] Alohida `GET /products` endpoint
- [ ] `category_id` filter parametri
- [ ] Pagination (page, limit)

---

## Cart

| Method | Path | Maqsad | Auth | Admin | Holat |
|--------|------|--------|------|-------|-------|
| `GET` | `/cart` | Foydalanuvchi cart i | Yes | No | 🟡 |
| `POST` | `/cart/items` | Cart ga mahsulot qo'shish | Yes | No | ✅ |
| `PATCH` | `/cart/items/{id}` | Quantity o'zgartirish | Yes | No | ✅ |
| `DELETE` | `/cart/items/{id}` | Cart dan o'chirish | Yes | No | ✅ |
| `DELETE` | `/cart` | Cart ni to'liq tozalash | Yes | No | ❌ |

> Cart endpoint lar `frontend/app.js:347,373,388` da chaqiriladi

- [x] Add to cart ishlaydi
- [x] Quantity o'zgartirish ishlaydi
- [x] Item o'chirish ishlaydi
- [ ] `GET /cart` — hozirgi cart holati
- [ ] `DELETE /cart` — to'liq tozalash
- [ ] Cart limit (20 ta) check
- [ ] UNIQUE(user_id, product_id) xato handling

---

## Orders

| Method | Path | Maqsad | Auth | Admin | Holat |
|--------|------|--------|------|-------|-------|
| `POST` | `/orders` | Buyurtma yaratish | Yes | No | ✅ (`main.py:267`) |
| `GET` | `/orders` | Buyurtmalar tarixi | Yes | No | ✅ |
| `GET` | `/orders/{id}` | Buyurtma detail | Yes | No | 🟡 |
| `POST` | `/orders/{id}/cancel` | Bekor qilish (faqat PENDING) | Yes | No | ❌ |
| `POST` | `/orders/{id}/reorder` | Qayta buyurtma | Yes | No | ❌ |

### `POST /orders` — ishlaydi ✅
```python
# backend/main.py:267 — mavjud
# Request body (tekshirish kerak):
{
    "user_id": 123,
    "items": [{"product_id": 1, "quantity": 2}],
    "delivery_address": "...",
    "latitude": 41.2,
    "longitude": 69.2,
    "payment_method": "CLICK"  # ❌ bu field hozir yo'q
}
# Response: { "order_id": 456, "total": 50000, "payment_url": "..." }
```

- [x] Buyurtma yaratiladi
- [x] Admin xabardor qilinadi
- [x] Payment URL qaytariladi
- [ ] `payment_method` field qabul qilinadi
- [ ] Validation schema (Pydantic)
- [ ] Minimum amount check

### `GET /orders` — ishlaydi ✅
```python
# backend/main.py — mavjud
# Yaxshilash kerak:
```

- [x] Buyurtmalar ro'yxati qaytariladi
- [ ] Pagination (page, limit parametrlari)
- [ ] Status filter
- [ ] `order_items` bilan birga (nested)

---

## Payments

| Method | Path | Maqsad | Auth | Admin | Holat |
|--------|------|--------|------|-------|-------|
| `POST` | `/payment/click/prepare` | Click prepare callback | No | No | 🟡 (`main.py:371`) |
| `POST` | `/payment/click/complete` | Click complete callback | No | No | 🟡 (`main.py:371`) |
| `POST` | `/payment/payme` | Payme JSONRPC | No | No | 🟡 (`main.py:371`) |

### `POST /payment/click/prepare` — qisman bor 🟡
```python
# backend/main.py:371 — mavjud
# Yaxshilash kerak: HMAC sign verify
# Request (Click dan keladi):
{
    "click_trans_id": "12345",
    "service_id": "678",
    "merchant_trans_id": "order_456",
    "amount": "50000",
    "action": "0",
    "sign_time": "2024-01-01 12:00:00",
    "sign_string": "md5hash..."
}
# Response:
{ "click_trans_id": "12345", "merchant_trans_id": "order_456", "error": 0 }
```

- [x] Endpoint mavjud
- [ ] HMAC sign verify
- [ ] Idempotency check
- [ ] Unit test

### `POST /payment/payme` — qisman bor 🟡
```python
# JSONRPC format:
{
    "id": 1,
    "method": "CheckPerformTransaction",
    "params": {
        "amount": 5000000,  # tiyin
        "account": { "order_id": "456" }
    }
}
```

- [x] Endpoint mavjud
- [ ] CheckPerformTransaction
- [ ] CreateTransaction
- [ ] PerformTransaction
- [ ] CancelTransaction
- [ ] Basic Auth verify

---

## Addresses

| Method | Path | Maqsad | Auth | Admin | Holat |
|--------|------|--------|------|-------|-------|
| `GET` | `/addresses` | Saqlangan manzillar | Yes | No | ❌ |
| `POST` | `/addresses` | Yangi manzil | Yes | No | ❌ |
| `PUT` | `/addresses/{id}` | Manzil tahrirlash | Yes | No | ❌ |
| `DELETE` | `/addresses/{id}` | Manzil o'chirish | Yes | No | ❌ |
| `PATCH` | `/addresses/{id}/default` | Default qilish | Yes | No | ❌ |

```python
# backend/routers/addresses.py (yaratish kerak)
@router.get("/addresses", response_model=List[AddressRead])
async def get_addresses(user_id: int, repo: AddressRepository = Depends()):
    return await repo.get_by_user(user_id)

@router.post("/addresses", response_model=AddressRead)
async def create_address(data: AddressCreate, repo: AddressRepository = Depends()):
    user_addresses = await repo.get_by_user(data.user_id)
    if len(user_addresses) >= 5:
        raise HTTPException(400, "Maksimal 5 ta manzil saqlash mumkin")
    return await repo.create(**data.dict())
```

- [ ] `addresses` router yaratilgan
- [ ] `AddressRepository` yaratilgan
- [ ] Max 5 limit
- [ ] Default manzil logikasi

---

## Promo Codes

| Method | Path | Maqsad | Auth | Admin | Holat |
|--------|------|--------|------|-------|-------|
| `POST` | `/promo/validate` | Kod tekshirish + chegirma | Yes | No | ❌ |
| `GET` | `/promo/my-usage` | Foydalanuvchi ishlatgan kodlar | Yes | No | ❌ |

```python
# backend/routers/promo.py (yaratish kerak)
@router.post("/promo/validate")
async def validate_promo(
    data: PromoValidate,  # { code, cart_amount, user_id }
    service: PromoService = Depends()
):
    try:
        result = await service.apply(data.code, data.user_id, data.cart_amount)
        return {
            "valid": True,
            "discount": result["discount"],
            "final_amount": result["final_amount"],
            "promo_type": result["type"]
        }
    except InvalidPromoCode as e:
        raise HTTPException(400, str(e))
```

- [ ] `/promo/validate` endpoint
- [ ] `PromoService` yaratilgan
- [ ] Edge case lar handle qilingan

---

## Referral

| Method | Path | Maqsad | Auth | Admin | Holat |
|--------|------|--------|------|-------|-------|
| `GET` | `/referral/info` | O'z referral kodi va statistika | Yes | No | ❌ |
| `GET` | `/referral/link` | Telegram referral link | Yes | No | ❌ |

---

## Admin — Orders

| Method | Path | Maqsad | Auth | Admin | Holat |
|--------|------|--------|------|-------|-------|
| `GET` | `/admin/orders` | Barcha buyurtmalar | Yes | Yes | ✅ (`main.py:471`) |
| `PATCH` | `/admin/orders/{id}/status` | Status o'zgartirish | Yes | Yes | ✅ (`main.py:454`) |
| `GET` | `/admin/orders/{id}` | Buyurtma detail | Yes | Yes | 🟡 |

### `GET /admin/orders` — ishlaydi ✅
```python
# backend/main.py:471 — mavjud
# Yaxshilash kerak:
```

- [x] Admin buyurtmalar ko'radi
- [ ] Status filter (pending, confirmed, ...)
- [ ] Sana filter (date_from, date_to)
- [ ] Pagination
- [ ] Admin auth check

### `PATCH /admin/orders/{id}/status` — ishlaydi ✅
```python
# backend/main.py:454 — mavjud
# Yaxshilash kerak: transition validation
```

- [x] Admin status o'zgartiradi
- [x] User xabar oladi (`main.py:454`)
- [ ] Transition validation (VALID_TRANSITIONS)
- [ ] Status history yoziladi

---

## Admin — Products & Stats

| Method | Path | Maqsad | Auth | Admin | Holat |
|--------|------|--------|------|-------|-------|
| `POST` | `/admin/products` | Mahsulot qo'shish | Yes | Yes | ❌ |
| `PATCH` | `/admin/products/{id}` | Mahsulot tahrirlash | Yes | Yes | ❌ |
| `DELETE` | `/admin/products/{id}` | Mahsulot o'chirish | Yes | Yes | ❌ |
| `POST` | `/admin/categories` | Kategoriya qo'shish | Yes | Yes | ❌ |
| `GET` | `/admin/stats` | Kunlik statistika | Yes | Yes | ❌ |

### `GET /admin/stats` — yaratish kerak ❌
```python
# Response:
{
    "today_orders": 15,
    "today_revenue": 750000,
    "pending_orders": 3,
    "total_users": 120,
    "payment_breakdown": {
        "click": 8,
        "payme": 5,
        "cash": 2
    }
}
```

- [ ] `/admin/stats` endpoint
- [ ] Bugungi tushum hisobi
- [ ] Payment usullari breakdown
- [ ] Pending orders count

---

## Yetkazildi Endpoint

| Method | Path | Maqsad | Auth | Admin | Holat |
|--------|------|--------|------|-------|-------|
| `POST` | `/orders/{id}/delivered` | Yetkazildi holati | Yes | Yes | ✅ (`main.py:454`) |

- [x] Endpoint mavjud
- [ ] Faqat admin yoki DELIVERING statusida

---

## Router Bo'lish Rejasi

```python
# backend/main.py dan alohida routerlarga bo'lish:

# backend/routers/orders.py     ← main.py:267, :371 (order endpoints)
# backend/routers/payments.py   ← main.py:335, :371 (payment endpoints)
# backend/routers/users.py      ← yangi
# backend/routers/addresses.py  ← yangi
# backend/routers/promo.py      ← yangi
# backend/routers/referral.py   ← yangi
# backend/routers/admin.py      ← main.py:454, :471 (admin endpoints)
# backend/routers/menu.py       ← yangi (alohida categories/products)

# backend/main.py da:
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(users.router)
app.include_router(addresses.router)
app.include_router(promo.router)
app.include_router(admin.router)
app.include_router(menu.router)
```

---

## API Tekshirish Checklistlari

### Hozir Ishlaydigan Endpoint lar
- [x] `POST /bootstrap` — WebApp initData + data
- [x] Cart CRUD (add, update, delete)
- [x] `POST /orders` — buyurtma yaratish
- [x] `GET /orders` — tarixi
- [x] Payment redirect URL lar
- [x] `GET /admin/orders` — admin ro'yxat
- [x] `PATCH /admin/orders/{id}/status` — status o'zgartirish
- [x] Frontend fayllar serve (`/`, `/app.js`, `/styles.css`)

### Sprint 2 da Qo'shiladi
- [ ] Click signature verify
- [ ] Payme JSONRPC to'liq
- [ ] Status transition validation
- [ ] Cash payment endpoint

### Sprint 3 da Qo'shiladi
- [ ] `/addresses` CRUD
- [ ] `/promo/validate`
- [ ] `/referral/info`
- [ ] `/orders/{id}/reorder`
- [ ] `/admin/stats`

---

[← Database](./06_database_roadmap.md) | [Keyingi: Deployment →](./08_deployment_security.md)

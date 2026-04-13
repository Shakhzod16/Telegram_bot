# API Hujjatlari

Base URL: `http://localhost:8000/api/v1`

Barcha himoyalangan endpointlar uchun header:
```
Authorization: Bearer {jwt_token}
```

---

## Auth

### POST /auth/telegram/init
Telegram initData bilan tizimga kirish.

**Request:**
```json
{
  "init_data": "user=%7B%22id%22%3A123...&hash=abc123"
}
```

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "telegram_id": 123456789,
    "first_name": "Ali",
    "language": "uz"
  }
}
```

**Errors:** 401 (invalid initData), 429 (rate limit)

---

## Catalog

### GET /categories
**Response 200:**
```json
[
  {
    "id": 1,
    "name_uz": "Burgerlar",
    "name_ru": "Бургеры",
    "image_url": "/static/images/burgers.jpg",
    "sort_order": 1
  }
]
```

### GET /products
**Query params:** `category_id`, `search`, `page` (default: 1), `size` (default: 20)

**Response 200:**
```json
{
  "items": [
    {
      "id": 1,
      "name_uz": "Classic Burger",
      "base_price": "35000.00",
      "weight_grams": 300,
      "image_url": "/static/images/classic.jpg",
      "category_id": 1
    }
  ],
  "total": 20,
  "page": 1,
  "size": 20
}
```

### GET /products/{id}
**Response 200:**
```json
{
  "id": 1,
  "name_uz": "Classic Burger",
  "description_uz": "Mazali burger...",
  "base_price": "35000.00",
  "weight_grams": 300,
  "variants": [
    {"id": 1, "name_uz": "Kichik", "price": "30000.00", "is_default": false},
    {"id": 2, "name_uz": "O'rta", "price": "35000.00", "is_default": true},
    {"id": 3, "name_uz": "Katta", "price": "45000.00", "is_default": false}
  ],
  "modifiers": [
    {"id": 1, "name_uz": "Qo'shimcha pishloq", "price_delta": "3000.00"}
  ]
}
```

---

## Cart

### GET /cart
**Response 200:**
```json
{
  "items": [
    {
      "id": "1:2",
      "product_id": 1,
      "product_name": "Classic Burger",
      "variant_id": 2,
      "variant_name": "O'rta",
      "quantity": 2,
      "unit_price": "35000.00",
      "total_price": "70000.00"
    }
  ],
  "subtotal": "70000.00",
  "item_count": 2
}
```

### POST /cart/items
**Request:**
```json
{
  "product_id": 1,
  "variant_id": 2,
  "quantity": 1,
  "modifier_ids": [1]
}
```
**Response 200:** yangilangan cart

### PATCH /cart/items/{id}
**Request:** `{"quantity": 3}`

### DELETE /cart/items/{id}
**Response 200:** yangilangan cart

---

## Addresses

### POST /addresses
**Request:**
```json
{
  "title": "Uy",
  "address_line": "Yunusobod, 19-kvartal, 5-uy",
  "lat": 41.3111,
  "lng": 69.2797,
  "apartment": "42",
  "floor": "4",
  "entrance": "2",
  "door_code": "1234",
  "landmark": "Dorixona yonida",
  "comment": "Qo'ng'iroq qilmang",
  "is_default": true
}
```

---

## Checkout

### POST /checkout/preview
**Request:**
```json
{
  "address_id": 1,
  "promo_code": "FIRST10"
}
```

**Response 200:**
```json
{
  "items": [...],
  "subtotal": "85000.00",
  "delivery_fee": "5000.00",
  "discount": "8500.00",
  "total": "81500.00",
  "promo_applied": true
}
```

### POST /orders
**Request:**
```json
{
  "address_id": 1,
  "promo_code": "FIRST10",
  "comment": "Tez yetkazing",
  "payment_method": "cash",
  "idempotency_key": "uuid-v4-here"
}
```

**Response 201:** yaratilgan order

**Errors:**
- 400: bo'sh savat
- 400: min order amount
- 400: branch yopiq
- 409: duplicate (idempotency)
- 422: delivery zone tashqarida

---

## Orders

### GET /orders
**Query:** `page`, `size`, `status`

### POST /orders/{id}/cancel
Faqat `status=pending` bo'lganda ishlaydi.
**Error 400:** boshqa statusda bekor qilib bo'lmaydi

### POST /orders/{id}/repeat
Avvalgi order itemlarini yangi savatga qo'shadi.

---

## Admin

Barcha admin endpointlar uchun `is_admin=True` kerak.

### PATCH /admin/orders/{id}/status
```json
{"status": "confirmed"}
```
Valid o'tishlar:
- pending → confirmed
- confirmed → preparing
- preparing → ready
- ready → on_the_way
- on_the_way → delivered
- pending → cancelled

---

## Xato formatlari

```json
{
  "detail": "Xato xabari",
  "code": "ERROR_CODE",
  "field": "field_name"
}
```

| HTTP kodi | Ma'no |
|-----------|-------|
| 400 | Noto'g'ri so'rov |
| 401 | Autentifikatsiya xatosi |
| 403 | Ruxsat yo'q |
| 404 | Topilmadi |
| 409 | Conflict (duplicate) |
| 422 | Validatsiya xatosi |
| 429 | Rate limit |
| 500 | Server xatosi |

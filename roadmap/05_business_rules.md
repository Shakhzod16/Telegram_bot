# 05 — Business / Technical / Security Rules

> Har rule: nima, nima uchun, qayerda, edge case, implementation eslatma.

---

## Business Rules

### RULE-B1: Minimum Buyurtma Summasi
| Maydon | Qiymat |
|--------|--------|
| **Tavsif** | Minimum buyurtma summa = 10 000 so'm |
| **Nima uchun** | Yetkazib berish xarajatini qoplash |
| **Qayerda** | `backend/services/cart_service.py`, `frontend/app.js` |
| **Edge case** | Promo chegirmadan keyin sum kamaysa ham check qilish kerak |
| **Implementation** | `CartService.validate_minimum()` → checkout oldidan |

- [ ] Backend da minimum check qo'shilgan
- [ ] Frontend da checkout tugma minimum bo'lmasa disabled
- [ ] Xato xabari 3 tilda: "Minimum buyurtma 10 000 so'm"

---

### RULE-B2: Mahsulot Mavjudligi
| Maydon | Qiymat |
|--------|--------|
| **Tavsif** | Mavjud bo'lmagan mahsulot cartga qo'shilmaydi |
| **Nima uchun** | Noto'g'ri buyurtma oldini olish |
| **Qayerda** | `backend/services/cart_service.py` |
| **Edge case** | Cart da turgan mahsulot checkout da o'chirilgan bo'lsa — xabar bilan skip |
| **Implementation** | Checkout da barcha cart items ni re-validate qilish |

- [ ] `is_available` field tekshiriladi cartga qo'shishda
- [ ] Checkout da re-validate
- [ ] Mavjud bo'lmasa user ga xabar + cart dan o'chirish

---

### RULE-B3: Bitta Aktiv Buyurtma
| Maydon | Qiymat |
|--------|--------|
| **Tavsif** | Foydalanuvchida bir vaqtda faqat 1 ta PENDING buyurtma |
| **Nima uchun** | Chalkashlikni oldini olish |
| **Qayerda** | `backend/services/order_service.py` |
| **Edge case** | Cancelled order yangi buyurtmaga to'sqinlik qilmaydi |
| **Implementation** | `create_order()` da check: `user da PENDING order bormi?` |

- [ ] Order yaratishda PENDING check
- [ ] PENDING bor bo'lsa → 400 + "Sizda faol buyurtma bor"
- [ ] CANCELLED bo'lsa yangi buyurtmaga ruxsat

---

### RULE-B4: Yetkazib Berish Vaqti Ko'rsatish
| Maydon | Qiymat |
|--------|--------|
| **Tavsif** | "30-45 daqiqa" ko'rsatish user ga |
| **Nima uchun** | User kutish boshqaruvi — UZ bozorida muhim |
| **Qayerda** | `backend/services/order_service.py`, bot handler |
| **Edge case** | Kech bo'lsa — user ga "Kechikish bor" xabari |
| **Implementation** | `estimated_delivery_at` field + xabarda ko'rsatish |

- [ ] Order yaratilganda `estimated_delivery_at` hisoblanadi
- [ ] User ga xabarda vaqt ko'rsatiladi
- [ ] Admin kechiktirsa — user ga yangi ETA

---

## Order Status Transition Rules

### RULE-O1: Status Davri
```
PENDING → CONFIRMED → PREPARING → DELIVERING → DELIVERED
  ↓           ↓
CANCELLED  CANCELLED
```

| Maydon | Qiymat |
|--------|--------|
| **Tavsif** | Status faqat belgilangan yo'l bo'yicha o'tadi |
| **Nima uchun** | Chalkash status oldini olish |
| **Qayerda** | `backend/services/order_service.py` |
| **Edge case** | DELIVERED dan orqaga yo'q |
| **Implementation** | `VALID_TRANSITIONS` dict + `validate_transition()` |

- [ ] `VALID_TRANSITIONS` dict mavjud
- [ ] `validate_transition()` funksiyasi
- [ ] Noto'g'ri transition → 400 + xato xabari

---

### RULE-O2: Status O'zgartirishga Ruxsat
| Maydon | Qiymat |
|--------|--------|
| **Tavsif** | Faqat admin status o'zgartiradi. Foydalanuvchi faqat PENDING ni CANCEL qila oladi |
| **Qayerda** | `bot/middlewares/admin_check.py`, `order_service.py` |
| **Edge case** | Foydalanuvchi CONFIRMED dan cancel qilolmaydi |
| **Implementation** | `is_admin check` + `user_can_cancel()` |

- [ ] Admin middleware bor
- [ ] `user_can_cancel(order_id, user_id)` logika
- [ ] Non-admin CONFIRMED → CANCELLED → 403

---

## Payment Rules

### RULE-P1: Payment Idempotency
| Maydon | Qiymat |
|--------|--------|
| **Tavsif** | Bir buyurtmaga bir to'lov. Ikkinchi urinish 200 (idempotent) |
| **Nima uchun** | Ikki marta to'lov yechilmasin |
| **Qayerda** | `backend/services/payment_service.py` |
| **Edge case** | Click/Payme callback ni ikki marta yuborishi mumkin |
| **Implementation** | `payments.order_id UNIQUE` + `idempotency_key` check |

- [ ] `payments` jadvalda `order_id UNIQUE`
- [ ] Takroriy callback → 200 (xato emas)
- [ ] DB constraint mavjud

---

### RULE-P2: Signature Verify
| Maydon | Qiymat |
|--------|--------|
| **Tavsif** | Click va Payme callback larda hash tekshiriladi |
| **Nima uchun** | Soxta to'lov oldini olish |
| **Qayerda** | `backend/services/payment_service.py` |
| **Edge case** | Hash xato bo'lsa order CONFIRM bo'lmaydi |
| **Implementation** | `hashlib.md5` / `sha1` sign verify |

- [ ] Click callback sign tekshiriladi
- [ ] Payme Basic Auth tekshiriladi
- [ ] Noto'g'ri sign → 400 (order o'zgarmaydi)

---

### RULE-P3: Cash Order Flow
| Maydon | Qiymat |
|--------|--------|
| **Tavsif** | Cash order da `payment_status = AWAITING_CASH`, redirect yo'q |
| **Nima uchun** | Cash boshqacha flow |
| **Qayerda** | `backend/services/order_service.py` |
| **Edge case** | Kurier qabul qilganda admin `CASH_RECEIVED` beradi |
| **Implementation** | `payment_method == CASH`: skip gateway |

- [ ] Cash order to'lov redirectsiz yaratiladi
- [ ] Admin da "💵 Naqd" badge ko'rinadi
- [ ] Admin "Naqd qabul qilindi" tugmasi

---

## Cart Rules

### RULE-C1: Cart DB da Saqlanadi
| Maydon | Qiymat |
|--------|--------|
| **Tavsif** | Cart WebApp session emas, DB da saqlanadi |
| **Nima uchun** | WebApp yopilsa cart yo'qolmasin |
| **Qayerda** | `backend/repositories/cart_repo.py` |
| **Edge case** | Session expire — cart DB da qoladi |
| **Implementation** | `cart_items` jadval `user_id` bilan bog'liq |

- [ ] Cart `cart_items` jadvalda
- [ ] WebApp ochilganda DB dan fetch qilinadi
- [ ] WebApp yopilsa cart saqlanadi

---

### RULE-C2: Cart Limit
| Maydon | Qiymat |
|--------|--------|
| **Tavsif** | Cartda max 20 ta mahsulot turi |
| **Nima uchun** | Cheksiz cart muammosi |
| **Qayerda** | `backend/services/cart_service.py` |
| **Edge case** | Bir xil mahsulot quantity oshirsa — count emas |
| **Implementation** | `len(cart_items) >= 20: raise CartLimitError` |

- [ ] 21-chi mahsulot → xato
- [ ] Quantity oshirish limit emas
- [ ] User ga xabar

---

### RULE-C3: Price Lock (Hozirgi Narx)
| Maydon | Qiymat |
|--------|--------|
| **Tavsif** | Checkout da hozirgi narx ishlatiladi (cartga qo'shilgandagi emas) |
| **Nima uchun** | Admin narx o'zgartirsa to'g'ri summa |
| **Qayerda** | `backend/services/cart_service.py` checkout |
| **Edge case** | Narx oshgan bo'lsa user ga ogohlantirish |
| **Implementation** | Checkout da `product.price` re-fetch |

- [ ] Checkout da narx DB dan qayta o'qiladi
- [ ] Narx farq bo'lsa user ga "Narx o'zgardi: ..." xabar
- [ ] `order_items.price_at_order` saqlanadi

---

## Security Rules

### RULE-S1: Admin Auth
| Maydon | Qiymat |
|--------|--------|
| **Tavsif** | Admin panel faqat `ADMIN_IDS` ro'yxatidagi Telegram ID lar |
| **Nima uchun** | Unauthorized access |
| **Qayerda** | `bot/middlewares/admin_check.py` |
| **Edge case** | ADMIN_IDS `.env` da, DB da emas |
| **Implementation** | `message.from_user.id in settings.ADMIN_IDS` |

- [ ] `admin_check.py` middleware mavjud
- [ ] Admin bo'lmagan user admin command → "ruxsat yo'q"
- [ ] ADMIN_IDS `.env` da

---

### RULE-S2: WebApp initData Verify
| Maydon | Qiymat |
|--------|--------|
| **Tavsif** | WebApp dan kelgan har so'rov Telegram initData bilan validate |
| **Nima uchun** | Soxta WebApp so'rov oldini olish |
| **Qayerda** | `backend/main.py:247` (hozir bootstrap da bor) |
| **Edge case** | initData 1 soatda expire — refresh kerak |
| **Implementation** | HMAC-SHA256 verify: `initData.hash` |

```python
import hmac, hashlib, json
from urllib.parse import parse_qsl

def verify_webapp_data(init_data: str, bot_token: str) -> bool:
    parsed = dict(parse_qsl(init_data, strict_parsing=True))
    hash_ = parsed.pop("hash", "")
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, data_check_string.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, hash_)
```

- [ ] `verify_webapp_data()` funksiyasi mavjud
- [ ] Bootstrap endpoint da verify qilinadi
- [ ] Noto'g'ri initData → 401

---

### RULE-S3: Rate Limiting
| Maydon | Qiymat |
|--------|--------|
| **Tavsif** | Har user 60 so'rov/daqiqa limit |
| **Nima uchun** | Spam va attack |
| **Qayerda** | `backend/main.py` yoki nginx |
| **Implementation** | `slowapi` yoki nginx `limit_req_zone` |

```python
# pip install slowapi
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/orders")
@limiter.limit("60/minute")
async def get_orders(request: Request):
    ...
```

- [ ] Rate limiting sozlangan
- [ ] Limitdan oshsa → 429 + "Iltimos sekinroq"
- [ ] Admin uchun limit yuqoriroq

---

### RULE-S4: SQL Injection Himoyasi
| Maydon | Qiymat |
|--------|--------|
| **Tavsif** | Barcha DB query lar ORM (SQLAlchemy) orqali |
| **Nima uchun** | SQL injection |
| **Qayerda** | Barcha repository fayllar |
| **Edge case** | Raw query kerak bo'lsa — parameterized |
| **Implementation** | `text()` bilan parameterized, hech qachon f-string SQL |

```python
# ❌ YOMON
await session.execute(f"SELECT * FROM users WHERE id = {user_id}")

# ✅ YAXSHI
await session.execute(select(User).where(User.id == user_id))

# ✅ Raw query kerak bo'lsa
from sqlalchemy import text
await session.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id})
```

- [ ] Hech qanday f-string SQL yo'q
- [ ] Barcha query ORM yoki parameterized
- [ ] `grep -r "f\"SELECT\|f'SELECT"` — natija bo'sh

---

## Code Architecture Rules

### RULE-A1: Layered Architecture
```
Router → Service → Repository → Model

Router:     Faqat HTTP: request parse, response format
Service:    Faqat business logic: validate, calculate, orchestrate
Repository: Faqat DB: CRUD operatsiyalar
Model:      Faqat data structure
```

- [ ] Router da `session.query` yo'q
- [ ] Service da HTTP import yo'q
- [ ] Repository da business logic yo'q

---

### RULE-A2: Bot Handler da Logika Yo'q
| Maydon | Qiymat |
|--------|--------|
| **Tavsif** | Bot handler faqat API chaqiradi, business logic emas |
| **Nima uchun** | DRY — bir logika bir joyda |
| **Qayerda** | `bot/handlers/*.py` |
| **Implementation** | Handler da faqat: fetch data, show keyboard, send message |

```python
# ❌ YOMON — business logic handler da
@dp.message_handler(text="📦 Buyurtmalar")
async def orders(message: types.Message):
    conn = get_db()
    orders = conn.execute("SELECT * FROM orders WHERE user_id = ?", (user_id,)).fetchall()
    # ... ko'p logika

# ✅ YAXSHI — handler faqat API chaqiradi
@dp.message_handler(text="📦 Buyurtmalar")
async def orders(message: types.Message):
    orders = await api_client.get_orders(user_id=message.from_user.id)
    await message.answer(format_orders(orders), reply_markup=orders_keyboard())
```

- [ ] Bot handler da DB query yo'q
- [ ] Handler da to'g'ridan-to'g'ri business logic yo'q
- [ ] Handler API service ni chaqiradi

---

### RULE-A3: Async All the Way
| Maydon | Qiymat |
|--------|--------|
| **Tavsif** | Barcha funksiyalar `async def` |
| **Nima uchun** | Blocking call = performance muammosi |
| **Implementation** | `asyncio` + `httpx` (requests emas), `aiosqlite` |

- [ ] Hech qanday `time.sleep()` yo'q → `asyncio.sleep()`
- [ ] `requests` library yo'q → `httpx.AsyncClient`
- [ ] Sync DB call yo'q → `async with AsyncSession()`

---

## Uzbekistan Market Specific Rules

### RULE-UZ1: Default Til
| Maydon | Qiymat |
|--------|--------|
| **Tavsif** | Default til = O'zbek. Foydalanuvchi o'zgartirsa DB da saqlanadi |
| **Qayerda** | `bot/handlers/onboarding.py` |
| **Implementation** | `user.language = language or "uz"` |

- [ ] Onboarding til tanlash birinchi qadam
- [ ] Tanlangan til DB da saqlanadi
- [ ] Har handler da `user.language` o'qiladi

---

### RULE-UZ2: Telefon Raqam Formati
| Maydon | Qiymat |
|--------|--------|
| **Tavsif** | Telefon raqam `+998XXXXXXXXX` formatda saqlanadi |
| **Qayerda** | `utils/validators.py` |
| **Implementation** | `normalize_phone_uz()` util |

```python
# utils/validators.py
def normalize_phone_uz(phone: str) -> str:
    phone = "".join(c for c in phone if c.isdigit() or c == "+")
    if phone.startswith("998") and len(phone) == 12:
        phone = "+" + phone
    elif phone.startswith("8") and len(phone) == 11:
        phone = "+998" + phone[1:]
    elif len(phone) == 9:
        phone = "+998" + phone
    return phone
```

- [ ] Onboarding da normalize qilinadi
- [ ] DB da `+998XXXXXXXXX` formatda
- [ ] `8` bilan boshlanganlar ham qabul qilinadi

---

### RULE-UZ3: Narx Ko'rsatish Formati
| Maydon | Qiymat |
|--------|--------|
| **Tavsif** | Narxlar so'm da ko'rsatiladi. Payme uchun tiyin ga konversiya ichki |
| **Qayerda** | `utils/formatters.py` |
| **Implementation** | `format_price(50000)` → `"50 000 so'm"` |

```python
# utils/formatters.py
def format_price(amount: int) -> str:
    return f"{amount:,} so'm".replace(",", " ")

def to_tiyins(som: int) -> int:
    """Payme uchun: so'm → tiyin"""
    return som * 100

def from_tiyins(tiyins: int) -> int:
    """Payme dan: tiyin → so'm"""
    return tiyins // 100
```

- [ ] `format_price()` barcha joy da ishlatiladi
- [ ] Payme amount tiyin da jo'natiladi
- [ ] Display da so'm da ko'rsatiladi

---

## Testing Rules

### RULE-T1: Test Pyramid
```
E2E tests      ← 10% (sekin, qimmat)
Integration    ← 20% (o'rta)
Unit tests     ← 70% (tez, arzon)
```

- [ ] Eng ko'p: unit test (service lar)
- [ ] O'rta: API test (endpoint lar)
- [ ] Kam: E2E (to'liq flow)

---

### RULE-T2: Real Payment Tests Yo'q
| Maydon | Qiymat |
|--------|--------|
| **Tavsif** | Payment testlarda faqat mock yoki sandbox |
| **Nima uchun** | Real pul yechilmasin |
| **Implementation** | `monkeypatch.setattr()` yoki `responses` library |

```python
# tests/unit/test_payment_service.py
def test_verify_click_sign_valid(monkeypatch):
    service = PaymentService()
    params = {
        "click_trans_id": "123",
        "service_id": "456",
        "merchant_trans_id": "789",
        "amount": "10000",
        "action": "1",
        "sign_time": "2024-01-01 12:00:00",
        "sign_string": "expected_hash_here"
    }
    assert service.verify_click_sign(params) == True
```

- [ ] Testlarda real to'lov API chaqirilmaydi
- [ ] Mock/fixture ishlatiladi
- [ ] Sandbox alohida test environment

---

### RULE-T3: Test Database
| Maydon | Qiymat |
|--------|--------|
| **Tavsif** | Testlar uchun alohida DB (SQLite in-memory) |
| **Nima uchun** | Production DB buzilmasin |
| **Implementation** | `pytest fixture: test_db = SQLite:///:memory:` |

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from database.models import Base

@pytest.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine) as session:
        yield session
    await engine.dispose()
```

- [ ] `conftest.py` da test DB fixture
- [ ] Testlar production DB ga tegmaydi
- [ ] Har test alohida clean state

---

[← Implementation Order](./04_implementation_order.md) | [Keyingi: Database →](./06_database_roadmap.md)

# 02 — Developer Execution Board

> **Foydalanish:** `- [ ]` ni `- [x]` ga o'zgartiring yoki VS Code da checkbox ni bosing.
> **🟢** = Hozir loyihada ishlaydi | **🔴** = Hali yo'q | **🟡** = Qisman bor

---

## PHASE 0 — Foundation & Code Quality
> **Maqsad:** Loyihani mustahkam poydevorga qo'yish — xato bo'lmaydi, config tartibli, log yoziladi
> **Taxminiy vaqt:** 3–5 kun | **Priority:** MUST-HAVE

---

### P0-T1 — Loyiha strukturasini qayta tartiblashtirish 🔴
> **Murakkablik:** Medium | **Dependency:** Yo'q
> **Branch:** `refactor/project-structure`
> **Commit:** `refactor: reorganize project into layered architecture`

#### Subtasklar
- [ ] `backend/routers/` papka yaratish → `backend/routers/__init__.py`
- [ ] `backend/services/` papka yaratish → `backend/services/__init__.py`
- [ ] `backend/repositories/` papka yaratish → `backend/repositories/__init__.py`
- [ ] `backend/schemas/` papka yaratish → `backend/schemas/__init__.py`
- [ ] `bot/middlewares/` papka yaratish → `bot/middlewares/__init__.py`
- [ ] `bot/keyboards/` papka yaratish → `bot/keyboards/__init__.py`
- [ ] `bot/states/` papka yaratish → `bot/states/__init__.py`
- [ ] `config/` papka + `config/settings.py` yaratish
- [ ] `tests/` papka + `tests/__init__.py` + `pytest.ini` yaratish
- [ ] Mavjud import larni yangi strukturaga moslashtirish

#### VS Code Bajarish Tartibi
1. Explorer da papkalar yarating (right-click → New Folder)
2. Har papkaga `__init__.py` qo'shing
3. `python -m bot.main` — ishlaydimi tekshirish
4. `curl http://localhost:8000/docs` — API ishlayaptimy

#### Acceptance Criteria
- [ ] Bot `/start` ga javob beradi
- [ ] FastAPI `/docs` ochiladi
- [ ] Hech qanday `ImportError` yo'q
- [ ] `pytest` xatosiz ishga tushadi (0 test bo'lsa ham)

#### Manual Testing
- [ ] Bot `/start` bosilganda menyu ko'rinadi
- [ ] `/docs` da endpoint lar ko'rinadi
- [ ] Terminal da `ImportError` yo'q

---

### P0-T2 — Settings va .env management 🔴
> **Murakkablik:** Easy | **Dependency:** P0-T1
> **Branch:** `feat/config-env`
> **Commit:** `feat: add pydantic settings and .env structure`

#### Subtasklar
- [ ] `pip install pydantic-settings` → `requirements.txt` ga qo'shish
- [ ] `config/settings.py` — `Settings(BaseSettings)` class yaratish
- [ ] `.env.example` — barcha o'zgaruvchilar (sharh bilan)
- [ ] `.env.development` va `.env.production` ajratish
- [ ] `BOT_TOKEN` ni `.env` dan o'qish (`bot/main.py`)
- [ ] `DATABASE_URL` ni `.env` dan o'qish (`backend/main.py`)
- [ ] `CLICK_*` kalitlarni `.env` ga ko'chirish
- [ ] `PAYME_*` kalitlarni `.env` ga ko'chirish
- [ ] `WEB_APP_URL` ni `.env` dan o'qish (hozir `.env:2` da bor — yangi settings orqali)
- [ ] `API_BASE_URL` ni `.env` ga ko'chirish (hozir `frontend/index.html:14-15` da hardcoded)
- [ ] `.env` ni `.gitignore` ga qo'shish (agar yo'q bo'lsa)

#### .env Namuna Tuzilmasi
```env
# Bot
BOT_TOKEN=your_bot_token_here
WEB_APP_URL=https://telegram-bot-1-8a3a.onrender.com
ADMIN_IDS=123456789,987654321

# Backend
DATABASE_URL=sqlite:///./food_delivery.db
SECRET_KEY=your_secret_key_here
ALLOWED_ORIGINS=https://telegram-bot-1-8a3a.onrender.com

# Click
CLICK_MERCHANT_ID=
CLICK_SERVICE_ID=
CLICK_SECRET_KEY=

# Payme
PAYME_MERCHANT_ID=
PAYME_SECRET_KEY=

# App
ENVIRONMENT=development
SENTRY_DSN=
```

#### VS Code Bajarish Tartibi
1. `config/settings.py` oching, `BaseSettings` class yozing
2. `Ctrl+Shift+F` → hardcoded token/key larni qidiring
3. Topilganlarni `settings.VARIABLE_NAME` bilan almashtiring
4. `python -c "from config.settings import settings; print(settings.BOT_TOKEN)"` test

#### Acceptance Criteria
- [ ] `from config.settings import settings` ishlaydi
- [ ] Hech qanday hardcoded token/secret kod ichida yo'q
- [ ] `.env.example` to'liq va sharhlangan
- [ ] `.env` git da ko'rinmaydi

#### Manual Testing
- [ ] `.env` faylini o'chirish → `ValidationError` chiqadi
- [ ] `.env` qaytarish → bot ishlaydi
- [ ] `git status` da `.env` ko'rinmaydi

---

### P0-T3 — Logging sozlash 🔴
> **Murakkablik:** Easy | **Dependency:** P0-T2
> **Branch:** `feat/logging`
> **Commit:** `feat: add structured logging with file rotation`

#### Subtasklar
- [ ] `utils/logger.py` yaratish
- [ ] `RotatingFileHandler` — `logs/app.log`, max 10MB, 5 backup
- [ ] Log levels: `DEBUG` dev da, `INFO` prod da
- [ ] FastAPI middleware — har request log (method, path, status, ms)
- [ ] Bot da `logger.info` — `/start`, buyurtma, to'lov
- [ ] Bot da `logger.error` — exception bilan birga

```python
# utils/logger.py namunasi
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # File handler
    fh = RotatingFileHandler("logs/app.log", maxBytes=10_000_000, backupCount=5)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    ))
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(levelname)s | %(message)s"))
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger
```

#### VS Code Bajarish Tartibi
1. `utils/logger.py` yarating
2. `backend/main.py` da `@app.middleware("http")` qo'shing
3. `bot/main.py` da `logger = setup_logger("bot")` qo'shing
4. Bot start qiling → `logs/app.log` fayl paydo bo'ladimi?

#### Acceptance Criteria
- [ ] `logs/app.log` avtomatik yaratiladi
- [ ] Har API request loglangan (GET /path → 200 → 45ms)
- [ ] Bot xatolari stacktrace bilan loglangan
- [ ] Log fayl 10MB dan oshsa rotate bo'ladi

#### Manual Testing
- [ ] `/start` bosing → log da ko'rinadi
- [ ] Noto'g'ri endpoint → log da 404 ko'rinadi
- [ ] `cat logs/app.log | grep ERROR` — bo'sh bo'lishi kerak

---

### P0-T4 — Global error handling 🔴
> **Murakkablik:** Medium | **Dependency:** P0-T3
> **Branch:** `feat/error-handling`
> **Commit:** `feat: add global error handlers for bot and api`

#### Subtasklar
- [ ] `backend/exceptions.py` — custom exception classlar
- [ ] FastAPI `@app.exception_handler(Exception)` — structured JSON error
- [ ] FastAPI `@app.exception_handler(HTTPException)` — standart error
- [ ] `bot/middlewares/error_middleware.py` — global bot exception handler
- [ ] Foydalanuvchiga xato xabari (3 tilda) — "Xatolik yuz berdi, qayta urining"
- [ ] Exception larda `logger.error(exc_info=True)` chaqirish

```python
# backend/exceptions.py
class OrderNotFound(Exception): pass
class PaymentFailed(Exception): pass
class CartEmpty(Exception): pass
class ProductUnavailable(Exception): pass
class InvalidPromoCode(Exception): pass

# bot/middlewares/error_middleware.py
@dp.errors.register()
async def handle_error(update: types.Update, exception: Exception):
    logger.error(f"Exception: {exception}", exc_info=True)
    if update.message:
        lang = await get_user_lang(update.message.from_user.id)
        await update.message.answer(texts.get("error_occurred", lang))
    return True  # error handled
```

#### VS Code Bajarish Tartibi
1. `backend/exceptions.py` yarating
2. `backend/main.py` da exception handler lar qo'shing
3. `bot/middlewares/error_middleware.py` yarating
4. Test: handler da `raise Exception("test")` qo'shing → bot crash bo'lmasligini tekshiring

#### Acceptance Criteria
- [ ] Bot istalgan xatoda crash bo'lmaydi
- [ ] User xato xabarini oladi (o'z tilida)
- [ ] API 500 da `{"error": "...", "code": 500}` qaytaradi
- [ ] Xato log ga tushadi

#### Manual Testing
- [ ] Noto'g'ri buyurtma jo'nating → bot ishlashda davom etadi
- [ ] `GET /nonexistent` → `{"error": "Not found", "code": 404}` qaytaradi
- [ ] Log da xato ko'rinadi

---

### P0-T5 — Database migration (Alembic) 🔴
> **Murakkablik:** Medium | **Dependency:** P0-T1
> **Branch:** `feat/alembic-migrations`
> **Commit:** `feat: add alembic for database versioning`

#### Subtasklar
- [ ] `pip install alembic` → `requirements.txt`
- [ ] `alembic init migrations` — papka yaratish
- [ ] `alembic.ini` da `DATABASE_URL` ni settings dan o'qish
- [ ] `migrations/env.py` da `target_metadata = Base.metadata` qo'yish
- [ ] Birinchi migration: `alembic revision --autogenerate -m "initial_tables"`
- [ ] `alembic upgrade head` ishlatib tekshirish
- [ ] `Makefile` yoki `scripts/migrate.sh` yaratish

```python
# migrations/env.py
from config.settings import settings
from database.models import Base

config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
target_metadata = Base.metadata
```

#### VS Code Bajarish Tartibi
1. Terminal: `pip install alembic && alembic init migrations`
2. `alembic.ini` va `migrations/env.py` ni edit qiling
3. `alembic revision --autogenerate -m "initial_tables"`
4. `migrations/versions/` da fayl paydo bo'ldi? → `alembic upgrade head`
5. DB da jadvallarni tekshiring (DBeaver yoki `sqlite3` CLI)

#### Acceptance Criteria
- [ ] `alembic upgrade head` xatosiz ishlaydi
- [ ] `alembic history` bo'sh emas
- [ ] Jadvallar DB da ko'rinadi
- [ ] `alembic downgrade -1` va `upgrade head` ishlaydi

#### Manual Testing
- [ ] `alembic current` — versiya ko'rsatadi
- [ ] `alembic show head` — migration tafsiloti
- [ ] DB da `alembic_version` jadval bor

---

## PHASE 1 — Core Backend Layering
> **Maqsad:** Kod arxitekturasini layerlarga bo'lish — router, service, repository
> **Taxminiy vaqt:** 5–7 kun | **Priority:** MUST-HAVE

---

### P1-T1 — Repository pattern 🔴
> **Murakkablik:** Hard | **Dependency:** P0-T5
> **Branch:** `refactor/repository-pattern`
> **Commit:** `refactor: extract db queries into repository classes`

#### Subtasklar
- [ ] `backend/repositories/base.py` — `BaseRepository[T]` generic class
- [ ] `backend/repositories/user_repo.py` — `UserRepository`
  - [ ] `get(user_id)`, `get_by_telegram_id(tg_id)`, `create(data)`, `update(user_id, data)`
- [ ] `backend/repositories/order_repo.py` — `OrderRepository`
  - [ ] `get(order_id)`, `get_by_user(user_id)`, `create(data)`, `update_status(order_id, status)`
- [ ] `backend/repositories/product_repo.py` — `ProductRepository`
  - [ ] `get_all()`, `get_by_category(cat_id)`, `get(product_id)`
- [ ] `backend/repositories/cart_repo.py` — `CartRepository`
  - [ ] `get_by_user(user_id)`, `add_item(user_id, product_id, qty)`, `remove_item(item_id)`, `clear(user_id)`
- [ ] `backend/database.py` — async session dependency

```python
# backend/repositories/base.py
from sqlalchemy.ext.asyncio import AsyncSession
from typing import TypeVar, Generic, Optional, List

ModelType = TypeVar("ModelType")

class BaseRepository(Generic[ModelType]):
    def __init__(self, session: AsyncSession, model):
        self.session = session
        self.model = model
    
    async def get(self, id: int) -> Optional[ModelType]:
        return await self.session.get(self.model, id)
    
    async def create(self, **kwargs) -> ModelType:
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
```

#### VS Code Bajarish Tartibi
1. `backend/repositories/base.py` yarating
2. `backend/repositories/user_repo.py` yarating
3. `backend/main.py` da bitta endpoint ni repo ishlatadigan qiling
4. Test: ishlaydimi?
5. Qolgan repo larni yarating

#### Acceptance Criteria
- [ ] Barcha DB query lar repository orqali ketadi
- [ ] Handler da to'g'ridan-to'g'ri `session.query` yo'q
- [ ] Async CRUD: `get`, `create`, `update`, `delete`

#### Manual Testing
- [ ] `GET /orders` ishlaydi (repo orqali)
- [ ] Yangi user yaratiladi (repo orqali)
- [ ] Mavjud endpoint lar buzilmagan

---

### P1-T2 — Service layer 🔴
> **Murakkablik:** Hard | **Dependency:** P1-T1
> **Branch:** `refactor/service-layer`
> **Commit:** `refactor: add service layer for business logic`

#### Subtasklar
- [ ] `backend/services/order_service.py` — `OrderService`
  - [ ] `create_order(user_id, items, address, payment_method)`
  - [ ] `update_status(order_id, new_status, changed_by)`
  - [ ] `cancel_order(order_id, user_id)`
  - [ ] `get_user_orders(user_id, page, limit)`
- [ ] `backend/services/cart_service.py` — `CartService`
  - [ ] `add_item(user_id, product_id, qty)`
  - [ ] `remove_item(user_id, item_id)`
  - [ ] `calculate_total(user_id)`
  - [ ] `clear(user_id)`
- [ ] `backend/services/payment_service.py` — `PaymentService`
  - [ ] `generate_click_url(order_id, amount)`
  - [ ] `verify_click_hash(params)` — HMAC verify
  - [ ] `generate_payme_url(order_id, amount)`
  - [ ] `process_payme_rpc(method, params)` — JSONRPC
- [ ] `backend/services/notification_service.py` — `NotificationService`
  - [ ] `notify_user(user_id, message)` — Telegram xabar
  - [ ] `notify_admin(order_id)` — admin ga yangi buyurtma
  - [ ] `notify_status_change(order_id, new_status)` — status xabari

```python
# backend/services/order_service.py
class OrderService:
    def __init__(
        self,
        order_repo: OrderRepository,
        cart_service: CartService,
        notification_service: NotificationService,
    ):
        self.order_repo = order_repo
        self.cart_service = cart_service
        self.notification = notification_service
    
    async def create_order(self, user_id: int, data: dict) -> Order:
        # 1. Validate items
        total = await self.cart_service.calculate_total(user_id)
        if total < 10_000:
            raise ValueError("Minimum buyurtma 10 000 so'm")
        
        # 2. Create order
        order = await self.order_repo.create(user_id=user_id, total=total, **data)
        
        # 3. Notify admin
        await self.notification.notify_admin(order.id)
        
        return order
```

#### VS Code Bajarish Tartibi
1. `backend/services/` papka
2. `order_service.py` — eng muhimi shu
3. `backend/main.py` da POST /orders endpointini service ishlatadigan qiling
4. Test: buyurtma yaratiladi?
5. Qolgan service lar

#### Acceptance Criteria
- [ ] Router faqat HTTP request/response
- [ ] Service faqat business logic
- [ ] Repository faqat DB
- [ ] `backend/main.py` kamida 100 qator qisqargan

#### Manual Testing
- [ ] `POST /orders` ishlaydi (service orqali)
- [ ] Xato bo'lsa rollback bo'ladi
- [ ] Admin xabar oladi

---

### P1-T3 — Pydantic schemas 🔴
> **Murakkablik:** Medium | **Dependency:** P1-T1
> **Branch:** `feat/pydantic-schemas`
> **Commit:** `feat: add pydantic v2 schemas for all endpoints`

#### Subtasklar
- [ ] `backend/schemas/user.py` — `UserCreate`, `UserRead`, `UserUpdate`
- [ ] `backend/schemas/order.py` — `OrderCreate`, `OrderRead`, `OrderStatusUpdate`
- [ ] `backend/schemas/product.py` — `ProductRead`, `CategoryRead`
- [ ] `backend/schemas/cart.py` — `CartItemAdd`, `CartItemRead`, `CartRead`
- [ ] `backend/schemas/payment.py` — `ClickCallback`, `PaymeRPC`
- [ ] `backend/schemas/address.py` — `AddressCreate`, `AddressRead`
- [ ] Barcha endpoint lar typed response qaytarsin

#### VS Code Bajarish Tartibi
1. `backend/schemas/` papka
2. Har schema uchun alohida fayl
3. `model_config = ConfigDict(from_attributes=True)` — ORM integration
4. `/docs` da schema lar ko'rinishini tekshiring

#### Acceptance Criteria
- [ ] `/docs` da barcha schema ko'rinadi
- [ ] Invalid JSON → 422 qaytaradi
- [ ] ORM model → schema conversion ishlaydi

#### Manual Testing
- [ ] `GET /products` — `[{id, name, price, ...}]` qaytaradi
- [ ] `POST /orders` noto'g'ri data → 422 + error details
- [ ] `/docs` da "Try it out" ishlaydi

---

## PHASE 2 — Order Flow & Payment
> **Maqsad:** To'lov va buyurtma flow ni production-ready qilish
> **Taxminiy vaqt:** 7–10 kun | **Priority:** MUST-HAVE

---

### P2-T1 — To'liq Order Status Flow 🟡
> **Murakkablik:** Hard | **Dependency:** P1-T2
> **Branch:** `feat/order-status-flow`
> **Commit:** `feat: implement order status state machine`
> **Hozirgi holat:** Admin status o'zgartira oladi (`backend/main.py:454`), lekin transition validatsiya yo'q

#### Subtasklar
- [x] Admin status o'zgartirishi — `backend/main.py:454` (mavjud)
- [x] Foydalanuvchiga status xabari — `backend/main.py:454` (mavjud)
- [ ] `OrderStatus` Enum yaratish: `PENDING`, `CONFIRMED`, `PREPARING`, `DELIVERING`, `DELIVERED`, `CANCELLED`
- [ ] `VALID_TRANSITIONS` dict — qaysi statusdan qaysi statusga o'tish mumkin
- [ ] `validate_transition(old, new)` — noto'g'ri transition → 400 error
- [ ] `order_status_history` jadval (migration)
  - [ ] `order_id`, `old_status`, `new_status`, `changed_by`, `changed_at`, `notes`
- [ ] Har status o'zgarishda `order_status_history` ga yozish
- [ ] Foydalanuvchi faqat `PENDING` da `CANCELLED` qila oladi

```python
# backend/services/order_service.py
VALID_TRANSITIONS = {
    "PENDING": ["CONFIRMED", "CANCELLED"],
    "CONFIRMED": ["PREPARING", "CANCELLED"],
    "PREPARING": ["DELIVERING"],
    "DELIVERING": ["DELIVERED"],
    "DELIVERED": [],
    "CANCELLED": [],
}

async def update_status(self, order_id: int, new_status: str, changed_by: str):
    order = await self.order_repo.get(order_id)
    allowed = VALID_TRANSITIONS.get(order.status, [])
    if new_status not in allowed:
        raise ValueError(f"{order.status} → {new_status} mumkin emas")
    # ... update + history + notify
```

#### VS Code Bajarish Tartibi
1. `database/models.py` da `OrderStatus` Enum
2. `OrderStatusHistory` model qo'shing
3. `alembic revision --autogenerate -m "add_order_status_history"`
4. `order_service.py` da `update_status()` ni `VALID_TRANSITIONS` bilan yozing
5. `backend/main.py` da admin status endpoint ni service ishlatadigan qiling

#### Acceptance Criteria
- [ ] `PENDING → CONFIRMED` ishlaydi
- [ ] `DELIVERED → PENDING` → 400 error
- [ ] `order_status_history` da yozuv qoladi
- [ ] Har statusda user xabar oladi

#### Manual Testing
- [ ] Admin `PENDING → CONFIRMED` → user xabar oladi
- [ ] `DELIVERED → PENDING` urinish → xato xabar
- [ ] DB da `order_status_history` yozuvlar bor

---

### P2-T2 — Click to'lov signature verify 🟡
> **Murakkablik:** Hard | **Dependency:** P1-T2
> **Branch:** `feat/click-signature-verify`
> **Commit:** `feat: add click payment hmac signature verification`
> **Hozirgi holat:** Click redirect ishlaydi (`backend/main.py:335`), lekin callback verify yo'q

#### Subtasklar
- [x] Click URL generatsiya — `backend/main.py:335` (mavjud)
- [ ] `POST /payment/click/prepare` — signature verify qo'shish
- [ ] `POST /payment/click/complete` — signature verify + order update
- [ ] `PaymentService.verify_click_sign(params)` — MD5 hash tekshirish
- [ ] `payments` jadval (migration) — to'lov yozuvlari
- [ ] Muvaffaqiyatli to'lov → `order.status = CONFIRMED`
- [ ] Muvaffaqiyatsiz to'lov → user ga xabar
- [ ] Idempotency: bir buyurtmaga bir to'lov

```python
# backend/services/payment_service.py
import hashlib

def verify_click_sign(self, params: dict) -> bool:
    sign_string = "".join([
        str(params["click_trans_id"]),
        str(params["service_id"]),
        self.click_secret_key,
        str(params["merchant_trans_id"]),
        str(params["amount"]),
        str(params["action"]),
        str(params["sign_time"]),
    ])
    expected = hashlib.md5(sign_string.encode()).hexdigest()
    return expected == params["sign_string"]
```

#### VS Code Bajarish Tartibi
1. Click API docs o'qing: docs.click.uz
2. `payment_service.py` da `verify_click_sign()` yozing
3. Postman da Click sandbox bilan test
4. `backend/main.py` da callback handler ni update qiling

#### Acceptance Criteria
- [ ] Click prepare — 200 qaytaradi
- [ ] Noto'g'ri sign — 400 qaytaradi
- [ ] Muvaffaqiyatli to'lov → order CONFIRMED
- [ ] User "To'lov qabul qilindi" xabari oladi

#### Manual Testing
- [ ] Sandbox to'lov → order status o'zgaradi
- [ ] Noto'g'ri sign bilan so'rov → rad etiladi
- [ ] DB da payment yozuv bor

---

### P2-T3 — Payme to'lov to'liq implementatsiya 🟡
> **Murakkablik:** Hard | **Dependency:** P2-T2
> **Branch:** `feat/payme-payment`
> **Commit:** `feat: implement payme jsonrpc payment handler`
> **Hozirgi holat:** Payme URL generatsiya bor (`backend/main.py:335`), JSONRPC handler yo'q

#### Subtasklar
- [x] Payme URL generatsiya — mavjud
- [ ] `POST /payment/payme` — JSONRPC endpoint
- [ ] `CheckPerformTransaction` — buyurtma mavjudmi?
- [ ] `CreateTransaction` — tranzaksiya yaratish
- [ ] `PerformTransaction` — to'lov tasdiqlash
- [ ] `CancelTransaction` — bekor qilish
- [ ] Basic Auth verify: `base64(PAYME_KEY)`
- [ ] Amount validation: tiyin → so'm konversiya

```python
# backend/routers/payments.py
@router.post("/payment/payme")
async def payme_handler(request: Request, service: PaymentService = Depends()):
    # Auth check
    auth = request.headers.get("Authorization", "")
    if not service.verify_payme_auth(auth):
        return {"error": {"code": -32504, "message": "Incorrect login"}}
    
    body = await request.json()
    method = body.get("method")
    params = body.get("params", {})
    id_ = body.get("id")
    
    match method:
        case "CheckPerformTransaction":
            result = await service.check_perform(params)
        case "CreateTransaction":
            result = await service.create_transaction(params)
        case "PerformTransaction":
            result = await service.perform_transaction(params)
        case "CancelTransaction":
            result = await service.cancel_transaction(params)
        case _:
            return {"error": {"code": -32601, "message": "Method not found"}, "id": id_}
    
    return {"result": result, "id": id_}
```

#### VS Code Bajarish Tartibi
1. Payme test merchant oling: test.paycom.uz
2. `payment_service.py` da JSONRPC metodlar yozing
3. Postman Collection: Payme test
4. Real so'm bilan test QILMANG — sandbox

#### Acceptance Criteria
- [ ] `CheckPerformTransaction` — buyurtma bor → `{"allow": true}`
- [ ] `CreateTransaction` — DB ga yoziladi
- [ ] `PerformTransaction` → order CONFIRMED
- [ ] Noto'g'ri auth → `-32504`

#### Manual Testing
- [ ] Payme sandbox to'lov ishlaydi
- [ ] `CancelTransaction` → order CANCELLED
- [ ] DB da transaction yozuv bor

---

### P2-T4 — Naqd to'lov (Cash on Delivery) 🔴
> **Murakkablik:** Easy | **Dependency:** P2-T1
> **Branch:** `feat/cash-payment`
> **Commit:** `feat: add cash on delivery payment option`

#### Subtasklar
- [ ] `PaymentMethod` enum: `CLICK`, `PAYME`, `CASH` (`database/models.py`)
- [ ] `database/models.py` da `payment_method` field `orders` jadvaliga
- [ ] `frontend/app.js` da payment tanlov UI (3 tugma)
- [ ] WebApp → Backend: `payment_method` parametrini jo'natish
- [ ] Cash order da to'lov redirect YO'Q
- [ ] Cash order da `payment_status = AWAITING_CASH`
- [ ] Admin da cash order belgi — "💵 Naqd"
- [ ] Admin "Naqd qabul qilindi" tugmasi → `CASH_RECEIVED`

#### VS Code Bajarish Tartibi
1. `database/models.py` da `PaymentMethod` enum va field qo'shing
2. `alembic revision --autogenerate -m "add_payment_method"` → `upgrade head`
3. `frontend/app.js` da 3 ta payment button
4. `backend/main.py` POST /orders da `payment_method` qabul qilish
5. Admin handler da cash badge

#### Acceptance Criteria
- [ ] Foydalanuvchi payment usulini tanlaydi
- [ ] Cash tanlaganda to'lov redirect bo'lmaydi
- [ ] Admin "💵 Naqd" badge ko'radi
- [ ] Cash order DB da `payment_method = CASH`

#### Manual Testing
- [ ] "Naqd to'lash" bosilganda buyurtma yaratiladi (redirect yo'q)
- [ ] Admin panelda cash order "💵" belgisi bilan ko'rinadi
- [ ] Online to'lov hali ham ishlaydi

---

## PHASE 3 — UX Improvements
> **Maqsad:** Foydalanuvchi tajribasini yaxshilash
> **Taxminiy vaqt:** 5–7 kun | **Priority:** SHOULD-HAVE

---

### P3-T1 — Saqlangan Manzillar (Saved Addresses) 🔴
> **Murakkablik:** Medium | **Dependency:** P2-T1
> **Branch:** `feat/saved-addresses`
> **Commit:** `feat: add saved addresses functionality`

#### Subtasklar
- [ ] `addresses` jadval (migration): `id, user_id, label, address_text, latitude, longitude, is_default`
- [ ] `AddressRepository` — CRUD
- [ ] `GET /addresses` — foydalanuvchi manzillari
- [ ] `POST /addresses` — yangi manzil saqlash
- [ ] `DELETE /addresses/{id}` — o'chirish
- [ ] `PATCH /addresses/{id}/default` — default qilish
- [ ] Max 5 ta manzil chegarasi
- [ ] `frontend/app.js` — saqlangan manzillar section
- [ ] Birinchi manzil auto default

#### Manual Testing
- [ ] Manzil saqlanadi
- [ ] Keyingi buyurtmada tanlanadi
- [ ] 6-chi manzil → xato

---

### P3-T2 — Qayta Buyurtma (Reorder) 🔴
> **Murakkablik:** Easy | **Dependency:** P2-T1
> **Branch:** `feat/reorder`
> **Commit:** `feat: add reorder from history`

#### Subtasklar
- [ ] `POST /orders/{id}/reorder` endpoint
- [ ] Eski order itemlardan cart yaratish (`CartService.from_order()`)
- [ ] Mavjud bo'lmagan mahsulot → skip + xabar
- [ ] Bot buyurtmalar tarixida "🔁 Qayta buyurtma" tugmasi
- [ ] WebApp ga o'tish cart to'ldirilgan holda

#### Manual Testing
- [ ] Eski buyurtmadan "🔁" bosiladi
- [ ] WebApp ochiladi, cart to'ldirilgan
- [ ] O'chirilgan mahsulot skip bo'ladi

---

### P3-T3 — i18n Centralizatsiya 🟡
> **Murakkablik:** Medium | **Dependency:** P0-T1
> **Branch:** `refactor/i18n`
> **Commit:** `refactor: centralize all text strings in locale files`
> **Hozirgi holat:** `utils/texts.py` mavjud — lekin to'liq emas, ba'zi matnlar handler da

#### Subtasklar
- [x] `utils/texts.py` — mavjud (to'liq emas)
- [ ] `bot/locales/uz.json` — barcha uz matnlar
- [ ] `bot/locales/ru.json` — barcha ru matnlar
- [ ] `bot/locales/en.json` — barcha en matnlar
- [ ] `utils/i18n.py` — `get_text(key, lang)` funksiya
- [ ] Barcha hardcoded matnlar handler larda → locale faylga
- [ ] `user.language` DB da saqlanadi
- [ ] Har handler da `lang = await get_user_lang(user_id)` chaqirish

#### Manual Testing
- [ ] `/start` uz tilida ishlaydi
- [ ] `/language` ru ga o'giradi — hamma joy ruscha
- [ ] Yangi matn qo'shish faqat JSON faylda

---

## PHASE 4 — Admin Panel
> **Maqsad:** Admin boshqaruvini kengaytirish
> **Taxminiy vaqt:** 5–7 kun | **Priority:** MUST-HAVE

---

### P4-T1 — Admin Telegram Panel yaxshilash 🟡
> **Murakkablik:** Hard | **Dependency:** P2-T1
> **Branch:** `feat/admin-panel-enhanced`
> **Commit:** `feat: enhance admin bot panel with full order management`
> **Hozirgi holat:** Admin status o'zgartira oladi, yangi buyurtma xabari bor

#### Subtasklar
- [x] Admin status o'zgartirish — mavjud
- [x] Yangi buyurtma notification — mavjud
- [ ] `bot/middlewares/admin_check.py` — `ADMIN_IDS` filter
- [ ] `/admin_orders` — pending buyurtmalar ro'yxati (inline keyboard)
- [ ] Buyurtma detail view — user, manzil, mahsulotlar, summa
- [ ] Payment method ko'rish (💳 Click / 💳 Payme / 💵 Naqd)
- [ ] `/admin_stats` — bugungi buyurtmalar soni + tushum
- [ ] Admin `/admin_help` — barcha buyruqlar ro'yxati
- [ ] Faqat ADMIN_IDS da bo'lganlar panel ishlatadi

#### Manual Testing
- [ ] Admin `/admin_orders` → pending ro'yxat
- [ ] Buyurtma bosilsa detail ko'rinadi
- [ ] Noadmin user `admin_orders` yozsa "ruxsat yo'q"
- [ ] `/admin_stats` → bugungi statistika

---

### P4-T2 — Admin Web Panel (FastAPI + Jinja2) 🔴
> **Murakkablik:** Hard | **Dependency:** P1-T2
> **Branch:** `feat/web-admin`
> **Commit:** `feat: add web admin panel with jinja2 templates`

#### Subtasklar
- [ ] `pip install jinja2 python-multipart`
- [ ] `admin/` papka + `admin/templates/`
- [ ] `GET /admin` — login sahifa
- [ ] `GET /admin/orders` — barcha buyurtmalar (filter: status, sana)
- [ ] `GET /admin/products` — mahsulot CRUD
- [ ] `GET /admin/categories` — kategoriya CRUD
- [ ] `GET /admin/users` — foydalanuvchilar ro'yxati
- [ ] Admin session yoki token auth
- [ ] Buyurtma export CSV

#### Manual Testing
- [ ] `/admin` → login ko'rinadi
- [ ] Login → buyurtmalar ko'rinadi
- [ ] Noadmin login → redirect

---

## PHASE 5 — Growth Features
> **Maqsad:** O'sish mexanizmlari qo'shish
> **Taxminiy vaqt:** 7–10 kun | **Priority:** SHOULD-HAVE

---

### P5-T1 — Promo Kod Tizimi 🔴
> **Murakkablik:** Medium | **Dependency:** P2-T1
> **Branch:** `feat/promo-codes`
> **Commit:** `feat: implement promo code system`

#### Subtasklar
- [ ] `promo_codes` jadval: `id, code(UNIQUE), type, value, min_order_amount, max_uses, used_count, expires_at, is_active`
- [ ] `promo_code_uses` jadval: `UNIQUE(promo_code_id, user_id)` — bir marta ishlatish
- [ ] `POST /promo/validate` — kod + cart_amount → chegirma
- [ ] `PromoService.apply(code, user_id, amount)`
- [ ] Frontend da promo code input field
- [ ] Order yaratishda `promo_code_id` saqlash
- [ ] Admin da promo kod CRUD

```python
async def apply(self, code: str, user_id: int, amount: int) -> dict:
    promo = await self.promo_repo.get_by_code(code)
    
    if not promo or not promo.is_active:
        raise InvalidPromoCode("Kod topilmadi yoki faol emas")
    
    if promo.expires_at and promo.expires_at < datetime.now():
        raise InvalidPromoCode("Kod muddati tugagan")
    
    if promo.used_count >= promo.max_uses:
        raise InvalidPromoCode("Kod limitga yetgan")
    
    # User bu kodni ishlatganmi?
    used = await self.promo_repo.check_used(promo.id, user_id)
    if used:
        raise InvalidPromoCode("Siz bu kodni allaqachon ishlatgansiz")
    
    if amount < promo.min_order_amount:
        raise InvalidPromoCode(f"Minimum buyurtma: {promo.min_order_amount} so'm")
    
    discount = amount * promo.value / 100 if promo.type == "percent" else promo.value
    return {"discount": discount, "final_amount": amount - discount}
```

#### Manual Testing
- [ ] To'g'ri kod → chegirma hisoblanadi
- [ ] Muddati o'tgan kod → xato
- [ ] Ikki marta ishlatish → xato
- [ ] Noto'g'ri kod → xato

---

### P5-T2 — Referral Tizimi 🔴
> **Murakkablik:** Medium | **Dependency:** P2-T1
> **Branch:** `feat/referral-system`
> **Commit:** `feat: implement referral system with bonus`

#### Subtasklar
- [ ] `users` jadvalga: `referral_code(UNIQUE)`, `bonus_balance` field
- [ ] `referrals` jadval: `referrer_id, referred_id(UNIQUE), bonus_given, bonus_amount, created_at`
- [ ] Ro'yxatdan o'tishda `referral_code` auto generate (UUID short)
- [ ] `/start?ref=CODE` — referral link orqali onboarding
- [ ] `onboarding.py` da `deep_link` parse qilish
- [ ] Taklif qilingan birinchi buyurtma → referrer ga bonus
- [ ] `GET /referral/info` — o'z referral linki va statistika
- [ ] Bonus `users.bonus_balance` ga qo'shiladi
- [ ] Checkout da bonus ishlatish imkoni

#### Manual Testing
- [ ] `/start?ref=ABC123` → referral saqlanadi
- [ ] Birinchi buyurtma → referrer bonus oladi
- [ ] `/referral/info` → to'g'ri statistika

---

## PHASE 6 — Testing
> **Maqsad:** Ishonchlilik va xavfsizlikni ta'minlash
> **Taxminiy vaqt:** 5–7 kun | **Priority:** MUST-HAVE before launch

---

### P6-T1 — Unit Tests 🔴
> **Murakkablik:** Medium | **Dependency:** P1-T2
> **Branch:** `feat/unit-tests`
> **Commit:** `test: add unit tests for services`

#### Subtasklar
- [ ] `pip install pytest pytest-asyncio pytest-mock`
- [ ] `tests/conftest.py` — test DB (SQLite in-memory), fixtures
- [ ] `tests/unit/test_order_service.py`
  - [ ] `test_create_order_success`
  - [ ] `test_create_order_minimum_amount_fail`
  - [ ] `test_update_status_valid_transition`
  - [ ] `test_update_status_invalid_transition`
  - [ ] `test_cancel_order_pending`
  - [ ] `test_cancel_order_not_pending_fail`
- [ ] `tests/unit/test_cart_service.py`
  - [ ] `test_add_item`, `test_remove_item`, `test_calculate_total`
- [ ] `tests/unit/test_payment_service.py`
  - [ ] `test_verify_click_sign_valid`
  - [ ] `test_verify_click_sign_invalid`

#### Manual Testing
- [ ] `pytest tests/unit/ -v` — barcha o'tadi
- [ ] `pytest --cov=backend/services` — coverage ko'rinadi

---

### P6-T2 — API Tests 🔴
> **Murakkablik:** Medium | **Dependency:** P6-T1
> **Branch:** `feat/api-tests`
> **Commit:** `test: add api integration tests`

#### Subtasklar
- [ ] `pip install httpx`
- [ ] `tests/api/test_orders_api.py`
  - [ ] `test_create_order_success`
  - [ ] `test_create_order_invalid_data`
  - [ ] `test_get_orders_pagination`
  - [ ] `test_cancel_order`
- [ ] `tests/api/test_payment_api.py`
  - [ ] `test_click_prepare_valid_sign`
  - [ ] `test_click_prepare_invalid_sign`
  - [ ] `test_payme_check_perform`
- [ ] `tests/api/test_promo_api.py`
  - [ ] `test_validate_valid_promo`
  - [ ] `test_validate_expired_promo`
  - [ ] `test_validate_max_uses`

#### Manual Testing
- [ ] `pytest tests/api/ -v` — barcha o'tadi
- [ ] `pytest --cov=backend` — 60%+ coverage

---

### P6-T3 — Payment Tests (Sandbox) 🔴
> **Murakkablik:** Hard | **Dependency:** P6-T2
> **Branch:** `test/payment-sandbox`
> **Commit:** `test: verify payment flows with sandbox`

#### Subtasklar
- [ ] Click sandbox test merchant olish
- [ ] Payme test merchant olish (test.paycom.uz)
- [ ] End-to-end: buyurtma → Click to'lov → status o'zgarish
- [ ] End-to-end: buyurtma → Payme to'lov → status o'zgarish
- [ ] To'lov muvaffaqiyatsiz → order holati tekshirish
- [ ] Ikki marta callback → idempotency tekshirish

#### Manual Testing
- [ ] Click sandbox: to'lov muvaffaqiyatli → order CONFIRMED
- [ ] Payme sandbox: to'lov muvaffaqiyatli → order CONFIRMED
- [ ] Ikki marta `/click/complete` → ikkinchisi 200 (idempotent)

---

[← README](./README.md) | [Keyingi: Sprint Planning →](./03_sprint_planning.md)

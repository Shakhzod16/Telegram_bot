# 02 вЂ” Developer Execution Board

> **Foydalanish:** `- [ ]` ni `- [x]` ga o'zgartiring yoki VS Code da checkbox ni bosing.
> **рџџў** = Hozir loyihada ishlaydi | **рџ”ґ** = Hali yo'q | **рџџЎ** = Qisman bor

---

## PHASE 0 вЂ” Foundation & Code Quality
> **Maqsad:** Loyihani mustahkam poydevorga qo'yish вЂ” xato bo'lmaydi, config tartibli, log yoziladi
> **Taxminiy vaqt:** 3вЂ“5 kun | **Priority:** MUST-HAVE

---

### P0-T1 вЂ” Loyiha strukturasini qayta tartiblashtirish рџ”ґ
> **Murakkablik:** Medium | **Dependency:** Yo'q
> **Branch:** `refactor/project-structure`
> **Commit:** `refactor: reorganize project into layered architecture`

#### Subtasklar
- [x] `backend/routers/` papka yaratish в†’ `backend/routers/__init__.py`
- [x] `backend/services/` papka yaratish в†’ `backend/services/__init__.py`
- [x] `backend/repositories/` papka yaratish в†’ `backend/repositories/__init__.py`
- [x] `backend/schemas/` papka yaratish в†’ `backend/schemas/__init__.py`
- [x] `bot/middlewares/` papka yaratish в†’ `bot/middlewares/__init__.py`
- [x] `bot/keyboards/` papka yaratish в†’ `bot/keyboards/__init__.py`
- [x] `bot/states/` papka yaratish в†’ `bot/states/__init__.py`
- [x] `config/` papka + `config/settings.py` yaratish
- [x] `tests/` papka + `tests/__init__.py` + `pytest.ini` yaratish
- [x] Mavjud import larni yangi strukturaga moslashtirish

#### VS Code Bajarish Tartibi
1. Explorer da papkalar yarating (right-click в†’ New Folder)
2. Har papkaga `__init__.py` qo'shing
3. `python -m bot.main` вЂ” ishlaydimi tekshirish
4. `curl http://localhost:8000/docs` вЂ” API ishlayaptimy

#### Acceptance Criteria
- [x] Bot `/start` ga javob beradi
- [x] FastAPI `/docs` ochiladi
- [x] Hech qanday `ImportError` yo'q
- [x] `pytest` xatosiz ishga tushadi (0 test bo'lsa ham)

#### Manual Testing
- [x] Bot `/start` bosilganda menyu ko'rinadi
- [x] `/docs` da endpoint lar ko'rinadi
- [x] Terminal da `ImportError` yo'q

---

### P0-T2 вЂ” Settings va .env management рџ”ґ
> **Murakkablik:** Easy | **Dependency:** P0-T1
> **Branch:** `feat/config-env`
> **Commit:** `feat: add pydantic settings and .env structure`

#### Subtasklar
- [x] `pip install pydantic-settings` в†’ `requirements.txt` ga qo'shish
- [x] `config/settings.py` вЂ” `Settings(BaseSettings)` class yaratish
- [x] `.env.example` вЂ” barcha o'zgaruvchilar (sharh bilan)
- [x] `.env.development` va `.env.production` ajratish
- [x] `BOT_TOKEN` ni `.env` dan o'qish (`bot/main.py`)
- [x] `DATABASE_URL` ni `.env` dan o'qish (`backend/main.py`)
- [x] `CLICK_*` kalitlarni `.env` ga ko'chirish
- [x] `PAYME_*` kalitlarni `.env` ga ko'chirish
- [x] `WEB_APP_URL` ni `.env` dan o'qish (hozir `.env:2` da bor вЂ” yangi settings orqali)
- [x] `API_BASE_URL` ni `.env` ga ko'chirish (hozir `frontend/index.html:14-15` da hardcoded)
- [x] `.env` ni `.gitignore` ga qo'shish (agar yo'q bo'lsa)

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
2. `Ctrl+Shift+F` в†’ hardcoded token/key larni qidiring
3. Topilganlarni `settings.VARIABLE_NAME` bilan almashtiring
4. `python -c "from config.settings import settings; print(settings.BOT_TOKEN)"` test

#### Acceptance Criteria
- [x] `from config.settings import settings` ishlaydi
- [x] Hech qanday hardcoded token/secret kod ichida yo'q
- [x] `.env.example` to'liq va sharhlangan
- [x] `.env` git da ko'rinmaydi

#### Manual Testing
- [x] `.env` faylini o'chirish в†’ `ValidationError` chiqadi
- [x] `.env` qaytarish в†’ bot ishlaydi
- [x] `git status` da `.env` ko'rinmaydi

---

### P0-T3 вЂ” Logging sozlash рџ”ґ
> **Murakkablik:** Easy | **Dependency:** P0-T2
> **Branch:** `feat/logging`
> **Commit:** `feat: add structured logging with file rotation`

#### Subtasklar
- [x] `utils/logger.py` yaratish
- [x] `RotatingFileHandler` вЂ” `logs/app.log`, max 10MB, 5 backup
- [x] Log levels: `DEBUG` dev da, `INFO` prod da
- [x] FastAPI middleware вЂ” har request log (method, path, status, ms)
- [x] Bot da `logger.info` вЂ” `/start`, buyurtma, to'lov
- [x] Bot da `logger.error` вЂ” exception bilan birga

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
4. Bot start qiling в†’ `logs/app.log` fayl paydo bo'ladimi?

#### Acceptance Criteria
- [x] `logs/app.log` avtomatik yaratiladi
- [x] Har API request loglangan (GET /path в†’ 200 в†’ 45ms)
- [x] Bot xatolari stacktrace bilan loglangan
- [x] Log fayl 10MB dan oshsa rotate bo'ladi

#### Manual Testing
- [x] `/start` bosing в†’ log da ko'rinadi
- [x] Noto'g'ri endpoint в†’ log da 404 ko'rinadi
- [x] `cat logs/app.log | grep ERROR` вЂ” bo'sh bo'lishi kerak

---

### P0-T4 вЂ” Global error handling рџ”ґ
> **Murakkablik:** Medium | **Dependency:** P0-T3
> **Branch:** `feat/error-handling`
> **Commit:** `feat: add global error handlers for bot and api`

#### Subtasklar
- [x] `backend/exceptions.py` вЂ” custom exception classlar
- [x] FastAPI `@app.exception_handler(Exception)` вЂ” structured JSON error
- [x] FastAPI `@app.exception_handler(HTTPException)` вЂ” standart error
- [x] `bot/middlewares/error_middleware.py` вЂ” global bot exception handler
- [x] Foydalanuvchiga xato xabari (3 tilda) вЂ” "Xatolik yuz berdi, qayta urining"
- [x] Exception larda `logger.error(exc_info=True)` chaqirish

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
4. Test: handler da `raise Exception("test")` qo'shing в†’ bot crash bo'lmasligini tekshiring

#### Acceptance Criteria
- [x] Bot istalgan xatoda crash bo'lmaydi
- [x] User xato xabarini oladi (o'z tilida)
- [x] API 500 da `{"error": "...", "code": 500}` qaytaradi
- [x] Xato log ga tushadi

#### Manual Testing
- [x] Noto'g'ri buyurtma jo'nating в†’ bot ishlashda davom etadi
- [x] `GET /nonexistent` в†’ `{"error": "Not found", "code": 404}` qaytaradi
- [x] Log da xato ko'rinadi

---

### P0-T5 вЂ” Database migration (Alembic) рџ”ґ
> **Murakkablik:** Medium | **Dependency:** P0-T1
> **Branch:** `feat/alembic-migrations`
> **Commit:** `feat: add alembic for database versioning`

#### Subtasklar
- [x] `pip install alembic` в†’ `requirements.txt`
- [x] `alembic init migrations` вЂ” papka yaratish
- [x] `alembic.ini` da `DATABASE_URL` ni settings dan o'qish
- [x] `migrations/env.py` da `target_metadata = Base.metadata` qo'yish
- [x] Birinchi migration: `alembic revision --autogenerate -m "initial_tables"`
- [x] `alembic upgrade head` ishlatib tekshirish
- [x] `Makefile` yoki `scripts/migrate.sh` yaratish

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
4. `migrations/versions/` da fayl paydo bo'ldi? в†’ `alembic upgrade head`
5. DB da jadvallarni tekshiring (DBeaver yoki `sqlite3` CLI)

#### Acceptance Criteria
- [x] `alembic upgrade head` xatosiz ishlaydi
- [x] `alembic history` bo'sh emas
- [x] Jadvallar DB da ko'rinadi
- [x] `alembic downgrade -1` va `upgrade head` ishlaydi

#### Manual Testing
- [x] `alembic current` вЂ” versiya ko'rsatadi
- [x] `alembic show head` вЂ” migration tafsiloti
- [x] DB da `alembic_version` jadval bor

---

## PHASE 1 вЂ” Core Backend Layering
> **Maqsad:** Kod arxitekturasini layerlarga bo'lish вЂ” router, service, repository
> **Taxminiy vaqt:** 5вЂ“7 kun | **Priority:** MUST-HAVE

---

### P1-T1 вЂ” Repository pattern рџ”ґ
> **Murakkablik:** Hard | **Dependency:** P0-T5
> **Branch:** `refactor/repository-pattern`
> **Commit:** `refactor: extract db queries into repository classes`

#### Subtasklar
- [x] `backend/repositories/base.py` вЂ” `BaseRepository[T]` generic class
- [x] `backend/repositories/user_repo.py` вЂ” `UserRepository`
  - [x] `get(user_id)`, `get_by_telegram_id(tg_id)`, `create(data)`, `update(user_id, data)`
- [x] `backend/repositories/order_repo.py` вЂ” `OrderRepository`
  - [x] `get(order_id)`, `get_by_user(user_id)`, `create(data)`, `update_status(order_id, status)`
- [x] `backend/repositories/product_repo.py` вЂ” `ProductRepository`
  - [x] `get_all()`, `get_by_category(cat_id)`, `get(product_id)`
- [x] `backend/repositories/cart_repo.py` вЂ” `CartRepository`
  - [x] `get_by_user(user_id)`, `add_item(user_id, product_id, qty)`, `remove_item(item_id)`, `clear(user_id)`
- [x] `backend/database.py` вЂ” async session dependency

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
- [x] Barcha DB query lar repository orqali ketadi
- [x] Handler da to'g'ridan-to'g'ri `session.query` yo'q
- [x] Async CRUD: `get`, `create`, `update`, `delete`

#### Manual Testing
- [x] `GET /orders` ishlaydi (repo orqali)
- [x] Yangi user yaratiladi (repo orqali)
- [x] Mavjud endpoint lar buzilmagan

---

### P1-T2 вЂ” Service layer рџ”ґ
> **Murakkablik:** Hard | **Dependency:** P1-T1
> **Branch:** `refactor/service-layer`
> **Commit:** `refactor: add service layer for business logic`

#### Subtasklar
- [x] `backend/services/order_service.py` вЂ” `OrderService`
  - [x] `create_order(user_id, items, address, payment_method)`
  - [x] `update_status(order_id, new_status, changed_by)`
  - [x] `cancel_order(order_id, user_id)`
  - [x] `get_user_orders(user_id, page, limit)`
- [x] `backend/services/cart_service.py` вЂ” `CartService`
  - [x] `add_item(user_id, product_id, qty)`
  - [x] `remove_item(user_id, item_id)`
  - [x] `calculate_total(user_id)`
  - [x] `clear(user_id)`
- [x] `backend/services/payment_service.py` вЂ” `PaymentService`
  - [x] `generate_click_url(order_id, amount)`
  - [x] `verify_click_hash(params)` вЂ” HMAC verify
  - [x] `generate_payme_url(order_id, amount)`
  - [x] `process_payme_rpc(method, params)` вЂ” JSONRPC
- [x] `backend/services/notification_service.py` вЂ” `NotificationService`
  - [x] `notify_user(user_id, message)` вЂ” Telegram xabar
  - [x] `notify_admin(order_id)` вЂ” admin ga yangi buyurtma
  - [x] `notify_status_change(order_id, new_status)` вЂ” status xabari

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
2. `order_service.py` вЂ” eng muhimi shu
3. `backend/main.py` da POST /orders endpointini service ishlatadigan qiling
4. Test: buyurtma yaratiladi?
5. Qolgan service lar

#### Acceptance Criteria
- [x] Router faqat HTTP request/response
- [x] Service faqat business logic
- [x] Repository faqat DB
- [x] `backend/main.py` kamida 100 qator qisqargan

#### Manual Testing
- [x] `POST /orders` ishlaydi (service orqali)
- [x] Xato bo'lsa rollback bo'ladi
- [x] Admin xabar oladi

---

### P1-T3 вЂ” Pydantic schemas рџ”ґ
> **Murakkablik:** Medium | **Dependency:** P1-T1
> **Branch:** `feat/pydantic-schemas`
> **Commit:** `feat: add pydantic v2 schemas for all endpoints`

#### Subtasklar
- [x] `backend/schemas/user.py` вЂ” `UserCreate`, `UserRead`, `UserUpdate`
- [x] `backend/schemas/order.py` вЂ” `OrderCreate`, `OrderRead`, `OrderStatusUpdate`
- [x] `backend/schemas/product.py` вЂ” `ProductRead`, `CategoryRead`
- [x] `backend/schemas/cart.py` вЂ” `CartItemAdd`, `CartItemRead`, `CartRead`
- [x] `backend/schemas/payment.py` вЂ” `ClickCallback`, `PaymeRPC`
- [x] `backend/schemas/address.py` вЂ” `AddressCreate`, `AddressRead`
- [x] Barcha endpoint lar typed response qaytarsin

#### VS Code Bajarish Tartibi
1. `backend/schemas/` papka
2. Har schema uchun alohida fayl
3. `model_config = ConfigDict(from_attributes=True)` вЂ” ORM integration
4. `/docs` da schema lar ko'rinishini tekshiring

#### Acceptance Criteria
- [x] `/docs` da barcha schema ko'rinadi
- [x] Invalid JSON в†’ 422 qaytaradi
- [x] ORM model в†’ schema conversion ishlaydi

#### Manual Testing
- [x] `GET /products` вЂ” `[{id, name, price, ...}]` qaytaradi
- [x] `POST /orders` noto'g'ri data в†’ 422 + error details
- [x] `/docs` da "Try it out" ishlaydi

---

## PHASE 2 вЂ” Order Flow & Payment
> **Maqsad:** To'lov va buyurtma flow ni production-ready qilish
> **Taxminiy vaqt:** 7вЂ“10 kun | **Priority:** MUST-HAVE

---

### P2-T1 вЂ” To'liq Order Status Flow рџџЎ
> **Murakkablik:** Hard | **Dependency:** P1-T2
> **Branch:** `feat/order-status-flow`
> **Commit:** `feat: implement order status state machine`
> **Hozirgi holat:** Admin status o'zgartira oladi (`backend/main.py:454`), lekin transition validatsiya yo'q

#### Subtasklar
- [x] Admin status o'zgartirishi вЂ” `backend/main.py:454` (mavjud)
- [x] Foydalanuvchiga status xabari вЂ” `backend/main.py:454` (mavjud)
- [x] `OrderStatus` Enum yaratish: `PENDING`, `CONFIRMED`, `PREPARING`, `DELIVERING`, `DELIVERED`, `CANCELLED`
- [x] `VALID_TRANSITIONS` dict вЂ” qaysi statusdan qaysi statusga o'tish mumkin
- [x] `validate_transition(old, new)` вЂ” noto'g'ri transition в†’ 400 error
- [x] `order_status_history` jadval (migration)
  - [x] `order_id`, `old_status`, `new_status`, `changed_by`, `changed_at`, `notes`
- [x] Har status o'zgarishda `order_status_history` ga yozish
- [x] Foydalanuvchi faqat `PENDING` da `CANCELLED` qila oladi

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
        raise ValueError(f"{order.status} в†’ {new_status} mumkin emas")
    # ... update + history + notify
```

#### VS Code Bajarish Tartibi
1. `database/models.py` da `OrderStatus` Enum
2. `OrderStatusHistory` model qo'shing
3. `alembic revision --autogenerate -m "add_order_status_history"`
4. `order_service.py` da `update_status()` ni `VALID_TRANSITIONS` bilan yozing
5. `backend/main.py` da admin status endpoint ni service ishlatadigan qiling

#### Acceptance Criteria
- [x] `PENDING в†’ CONFIRMED` ishlaydi
- [x] `DELIVERED в†’ PENDING` в†’ 400 error
- [x] `order_status_history` da yozuv qoladi
- [x] Har statusda user xabar oladi

#### Manual Testing
- [x] Admin `PENDING в†’ CONFIRMED` в†’ user xabar oladi
- [x] `DELIVERED в†’ PENDING` urinish в†’ xato xabar
- [x] DB da `order_status_history` yozuvlar bor

---

### P2-T2 вЂ” Click to'lov signature verify рџџЎ
> **Murakkablik:** Hard | **Dependency:** P1-T2
> **Branch:** `feat/click-signature-verify`
> **Commit:** `feat: add click payment hmac signature verification`
> **Hozirgi holat:** Click redirect ishlaydi (`backend/main.py:335`), lekin callback verify yo'q

#### Subtasklar
- [x] Click URL generatsiya вЂ” `backend/main.py:335` (mavjud)
- [x] `POST /payment/click/prepare` вЂ” signature verify qo'shish
- [x] `POST /payment/click/complete` вЂ” signature verify + order update
- [x] `PaymentService.verify_click_sign(params)` вЂ” MD5 hash tekshirish
- [x] `payments` jadval (migration) вЂ” to'lov yozuvlari
- [x] Muvaffaqiyatli to'lov в†’ `order.status = CONFIRMED`
- [x] Muvaffaqiyatsiz to'lov в†’ user ga xabar
- [x] Idempotency: bir buyurtmaga bir to'lov

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
- [x] Click prepare вЂ” 200 qaytaradi
- [x] Noto'g'ri sign вЂ” 400 qaytaradi
- [x] Muvaffaqiyatli to'lov в†’ order CONFIRMED
- [x] User "To'lov qabul qilindi" xabari oladi

#### Manual Testing
- [x] Sandbox to'lov в†’ order status o'zgaradi
- [x] Noto'g'ri sign bilan so'rov в†’ rad etiladi
- [x] DB da payment yozuv bor

---

### P2-T3 вЂ” Payme to'lov to'liq implementatsiya рџџЎ
> **Murakkablik:** Hard | **Dependency:** P2-T2
> **Branch:** `feat/payme-payment`
> **Commit:** `feat: implement payme jsonrpc payment handler`
> **Hozirgi holat:** Payme URL generatsiya bor (`backend/main.py:335`), JSONRPC handler yo'q

#### Subtasklar
- [x] Payme URL generatsiya вЂ” mavjud
- [x] `POST /payment/payme` вЂ” JSONRPC endpoint
- [x] `CheckPerformTransaction` вЂ” buyurtma mavjudmi?
- [x] `CreateTransaction` вЂ” tranzaksiya yaratish
- [x] `PerformTransaction` вЂ” to'lov tasdiqlash
- [x] `CancelTransaction` вЂ” bekor qilish
- [x] Basic Auth verify: `base64(PAYME_KEY)`
- [x] Amount validation: tiyin в†’ so'm konversiya

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
4. Real so'm bilan test QILMANG вЂ” sandbox

#### Acceptance Criteria
- [x] `CheckPerformTransaction` вЂ” buyurtma bor в†’ `{"allow": true}`
- [x] `CreateTransaction` вЂ” DB ga yoziladi
- [x] `PerformTransaction` в†’ order CONFIRMED
- [x] Noto'g'ri auth в†’ `-32504`

#### Manual Testing
- [x] Payme sandbox to'lov ishlaydi
- [x] `CancelTransaction` в†’ order CANCELLED
- [x] DB da transaction yozuv bor

---

### P2-T4 вЂ” Naqd to'lov (Cash on Delivery) рџ”ґ
> **Murakkablik:** Easy | **Dependency:** P2-T1
> **Branch:** `feat/cash-payment`
> **Commit:** `feat: add cash on delivery payment option`

#### Subtasklar
- [x] `PaymentMethod` enum: `CLICK`, `PAYME`, `CASH` (`database/models.py`)
- [x] `database/models.py` da `payment_method` field `orders` jadvaliga
- [x] `frontend/app.js` da payment tanlov UI (3 tugma)
- [x] WebApp в†’ Backend: `payment_method` parametrini jo'natish
- [x] Cash order da to'lov redirect YO'Q
- [x] Cash order da `payment_status = AWAITING_CASH`
- [x] Admin da cash order belgi вЂ” "рџ’µ Naqd"
- [x] Admin "Naqd qabul qilindi" tugmasi в†’ `CASH_RECEIVED`

#### VS Code Bajarish Tartibi
1. `database/models.py` da `PaymentMethod` enum va field qo'shing
2. `alembic revision --autogenerate -m "add_payment_method"` в†’ `upgrade head`
3. `frontend/app.js` da 3 ta payment button
4. `backend/main.py` POST /orders da `payment_method` qabul qilish
5. Admin handler da cash badge

#### Acceptance Criteria
- [x] Foydalanuvchi payment usulini tanlaydi
- [x] Cash tanlaganda to'lov redirect bo'lmaydi
- [x] Admin "рџ’µ Naqd" badge ko'radi
- [x] Cash order DB da `payment_method = CASH`

#### Manual Testing
- [x] "Naqd to'lash" bosilganda buyurtma yaratiladi (redirect yo'q)
- [x] Admin panelda cash order "рџ’µ" belgisi bilan ko'rinadi
- [x] Online to'lov hali ham ishlaydi

---

## PHASE 3 вЂ” UX Improvements
> **Maqsad:** Foydalanuvchi tajribasini yaxshilash
> **Taxminiy vaqt:** 5вЂ“7 kun | **Priority:** SHOULD-HAVE

---

### P3-T1 вЂ” Saqlangan Manzillar (Saved Addresses) рџџЎ
> **Murakkablik:** Medium | **Dependency:** P2-T1
> **Branch:** `feat/saved-addresses`
> **Commit:** `feat: add saved addresses functionality`

#### Subtasklar
- [x] `addresses` jadval (migration): `id, user_id, label, address_text, latitude, longitude, is_default`
- [x] `AddressRepository` вЂ” CRUD
- [x] `GET /addresses` вЂ” foydalanuvchi manzillari
- [x] `POST /addresses` вЂ” yangi manzil saqlash
- [x] `DELETE /addresses/{id}` вЂ” o'chirish
- [x] `PATCH /addresses/{id}/default` вЂ” default qilish
- [x] Max 5 ta manzil chegarasi
- [x] `frontend/app.js` вЂ” saqlangan manzillar section
- [x] Birinchi manzil auto default

#### Manual Testing
- [x] Manzil saqlanadi
- [x] Keyingi buyurtmada tanlanadi
- [x] 6-chi manzil в†’ xato

---

### P3-T2 вЂ” Qayta Buyurtma (Reorder) рџџЎ
> **Murakkablik:** Easy | **Dependency:** P2-T1
> **Branch:** `feat/reorder`
> **Commit:** `feat: add reorder from history`

#### Subtasklar
- [x] `POST /orders/{id}/reorder` endpoint
- [x] Eski order itemlardan cart yaratish (`CartService.from_order()`)
- [x] Mavjud bo'lmagan mahsulot в†’ skip + xabar
- [x] Bot buyurtmalar tarixida "рџ”Ѓ Qayta buyurtma" tugmasi
- [x] WebApp ga o'tish cart to'ldirilgan holda

#### Manual Testing
- [x] Eski buyurtmadan "рџ”Ѓ" bosiladi
- [x] WebApp ochiladi, cart to'ldirilgan
- [x] O'chirilgan mahsulot skip bo'ladi

---

### P3-T3 вЂ” i18n Centralizatsiya рџџў
> **Murakkablik:** Medium | **Dependency:** P0-T1
> **Branch:** `refactor/i18n`
> **Commit:** `refactor: centralize all text strings in locale files`
> **Hozirgi holat:** `utils/texts.py` mavjud вЂ” lekin to'liq emas, ba'zi matnlar handler da

#### Subtasklar
- [x] `utils/texts.py` вЂ” mavjud (to'liq emas)
- [x] `bot/locales/uz.json` вЂ” barcha uz matnlar
- [x] `bot/locales/ru.json` вЂ” barcha ru matnlar
- [x] `bot/locales/en.json` вЂ” barcha en matnlar
- [x] `utils/i18n.py` вЂ” `get_text(key, lang)` funksiya
- [x] Barcha hardcoded matnlar handler larda в†’ locale faylga
- [x] `user.language` DB da saqlanadi
- [x] Har handler da `lang = await get_user_lang(user_id)` chaqirish

#### Manual Testing
- [x] `/start` uz tilida ishlaydi
- [x] `/language` ru ga o'giradi вЂ” hamma joy ruscha
- [x] Yangi matn qo'shish faqat JSON faylda

---

## PHASE 4 вЂ” Admin Panel
> **Maqsad:** Admin boshqaruvini kengaytirish
> **Taxminiy vaqt:** 5вЂ“7 kun | **Priority:** MUST-HAVE

---

### P4-T1 вЂ” Admin Telegram Panel yaxshilash рџџЎ
> **Murakkablik:** Hard | **Dependency:** P2-T1
> **Branch:** `feat/admin-panel-enhanced`
> **Commit:** `feat: enhance admin bot panel with full order management`
> **Hozirgi holat:** Admin status o'zgartira oladi, yangi buyurtma xabari bor

#### Subtasklar
- [x] Admin status o'zgartirish вЂ” mavjud
- [x] Yangi buyurtma notification вЂ” mavjud
- [ ] `bot/middlewares/admin_check.py` вЂ” `ADMIN_IDS` filter
- [ ] `/admin_orders` вЂ” pending buyurtmalar ro'yxati (inline keyboard)
- [ ] Buyurtma detail view вЂ” user, manzil, mahsulotlar, summa
- [ ] Payment method ko'rish (рџ’і Click / рџ’і Payme / рџ’µ Naqd)
- [ ] `/admin_stats` вЂ” bugungi buyurtmalar soni + tushum
- [ ] Admin `/admin_help` вЂ” barcha buyruqlar ro'yxati
- [ ] Faqat ADMIN_IDS da bo'lganlar panel ishlatadi

#### Manual Testing
- [ ] Admin `/admin_orders` в†’ pending ro'yxat
- [ ] Buyurtma bosilsa detail ko'rinadi
- [ ] Noadmin user `admin_orders` yozsa "ruxsat yo'q"
- [ ] `/admin_stats` в†’ bugungi statistika

---

### P4-T2 вЂ” Admin Web Panel (FastAPI + Jinja2) рџ”ґ
> **Murakkablik:** Hard | **Dependency:** P1-T2
> **Branch:** `feat/web-admin`
> **Commit:** `feat: add web admin panel with jinja2 templates`

#### Subtasklar
- [ ] `pip install jinja2 python-multipart`
- [ ] `admin/` papka + `admin/templates/`
- [ ] `GET /admin` вЂ” login sahifa
- [ ] `GET /admin/orders` вЂ” barcha buyurtmalar (filter: status, sana)
- [ ] `GET /admin/products` вЂ” mahsulot CRUD
- [ ] `GET /admin/categories` вЂ” kategoriya CRUD
- [ ] `GET /admin/users` вЂ” foydalanuvchilar ro'yxati
- [ ] Admin session yoki token auth
- [ ] Buyurtma export CSV

#### Manual Testing
- [ ] `/admin` в†’ login ko'rinadi
- [ ] Login в†’ buyurtmalar ko'rinadi
- [ ] Noadmin login в†’ redirect

---

## PHASE 5 вЂ” Growth Features
> **Maqsad:** O'sish mexanizmlari qo'shish
> **Taxminiy vaqt:** 7вЂ“10 kun | **Priority:** SHOULD-HAVE

---

### P5-T1 вЂ” Promo Kod Tizimi рџ”ґ
> **Murakkablik:** Medium | **Dependency:** P2-T1
> **Branch:** `feat/promo-codes`
> **Commit:** `feat: implement promo code system`

#### Subtasklar
- [ ] `promo_codes` jadval: `id, code(UNIQUE), type, value, min_order_amount, max_uses, used_count, expires_at, is_active`
- [ ] `promo_code_uses` jadval: `UNIQUE(promo_code_id, user_id)` вЂ” bir marta ishlatish
- [ ] `POST /promo/validate` вЂ” kod + cart_amount в†’ chegirma
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
- [ ] To'g'ri kod в†’ chegirma hisoblanadi
- [ ] Muddati o'tgan kod в†’ xato
- [ ] Ikki marta ishlatish в†’ xato
- [ ] Noto'g'ri kod в†’ xato

---

### P5-T2 вЂ” Referral Tizimi рџ”ґ
> **Murakkablik:** Medium | **Dependency:** P2-T1
> **Branch:** `feat/referral-system`
> **Commit:** `feat: implement referral system with bonus`

#### Subtasklar
- [ ] `users` jadvalga: `referral_code(UNIQUE)`, `bonus_balance` field
- [ ] `referrals` jadval: `referrer_id, referred_id(UNIQUE), bonus_given, bonus_amount, created_at`
- [ ] Ro'yxatdan o'tishda `referral_code` auto generate (UUID short)
- [ ] `/start?ref=CODE` вЂ” referral link orqali onboarding
- [ ] `onboarding.py` da `deep_link` parse qilish
- [ ] Taklif qilingan birinchi buyurtma в†’ referrer ga bonus
- [ ] `GET /referral/info` вЂ” o'z referral linki va statistika
- [ ] Bonus `users.bonus_balance` ga qo'shiladi
- [ ] Checkout da bonus ishlatish imkoni

#### Manual Testing
- [ ] `/start?ref=ABC123` в†’ referral saqlanadi
- [ ] Birinchi buyurtma в†’ referrer bonus oladi
- [ ] `/referral/info` в†’ to'g'ri statistika

---

## PHASE 6 вЂ” Testing
> **Maqsad:** Ishonchlilik va xavfsizlikni ta'minlash
> **Taxminiy vaqt:** 5вЂ“7 kun | **Priority:** MUST-HAVE before launch

---

### P6-T1 вЂ” Unit Tests рџ”ґ
> **Murakkablik:** Medium | **Dependency:** P1-T2
> **Branch:** `feat/unit-tests`
> **Commit:** `test: add unit tests for services`

#### Subtasklar
- [ ] `pip install pytest pytest-asyncio pytest-mock`
- [ ] `tests/conftest.py` вЂ” test DB (SQLite in-memory), fixtures
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
- [ ] `pytest tests/unit/ -v` вЂ” barcha o'tadi
- [ ] `pytest --cov=backend/services` вЂ” coverage ko'rinadi

---

### P6-T2 вЂ” API Tests рџ”ґ
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
- [ ] `pytest tests/api/ -v` вЂ” barcha o'tadi
- [ ] `pytest --cov=backend` вЂ” 60%+ coverage

---

### P6-T3 вЂ” Payment Tests (Sandbox) рџ”ґ
> **Murakkablik:** Hard | **Dependency:** P6-T2
> **Branch:** `test/payment-sandbox`
> **Commit:** `test: verify payment flows with sandbox`

#### Subtasklar
- [ ] Click sandbox test merchant olish
- [ ] Payme test merchant olish (test.paycom.uz)
- [ ] End-to-end: buyurtma в†’ Click to'lov в†’ status o'zgarish
- [ ] End-to-end: buyurtma в†’ Payme to'lov в†’ status o'zgarish
- [ ] To'lov muvaffaqiyatsiz в†’ order holati tekshirish
- [ ] Ikki marta callback в†’ idempotency tekshirish

#### Manual Testing
- [ ] Click sandbox: to'lov muvaffaqiyatli в†’ order CONFIRMED
- [ ] Payme sandbox: to'lov muvaffaqiyatli в†’ order CONFIRMED
- [ ] Ikki marta `/click/complete` в†’ ikkinchisi 200 (idempotent)

---

[в†ђ README](./README.md) | [Keyingi: Sprint Planning в†’](./03_sprint_planning.md)

# 04 — Implementation Order (VS Code)

> **Maqsad:** VS Code da qaysi fayldan boshlash, qaysi tartibda ishlash — aniq ketma-ketlik

---

## 4.1 Qaysi Fayldan Boshlash Kerak

> Mantiq: har keyingi fayl oldingi fayl tayyor bo'lgandan keyin yoziladi.

```
Boshlash tartibi:
1.  config/settings.py          ← barcha modul buni import qiladi
2.  database/models.py          ← hamma narsa DB modelga bog'liq
3.  migrations/                 ← DB tayyor bo'lsin (alembic)
4.  backend/repositories/       ← DB dan oldin service bo'lmaydi
5.  backend/schemas/            ← API dan oldin schema kerak
6.  backend/services/           ← repo tayyor bo'lsa service
7.  backend/routers/            ← service tayyor bo'lsa router
8.  bot/middlewares/            ← bot xavfsizligi
9.  bot/keyboards/              ← handler dan oldin keyboard
10. bot/handlers/               ← backend API ishlayotganda
11. frontend/app.js             ← API endpoint lar tayyor bo'lganda
12. tests/                      ← har modul yozilgandan keyin
```

---

## 4.2 Birinchi 10 ta Fayl (VS Code da ochish tartibi)

### Step 1: `config/settings.py`
```bash
# Terminal
mkdir -p config && touch config/__init__.py config/settings.py
```

```python
# config/settings.py
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Bot
    BOT_TOKEN: str
    WEB_APP_URL: str
    ADMIN_IDS: List[int] = []
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./food_delivery.db"
    
    # Click
    CLICK_MERCHANT_ID: str = ""
    CLICK_SERVICE_ID: str = ""
    CLICK_SECRET_KEY: str = ""
    
    # Payme
    PAYME_MERCHANT_ID: str = ""
    PAYME_SECRET_KEY: str = ""
    
    # App
    SECRET_KEY: str = "changeme"
    ENVIRONMENT: str = "development"
    SENTRY_DSN: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()
```

**Tekshirish:** `python -c "from config.settings import settings; print('OK')"`

---

### Step 2: `database/models.py` — yetishmayotgan model lar qo'shish

```python
# database/models.py ga qo'shish kerak bo'lgan:
import enum

class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PREPARING = "PREPARING"
    DELIVERING = "DELIVERING"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

class PaymentMethod(str, enum.Enum):
    CLICK = "CLICK"
    PAYME = "PAYME"
    CASH = "CASH"

class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    AWAITING_CASH = "AWAITING_CASH"

# Yangi jadvallar qo'shish:
class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    old_status = Column(String, nullable=True)
    new_status = Column(String, nullable=False)
    changed_by = Column(String)  # "admin" yoki user_id
    changed_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(String, nullable=True)

class Address(Base):
    __tablename__ = "addresses"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    label = Column(String)  # "Uy", "Ish", etc.
    address_text = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class PromoCode(Base):
    __tablename__ = "promo_codes"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    type = Column(String)  # "percent" yoki "fixed"
    value = Column(Float, nullable=False)
    min_order_amount = Column(Integer, default=0)
    max_uses = Column(Integer, default=1)
    used_count = Column(Integer, default=0)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
```

---

### Step 3: `migrations/` — Alembic setup

```bash
# Terminal
pip install alembic aiosqlite
alembic init migrations
```

```python
# migrations/env.py ga o'zgartirish
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from config.settings import settings
from database.models import Base

def run_migrations_offline():
    url = settings.DATABASE_URL
    context.configure(url=url, target_metadata=Base.metadata, ...)

# migrations/alembic.ini
# sqlalchemy.url = — bu bo'sh qolsin, env.py dan o'qiladi
```

```bash
# Birinchi migration
alembic revision --autogenerate -m "initial_tables"
alembic upgrade head
```

---

### Step 4: `backend/repositories/` — yaratish

```python
# backend/repositories/base.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import TypeVar, Generic, Type, Optional, List

T = TypeVar("T")

class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model
    
    async def get(self, id: int) -> Optional[T]:
        return await self.session.get(self.model, id)
    
    async def get_all(self) -> List[T]:
        result = await self.session.execute(select(self.model))
        return result.scalars().all()
    
    async def create(self, **kwargs) -> T:
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
    
    async def delete(self, id: int) -> bool:
        obj = await self.get(id)
        if obj:
            await self.session.delete(obj)
            await self.session.commit()
            return True
        return False
```

---

### Step 5: `backend/services/order_service.py`

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

class OrderService:
    def __init__(self, order_repo, notification_service):
        self.order_repo = order_repo
        self.notification = notification_service
    
    async def create_order(self, user_id: int, data: dict) -> dict:
        # Validate
        if data.get("total", 0) < 10_000:
            raise ValueError("Minimum buyurtma 10 000 so'm")
        
        # Create
        order = await self.order_repo.create(user_id=user_id, **data)
        
        # Notify admin
        await self.notification.notify_admin(order["id"])
        
        return order
    
    async def update_status(self, order_id: int, new_status: str, changed_by: str):
        order = await self.order_repo.get(order_id)
        if not order:
            raise ValueError("Buyurtma topilmadi")
        
        allowed = VALID_TRANSITIONS.get(order["status"], [])
        if new_status not in allowed:
            raise ValueError(f"{order['status']} → {new_status} mumkin emas")
        
        updated = await self.order_repo.update_status(order_id, new_status)
        await self.notification.notify_status_change(order_id, new_status)
        return updated
```

---

### Step 6: `backend/routers/orders.py` — `backend/main.py` dan ko'chirish

```python
# backend/routers/orders.py
from fastapi import APIRouter, Depends, HTTPException
from backend.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/")
async def create_order(data: dict, service: OrderService = Depends()):
    try:
        return await service.create_order(data["user_id"], data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{order_id}")
async def get_order(order_id: int, service: OrderService = Depends()):
    order = await service.order_repo.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    return order
```

---

## 4.3 Bug Chiqishi Ehtimoli Ko'p Joylar

| Fayl | Risk | Muammo | Yechim |
|------|------|--------|--------|
| `bot/handlers/webapp.py` | WebApp → Backend sync | initData expire bo'lishi | initData refresh logikasi |
| `backend/main.py:371` | Click callback | HMAC sign xatosi | Unit test yozish |
| `migrations/env.py` | Async session | sync engine kerak | `run_sync` pattern |
| `bot/main.py` | Webhook vs polling | Ikkalasi bir vaqtda | Faqat bittasi |
| `backend/main.py:267` | Concurrent orders | Race condition | DB constraint |
| `frontend/app.js:27` | Hardcoded URL | Render URL o'zgarsa | `.env` dan o'qish |

---

## 4.4 Database Migration Kerak Bo'lgan Joylar

```bash
# Sprint 1 migrations
alembic revision --autogenerate -m "initial_tables"
alembic upgrade head

# Sprint 2 migrations
alembic revision --autogenerate -m "add_order_status_history"
alembic revision --autogenerate -m "add_payment_method_field"
alembic upgrade head

# Sprint 3 migrations
alembic revision --autogenerate -m "add_addresses_table"
alembic revision --autogenerate -m "add_promo_codes_table"
alembic revision --autogenerate -m "add_referral_fields"
alembic upgrade head
```

---

## 4.5 Service Layerga Ajratish Kerak Bo'lgan Funksiyalar

> `backend/main.py` dan service layerga ko'chirish:

```python
# backend/main.py da bor, servicega ko'chirish kerak:

# → backend/services/order_service.py
create_order()          # line ~267
update_order_status()   # line ~454

# → backend/services/payment_service.py  
generate_click_url()    # line ~335
generate_payme_url()    # line ~335
handle_click_callback() # line ~371
handle_payme_rpc()      # (qo'shish kerak)

# → backend/services/notification_service.py
notify_user()           # admin xabar yuborish logikasi
notify_admin()          # yangi buyurtma adminga

# → backend/services/cart_service.py
calculate_total()       # line ~247 (bootstrap da)
validate_cart_items()   # (qo'shish kerak)
```

---

## 4.6 Reusable Qilish Kerak Bo'lgan Kodlar

```python
# utils/formatters.py
def format_price(amount: int) -> str:
    """50000 → '50 000 so'm'"""
    return f"{amount:,} so'm".replace(",", " ")

def format_phone(phone: str) -> str:
    """O'zbek raqamni +998 formatga normalize"""
    phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if phone.startswith("8") and len(phone) == 11:
        phone = "+998" + phone[1:]
    elif not phone.startswith("+"):
        phone = "+998" + phone
    return phone

# utils/keyboards.py
def main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Asosiy menyu keyboard — barcha handler da bir xil"""
    ...

def order_action_keyboard(order_id: int, status: str) -> InlineKeyboardMarkup:
    """Admin order tugmalari — status ga qarab ko'rsatish"""
    ...

# utils/pagination.py
def paginate(query_result: list, page: int, limit: int = 10) -> dict:
    """Umumiy pagination helper"""
    total = len(query_result)
    start = (page - 1) * limit
    end = start + limit
    return {
        "items": query_result[start:end],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }
```

---

## 4.7 `.env` ga O'tkazish Kerak Bo'lgan Narsalar

### Hozir Hardcoded Bo'lishi Mumkin Bo'lgan Joylar

```bash
# VS Code da qidirish:
Ctrl+Shift+F → "http://localhost"       # dev URL
Ctrl+Shift+F → "https://telegram-bot"  # render URL hardcoded?  
Ctrl+Shift+F → "BOT_TOKEN"             # token hardcoded?
Ctrl+Shift+F → "sqlite:///"            # DB path hardcoded?
Ctrl+Shift+F → "CLICK_"               # payment key hardcoded?
Ctrl+Shift+F → "PAYME_"               # payment key hardcoded?
```

### Tekshirish Ro'yxati
- [ ] `frontend/index.html:14-15` — `API_BASE_URL` hardcoded → `.env` yoki build time inject
- [ ] `frontend/app.js:27` — `API_BASE_URL` → dynamic (window.API_BASE_URL yoki .env)
- [ ] `bot/main.py` — `BOT_TOKEN` → `settings.BOT_TOKEN`
- [ ] `bot/.env:2` — `WEB_APP_URL` → `settings.WEB_APP_URL`
- [ ] `backend/main.py` — `CLICK_*` kalitlar → `settings.CLICK_*`
- [ ] `backend/main.py` — `PAYME_*` kalitlar → `settings.PAYME_*`
- [ ] `backend/main.py` — `ADMIN_IDS` → `settings.ADMIN_IDS`

---

## 4.8 Frontend API URL Muammosi

```javascript
// frontend/index.html:14-15 — MUAMMO
const API_BASE_URL = "https://telegram-bot-1-8a3a.onrender.com";

// YECHIM 1: Backend dan inject qilish
// backend/main.py da frontend serve qilganda:
@app.get("/")
async def serve_frontend():
    # HTML ni o'qib, API_BASE_URL ni o'zgartirish
    content = open("frontend/index.html").read()
    content = content.replace(
        "{{API_BASE_URL}}", 
        settings.WEB_APP_URL
    )
    return HTMLResponse(content)

// YECHIM 2: JavaScript da relative URL
// app.js:27
const API_BASE_URL = window.location.origin;  // frontend va backend bir domain da
```

---

[← Sprint Planning](./03_sprint_planning.md) | [Keyingi: Business Rules →](./05_business_rules.md)

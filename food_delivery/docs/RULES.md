# Loyiha Qoidalari

## Kod yozish qoidalari

### Mutlaq qoidalar (buzilmaydi)

1. **Barcha DB operatsiyalar async** — `async def`, `await` kalit so'zlari shart
2. **Business logic faqat services/** — endpoint ichida hisoblash, qaror qabul qilish YO'Q
3. **DB so'rovlari faqat repositories/** — service ichida to'g'ridan-to'g'ri DB YO'Q
4. **Config faqat .env dan** — hardcode qiymatlari YO'Q (token, URL, kalit)
5. **Barcha funksiyalar type hint bilan** — `def foo(x: int) -> str:`
6. **Pydantic v2** — barcha request/response sxemalar uchun

### Import tartibi

```python
# 1. Standard library
import os
from datetime import datetime

# 2. Third party
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

# 3. Local
from app.core.config import settings
from app.models.user import User
```

### Naming konvensiyalari

| Narsa | Format | Misol |
|-------|--------|-------|
| Fayl | snake_case | `cart_service.py` |
| Sinf | PascalCase | `CartService` |
| Funksiya | snake_case | `get_cart_items()` |
| Konstanta | UPPER_SNAKE | `MAX_CART_ITEMS = 50` |
| DB ustun | snake_case | `created_at` |
| API endpoint | kebab-case | `/cart-items` |

### Exception qoidalari

```python
# NOTO'G'RI — exception har joyda
async def get_user(user_id: int):
    try:
        user = await db.get(User, user_id)
    except Exception as e:
        logger.error(e)
        raise HTTPException(400, str(e))

# TO'G'RI — custom exception, middleware handle qiladi
async def get_user(user_id: int):
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise UserNotFoundError(user_id)
    return user
```

## Xavfsizlik qoidalari

- [ ] initData HMAC-SHA256 bilan verify qilinadi
- [ ] JWT token expire: 7 kun
- [ ] Barcha admin routelar `is_admin` tekshiradi
- [ ] Rate limit: auth 5/min, public 60/min
- [ ] Checkout da narx DB dan qayta tekshiriladi
- [ ] Order da idempotency key saqlanadi
- [ ] SQL injection: faqat ORM parametrlar
- [ ] Input sanitization: Pydantic validator

## Git qoidalari

### Branch nomlash

```
feature/cart-redis-sync
bugfix/checkout-price-verify
hotfix/bot-start-crash
```

### Commit format

```
feat: add Redis cart sync
fix: checkout price verification
docs: update API docs
test: add cart service tests
refactor: move business logic to service
```

## Frontend qoidalari

- Telegram WebApp SDK barcha sahifalarda ulanadi
- Haptic feedback barcha tugmalarda: `Telegram.WebApp.HapticFeedback.impactOccurred('light')`
- Tema: faqat Telegram CSS variables ishlatiladi
- Har ekranda loading skeleton bo'ladi
- Har ekranda empty state bo'ladi
- Har ekranda error state bo'ladi
- Bottom navbar sticky, har vaqt ko'rinadi
- Mobile-first, 375px dan boshlab test qilinadi

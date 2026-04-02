# 🍔 FoodFlow / FoodExpress — Telegram Food Delivery Bot
## Production Roadmap — Uzbekistan Market

> **Bot haqida:** Ovqat yetkazib berish uchun Telegram bot. Foydalanuvchini ro'yxatdan o'tkazadi, WebApp orqali menyu ko'rsatadi, savatcha yuritadi, Click/Payme to'loviga yo'naltiradi, admin orqali buyurtmalarni boshqaradi.
>
> **Stack:** Telegram Bot (aiogram) + Telegram WebApp + FastAPI backend (Render) + SQLite/PostgreSQL
>
> **Brend:** `FoodExpress` (utils/texts.py) / `FoodFlow` (frontend)

---

## 📁 Roadmap Fayllar

| Fayl | Mavzu | Holat |
|------|-------|-------|
| [01_project_audit.md](./01_project_audit.md) | Loyiha audit — kuchli/zaif tomonlar | ✅ |
| [02_execution_board.md](./02_execution_board.md) | Developer Execution Board — task/subtask | ✅ |
| [03_sprint_planning.md](./03_sprint_planning.md) | Sprint 1–4 planning | ✅ |
| [04_implementation_order.md](./04_implementation_order.md) | VS Code step-by-step implementatsiya | ✅ |
| [05_business_rules.md](./05_business_rules.md) | Business / Technical / Security qoidalar | ✅ |
| [06_database_roadmap.md](./06_database_roadmap.md) | Database jadvallar, fieldlar, migration | ✅ |
| [07_api_roadmap.md](./07_api_roadmap.md) | FastAPI endpoint lar to'liq ro'yxat | ✅ |
| [08_deployment_security.md](./08_deployment_security.md) | Deployment va Security checklist | ✅ |
| [09_timeline.md](./09_timeline.md) | 30/60/90 kunlik reja | ✅ |
| [10_mvp_checklist.md](./10_mvp_checklist.md) | MVP Launch checklist | ✅ |

---

## 🟢 Hozir Ishlaydigan Funksiyalar

```
✅ /start onboarding (til, ism, telefon, shahar)
✅ 3 til: o'zbek, rus, ingliz
✅ Asosiy menyu (Buyurtma berish, Tarix, Til o'zgartirish)
✅ WebApp ochish (Buyurtma berish tugmasi)
✅ WebApp: mahsulotlar va kategoriyalar
✅ WebApp: savatchaga qo'shish / sonini o'zgartirish
✅ Manzil: qo'lda yozish + geolokatsiya
✅ Buyurtma yaratish
✅ Click to'loviga yo'naltirish
✅ Payme to'loviga yo'naltirish
✅ Buyurtmalar tarixi
✅ Buyurtma holati xabarlari (foydalanuvchiga)
✅ Admin: yangi buyurtmalarni ko'rish
✅ Admin: status o'zgartirish (6 holat)
✅ Backend API (FastAPI, Render da ishlaydi)
✅ Frontend fayllar backend orqali serve qilinadi
```

## 🔴 Hali Yo'q (Kerak Bo'lgan)

```
❌ Service layer (business logic handler da)
❌ Repository pattern (DB query scattered)
❌ Alembic migration
❌ Global error handling
❌ Logging (file rotation)
❌ Cash to'lov
❌ Saqlangan manzillar
❌ Qayta buyurtma (reorder)
❌ Promo kod tizimi
❌ Referral tizimi
❌ Test (unit, integration, API)
❌ Admin analytics
❌ Webhook mode (hozir polling)
❌ Production monitoring (Sentry)
```

---

## ⚡ Tezkor Boshlash

```bash
# 1. Hozirgi holatni tekshirish
python -m bot.main  # bot ishlayaptimy?
curl https://telegram-bot-1-8a3a.onrender.com/health  # backend ishlayaptimy?

# 2. Birinchi vazifa
# 02_execution_board.md → PHASE 0 → P0-T1 boshlang
```

---

## 📊 Progress Tracker

| Phase | Nom | Tasks | Done | Progress |
|-------|-----|-------|------|----------|
| P0 | Foundation & Code Quality | 5 | 0 | ░░░░░░░░░░ 0% |
| P1 | Core Backend Layering | 3 | 0 | ░░░░░░░░░░ 0% |
| P2 | Order Flow & Payment | 4 | 0 | ░░░░░░░░░░ 0% |
| P3 | UX Improvements | 3 | 0 | ░░░░░░░░░░ 0% |
| P4 | Admin Panel | 2 | 0 | ░░░░░░░░░░ 0% |
| P5 | Growth Features | 2 | 0 | ░░░░░░░░░░ 0% |
| P6 | Testing | 3 | 0 | ░░░░░░░░░░ 0% |

> **Eslatma:** `- [x]` qilib belgilash uchun VS Code da fayl ichida checkbox ni bosing yoki `[ ]` ni `[x]` ga o'zgartiring.

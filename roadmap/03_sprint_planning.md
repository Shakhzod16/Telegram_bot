# 03 — Sprint Planning

> **Format:** 2 haftalik sprint. Bitta developer uchun realistik.
> **Eslatma:** Sprint boshida `[ ]` → sprint oxirida `[x]` qiling

---

## Sprint 1 — Foundation & Stable Core
> **Sana:** 1–14 kun | **Maqsad:** Loyihani mustahkam poydevorga qo'yish

### 🎯 Sprint Goal
> Loyiha strukturasi tartibli, config .env da, log yozilmoqda, DB migration ishlaydi, layered architecture qo'llanilgan — va barcha mavjud funksiyalar hali ham ishlaydi.

### 📋 Sprint Tasks

#### Hafta 1
- [ ] **P0-T1** Loyiha strukturasini qayta tartiblashtirish *(Medium, 2 kun)*
- [ ] **P0-T2** Settings va .env management *(Easy, 1 kun)*
- [ ] **P0-T3** Logging sozlash *(Easy, 1 kun)*
- [ ] **P0-T4** Global error handling *(Medium, 1 kun)*

#### Hafta 2
- [ ] **P0-T5** Database migration (Alembic) *(Medium, 1.5 kun)*
- [ ] **P1-T1** Repository pattern *(Hard, 2 kun)*
- [ ] **P1-T2** Service layer *(Hard, 2 kun)*
- [ ] **P1-T3** Pydantic schemas *(Medium, 1.5 kun)*

### 📦 Deliverables
- [ ] Toza loyiha strukturasi (routers/, services/, repositories/, schemas/)
- [ ] Barcha config `.env` da — hech qanday hardcoded secret yo'q
- [ ] `logs/app.log` yozilmoqda
- [ ] Bot crash bo'lmaydi (error handling ishlaydi)
- [ ] `alembic upgrade head` xatosiz
- [ ] Layered architecture: Router → Service → Repository

### 🧪 Testing
- [ ] Bot `/start` ishlaydi
- [ ] FastAPI `/docs` ochiladi
- [ ] `curl https://telegram-bot-1-8a3a.onrender.com/health` → 200
- [ ] `pytest` xatosiz ishga tushadi

### ⚠️ Risklar
| Risk | Ehtimollik | Yechim |
|------|-----------|--------|
| Import chalkashligi | Yuqori | Har import dan keyin test |
| Circular dependency | O'rta | Dependency injection ishlatish |
| Async session muammosi | O'rta | `AsyncSession` to'g'ri inject |
| Alembic migration xatosi | O'rta | `sync` engine use qilish |

### ✅ Definition of Done
- [ ] Barcha mavjud funksiyalar ishlaydi (regression yo'q)
- [ ] Hech qanday hardcoded secret yo'q
- [ ] `alembic upgrade head` xatosiz
- [ ] `pytest` xatosiz (0 test ham bo'lsa)
- [ ] `git log --oneline` — har task uchun commit bor

---

## Sprint 2 — Order Flow & Payments
> **Sana:** 15–28 kun | **Maqsad:** To'lov va buyurtma flow ni production-ready qilish

### 🎯 Sprint Goal
> To'lov signature verify ishlaydi, order status machine to'liq, cash payment bor, admin panel kuchaytirilgan — real foydalanuvchilar bilan test qilish mumkin.

### 📋 Sprint Tasks

#### Hafta 3
- [ ] **P2-T1** To'liq Order Status State Machine *(Hard, 2 kun)*
- [ ] **P2-T2** Click signature verify *(Hard, 2 kun)*
- [ ] **P2-T3** Payme JSONRPC *(Hard, 2 kun)*

#### Hafta 4
- [ ] **P2-T4** Cash payment *(Easy, 1 kun)*
- [ ] **P4-T1** Admin Telegram panel yaxshilash *(Hard, 2 kun)*
- [ ] Bug fix va integration test *(2 kun)*

### 📦 Deliverables
- [ ] Order status machine: `PENDING → CONFIRMED → PREPARING → DELIVERING → DELIVERED`
- [ ] Click sandbox to'lov end-to-end ishlaydi
- [ ] Payme sandbox to'lov end-to-end ishlaydi
- [ ] Cash payment option
- [ ] Admin `/admin_orders`, `/admin_stats` ishlaydi
- [ ] `order_status_history` jadval to'ldirilmoqda

### 🧪 Testing
- [ ] Click sandbox: to'lov → order CONFIRMED → user xabar
- [ ] Payme sandbox: to'lov → order CONFIRMED → user xabar
- [ ] Cash: buyurtma → redirect yo'q → admin ko'radi
- [ ] Noto'g'ri signature → 400
- [ ] DELIVERED → PENDING → 400

### ⚠️ Risklar
| Risk | Ehtimollik | Yechim |
|------|-----------|--------|
| Click API o'zgarishi | Past | Docs tekshirish |
| HMAC sign xatosi | Yuqori | Unit test yozish |
| Payme JSONRPC spec | O'rta | Rasmiy docs o'qish |
| Async notification race | O'rta | Background task ishlatish |

### ✅ Definition of Done
- [ ] To'lov end-to-end sandbox da ishlaydi
- [ ] Admin buyurtma boshqaradi
- [ ] Barcha status transition test qilingan
- [ ] User har statusda xabar oladi
- [ ] `order_status_history` da yozuvlar bor
- [ ] Hech qanday unhandled exception yo'q

---

## Sprint 3 — UX & Growth Features
> **Sana:** 29–42 kun | **Maqsad:** Foydalanuvchi tajribasini yaxshilash + o'sish

### 🎯 Sprint Goal
> Saqlangan manzillar, reorder, centralized i18n, promo kod va referral tizimi — foydalanuvchi loyal bo'lishi uchun asos.

### 📋 Sprint Tasks

#### Hafta 5
- [ ] **P3-T1** Saqlangan manzillar *(Medium, 2 kun)*
- [ ] **P3-T2** Qayta buyurtma (Reorder) *(Easy, 1 kun)*
- [ ] **P3-T3** i18n centralizatsiya *(Medium, 2 kun)*

#### Hafta 6
- [ ] **P5-T1** Promo kod tizimi *(Medium, 3 kun)*
- [ ] **P5-T2** Referral tizimi *(Medium, 2 kun)*
- [ ] Bug fix *(2 kun)*

### 📦 Deliverables
- [ ] Manzil saqlash va keyingi buyurtmada tanlash
- [ ] "🔁 Qayta buyurtma" tugmasi tarixda
- [ ] Barcha til strings `bot/locales/` da
- [ ] Promo kod chegirma beradi
- [ ] Referral link + bonus tizimi

### 🧪 Testing
- [ ] Manzil saqlanadi → keyingi buyurtmada tanlash
- [ ] Reorder → cart to'ldirilgan holda WebApp ochiladi
- [ ] `WELCOME10` promo → 10% chegirma
- [ ] Do'stni taklif → birinchi buyurtmada bonus
- [ ] O'chirilgan mahsulot reorder da skip bo'ladi

### ⚠️ Risklar
| Risk | Ehtimollik | Yechim |
|------|-----------|--------|
| Promo race condition | O'rta | DB unique constraint |
| Referral circular | Past | `referred_id UNIQUE` |
| i18n refactor regression | O'rta | Har til alohida test |

### ✅ Definition of Done
- [ ] Saved address ishlaydi (max 5)
- [ ] Promo 10+ edge case ni o'tadi
- [ ] Referral bonus yaratiladi va ko'rinadi
- [ ] Barcha til strings locales da (handler da matn yo'q)
- [ ] Promo bir foydalanuvchi bir marta ishlatadi

---

## Sprint 4 — Testing, Deploy & Launch
> **Sana:** 43–56 kun | **Maqsad:** Production ga chiqish

### 🎯 Sprint Goal
> Testlar yozilgan, production server tayyor, webhook ishlaydi, monitoring bor, real foydalanuvchilar bilan 72 soat stable.

### 📋 Sprint Tasks

#### Hafta 7
- [ ] **P6-T1** Unit tests *(Medium, 2 kun)*
- [ ] **P6-T2** API tests *(Medium, 2 kun)*
- [ ] **P6-T3** Payment sandbox tests *(Hard, 1 kun)*

#### Hafta 8
- [ ] Deployment setup (VPS/Render, Nginx, SSL) *(2 kun)*
- [ ] Webhook mode sozlash *(1 kun)*
- [ ] Monitoring (Sentry) *(0.5 kun)*
- [ ] Backup script *(0.5 kun)*
- [ ] Soft launch *(1 kun)*
- [ ] Bug fix loop *(2 kun)*

### 📦 Deliverables
- [ ] 60%+ test coverage
- [ ] Production server (VPS yoki Render pro)
- [ ] HTTPS + SSL sertifikat
- [ ] Webhook ishlaydi (polling emas)
- [ ] Sentry error tracking
- [ ] Daily DB backup script
- [ ] Real foydalanuvchilar bilan 72 soat stable

### 🧪 Testing
- [ ] `pytest --cov=backend` → 60%+
- [ ] Bot webhook ishlaydi (`/getWebhookInfo` → URL bor)
- [ ] Production Click to'lov (kichik summa bilan test)
- [ ] Production Payme to'lov (kichik summa bilan test)
- [ ] 50 concurrent user load test (locust)

### ⚠️ Risklar
| Risk | Ehtimollik | Yechim |
|------|-----------|--------|
| Webhook SSL muammosi | O'rta | certbot + nginx config |
| Production payment fail | O'rta | Sandbox test + gradual rollout |
| Real traffic load | O'rta | Uvicorn workers + monitoring |
| Unknown edge case | Yuqori | User feedback loop |

### ✅ Definition of Done
- [ ] Bot production da ishlaydi
- [ ] Payment real pul bilan ishlaydi
- [ ] Admin panel ishlaydi
- [ ] 72 soat hech qanday crash yo'q
- [ ] Monitoring dashboard bor
- [ ] Error rate < 1%
- [ ] Backup har kecha ishga tushadi

---

## 📊 Sprint Velocity Tracker

| Sprint | Planned Tasks | Done | Velocity |
|--------|--------------|------|----------|
| Sprint 1 | 8 | 0 | — |
| Sprint 2 | 6 | 0 | — |
| Sprint 3 | 5 | 0 | — |
| Sprint 4 | 8 | 0 | — |

> Har sprint oxirida done task soni ni to'ldiring.

---

[← Execution Board](./02_execution_board.md) | [Keyingi: Implementation Order →](./04_implementation_order.md)

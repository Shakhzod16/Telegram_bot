# 01 — Project Audit

> **Oxirgi yangilanish:** 2026-03-28
> **Loyiha:** FoodFlow / FoodExpress Telegram Food Delivery Bot

---

## ✅ Kuchli Tomonlar

- [x] **Telegram-native** — UZda eng ko'p ishlatiladigan messenger orqali ishlaydi
- [x] **3 til** (uz/ru/en) — lokal bozor uchun to'g'ri qadam (`utils/texts.py`)
- [x] **WebApp integration** — native app shart emas, AppStore yo'q
- [x] **Click + Payme** — ikki asosiy payment gateway qamrab olingan
- [x] **Onboarding flow** — telefon va shahar olish to'g'ri ketma-ketlikda (`bot/handlers/onboarding.py`)
- [x] **Lokatsiya/manzil ikki xil** — qo'lda + GPS (`bot/handlers/webapp.py`)
- [x] **FastAPI backend** — production-ready, Render da ishlaydi
- [x] **Frontend backend tomonidan serve** — alohida hosting shart emas (`backend/main.py:232-242`)
- [x] **Admin order management** — 6 xil status boshqaruvi
- [x] **Order status notification** — foydalanuvchiga real-time xabar

---

## ❌ Zaif Tomonlar

- [ ] **Service layer yo'q** — business logic to'g'ridan handler ichida (`backend/main.py` — barcha logika bitta faylda)
- [ ] **Repository pattern yo'q** — DB query lar scattered holda
- [ ] **Error handling zaifligi** — user xato qilsa bot to'xtab qolishi mumkin
- [ ] **State management** — FSM ishlatilmayapti (aiogram FSM yo'q)
- [ ] **Cart WebApp sync** — WebApp ↔ backend sync muammosi (frontend `app.js:27` da hardcoded URL)
- [ ] **Test yo'q** — hech qanday unit yoki integration test
- [ ] **Logging minimal** — xato qayerdan kelganini bilish qiyin
- [ ] **Webhook o'rnatilmagan** — hozir polling mode (`backend/main.py` webhook handler bor lekin sozlanmagan)
- [ ] **Alembic yo'q** — database migration tool yo'q
- [ ] **Brend nomi chalkash** — `FoodExpress` (texts.py) vs `FoodFlow` (frontend) — bir xil bo'lishi kerak
- [ ] **Cash payment yo'q** — UZda katta segment naqd to'laydi
- [ ] **Promo/referral yo'q** — o'sish mexanizmi yo'q
- [ ] **Saqlangan manzillar yo'q** — har buyurtmada qaytadan kiritadi
- [ ] **Admin analytics yo'q** — faqat order ko'rish bor

---

## 🟡 Hozirgi MVP Holati

| Komponent | Fayl | Holat | Izoh |
|-----------|------|-------|------|
| Onboarding | `bot/handlers/onboarding.py` | ✅ Ishlaydi | To'liq |
| 3 til | `utils/texts.py` | ✅ Ishlaydi | Matnlar to'liq |
| Asosiy menyu | `bot/main.py` | ✅ Ishlaydi | OK |
| WebApp ochish | `bot/handlers/webapp.py` | ✅ Ishlaydi | URL `.env:2` da |
| Menu ko'rsatish | `frontend/app.js` | ✅ Ishlaydi | Kategoriya filter bor |
| Cart | `frontend/app.js:347,373,388` | ⚠️ Ishlaydi | Sync muammosi bor |
| Manzil (qo'lda) | `bot/handlers/webapp.py` | ✅ Ishlaydi | OK |
| Manzil (GPS) | `bot/handlers/webapp.py` | ✅ Ishlaydi | OK |
| Buyurtma yaratish | `backend/main.py:267` | ✅ Ishlaydi | Validation zaifligi |
| Click to'lov | `backend/main.py:335` | ✅ Ishlaydi | Sandbox tekshirilgan? |
| Payme to'lov | `backend/main.py:335` | ✅ Ishlaydi | Sandbox tekshirilgan? |
| To'lov callback | `backend/main.py:371` | ⚠️ Ishlaydi | Signature verify? |
| Order tarixi | `backend/main.py` | ✅ Ishlaydi | Pagination yo'q |
| Status notify | `backend/main.py:454` | ✅ Ishlaydi | OK |
| Admin orders | `backend/main.py:471` | ✅ Ishlaydi | Minimal |
| Bootstrap API | `backend/main.py:247` | ✅ Ishlaydi | initData auth |
| Testing | — | ❌ Yo'q | Kritik |
| Logging | — | ❌ Minimal | Yetarli emas |
| Error handling | — | ❌ Minimal | Xavfli |

---

## 🚨 Launch uchun Yetishmayotgan (Muhimlik tartibida)

```
KRITIK (launch blokeri):
  1. Global error handling — bot crash bo'lmasin
  2. Payment callback signature verify — soxta to'lov xavfi
  3. Webhook + SSL setup — polling production da yaxshi emas
  4. Order status to'liq flow tekshirish

MUHIM (launch oldidan):
  5. Cash payment — UZda zarur
  6. Logging — xatolarni kuzatish uchun
  7. Brend nomi birlashtirish — FoodFlow yoki FoodExpress?
  8. Admin panel yaxshilash — confirm/reject qulayroq

KERAKLI (post-launch):
  9. Saqlangan manzillar
  10. Reorder
  11. Promo kod
  12. Test yozish
```

---

## 🇺🇿 Uzbekistan Bozori uchun Moslashtirish

| Jihat | Hozirgi holat | Kerakli |
|-------|--------------|---------|
| Til | ✅ uz/ru/en | Default = uz bo'lsin |
| To'lov | ⚠️ Click + Payme | + Cash on delivery |
| Telefon | ✅ Olinmoqda | +998 formatga normalize |
| Narx | ✅ So'm da | 50 000 → "50 000 so'm" format |
| Yetkazib berish | ⚠️ Manzil olinmoqda | Zona/tuman filtri |
| Referral | ❌ Yo'q | Do'st taklif — kuchli kanal |
| Promo | ❌ Yo'q | Yangi foydalanuvchi uchun |
| Vaqt | ❌ Ko'rsatilmaydi | "30-45 daqiqa" ko'rsatish |

---

## 🗂️ Mavjud Fayl Strukturasi

```
├── bot/
│   ├── main.py                 ✅ ishlaydi
│   ├── handlers/
│   │   ├── onboarding.py       ✅ ishlaydi
│   │   └── webapp.py           ✅ ishlaydi
├── backend/
│   ├── main.py                 ✅ ishlaydi (barcha logika shu yerda)
│   └── models.py               ✅ ishlaydi
├── frontend/
│   ├── index.html              ✅ ishlaydi
│   ├── app.js                  ✅ ishlaydi
│   └── styles.css              ✅ ishlaydi
├── database/
│   └── models.py               ✅ ishlaydi
└── utils/
    └── texts.py                ✅ ishlaydi
```

**Yetishmayotgan papkalar:**
```
├── backend/routers/            ❌ yo'q
├── backend/services/           ❌ yo'q
├── backend/repositories/       ❌ yo'q
├── backend/schemas/            ❌ yo'q
├── config/                     ❌ yo'q
├── migrations/                 ❌ yo'q
└── tests/                      ❌ yo'q
```

---

[← README](./README.md) | [Keyingi: Execution Board →](./02_execution_board.md)

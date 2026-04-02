# 10 — MVP Launch Checklist

> **Maqsad:** Launch oldidan barcha kerakli narsalar tekshirilsin.
> **Muhim:** Har punktni real tekshirib `[x]` qiling, taxmin bilan emas.

---

## 🔴 KRITIK — Bu lar bo'lmasa launch YO'Q

### Bot
- [x] `/start` ga javob beradi
- [x] Onboarding to'liq (til → ism → telefon → shahar)
- [x] 3 tilda ishlaydi (uz/ru/en)
- [x] Asosiy menyu ishlaydi
- [ ] Bot crash bo'lmaydi (global error handler)

### WebApp
- [x] "Buyurtma berish" tugmasi WebApp ochadi
- [x] Mahsulotlar ko'rinadi
- [x] Kategoriya filtri ishlaydi
- [x] Cartga qo'shish/o'chirish ishlaydi
- [x] Manzil qo'lda kiritish ishlaydi
- [x] Manzil GPS orqali olish ishlaydi

### Buyurtma
- [x] Buyurtma yaratiladi
- [x] Buyurtma DB ga saqlanadi
- [x] Admin yangi buyurtma xabarini oladi

### To'lov
- [x] Click to'loviga yo'naltiradi
- [x] Payme to'loviga yo'naltiradi
- [ ] Click callback signature verify ishlaydi
- [ ] Payme JSONRPC to'liq ishlaydi
- [ ] Muvaffaqiyatli to'lov → order CONFIRMED
- [ ] To'lov muvaffaqiyatsiz → user xabar oladi
- [ ] Cash payment ishlaydi

### Order Status
- [x] Admin status o'zgartira oladi (6 holat)
- [x] Status o'zgarganda user xabar oladi
- [ ] Status transition validation (DELIVERED → PENDING bo'lmaydi)
- [ ] `order_status_history` yozilmoqda

### Admin
- [x] Admin yangi buyurtmani ko'radi
- [x] Admin status o'zgartiradi
- [ ] Faqat admin ID lar panel ishlatadi (middleware)
- [ ] Admin `/admin_stats` buyruqi ishlaydi

### Tarixi
- [x] Foydalanuvchi buyurtmalar tarixini ko'radi
- [ ] Tarixi pagination bilan ishlaydi

---

## 🟡 MUHIM — Launch uchun kerakli

### Texnik
- [ ] Global error handling bor (bot crash bo'lmaydi)
- [ ] Logging fayl rotation bilan ishlaydi
- [ ] Barcha config `.env` dan o'qiladi
- [ ] Hech qanday hardcoded secret kod ichida yo'q
- [ ] Database migration (Alembic) ishlaydi
- [ ] `.env` `.gitignore` da

### Xavfsizlik
- [ ] Webhook HTTPS bilan ishlaydi (yoki Render HTTPS)
- [ ] Bot webhook secret token o'rnatilgan
- [ ] WebApp initData HMAC verify ishlaydi
- [ ] Payment signature verify ishlaydi
- [ ] Rate limiting sozlangan

### UX
- [ ] Brend nomi bir xil (FoodFlow yoki FoodExpress — birini tanlang)
- [ ] Xato xabarlari 3 tilda
- [ ] Loading indicator WebApp da bor

---

## 🟢 KERAKLI — Tez orada qo'shiladi

> Launch dan keyin birinchi 2 haftada:

- [ ] Saqlangan manzillar
- [ ] Qayta buyurtma (reorder)
- [ ] Buyurtmalar tarixi pagination
- [ ] Admin analytics (kunlik tushum, buyurtmalar)
- [ ] Monitoring (Sentry)
- [ ] Backup script

---

## 📋 Launch Kungi Tekshiruv

### Backend
```bash
# 1. Backend ishlayaptimy?
curl https://telegram-bot-1-8a3a.onrender.com/docs
# → 200 OK

# 2. Health check
curl https://telegram-bot-1-8a3a.onrender.com/health
# → {"status": "ok"}

# 3. DB ulanish
alembic current
# → versiya ko'rinadi
```

- [ ] `/docs` ochiladi
- [ ] `/health` → 200
- [ ] DB migration versiyasi to'g'ri

### Bot
```bash
# Bot webhook holatini tekshirish
curl https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo
# → {"ok":true,"result":{"url":"https://...","has_custom_certificate":false,...}}
```

- [ ] Webhook URL o'rnatilgan
- [ ] `pending_update_count` ko'p emas
- [ ] Bot `/start` ga javob beradi

### Payment
```bash
# Click sandbox test
# Payme sandbox test
```

- [ ] Click sandbox to'lov ishlaydi
- [ ] Payme sandbox to'lov ishlaydi
- [ ] Real payment production credential o'rnatilgan

### Admin
- [ ] Admin ID lar `.env` da to'g'ri
- [ ] Admin yangi buyurtma xabar oladi
- [ ] Admin status o'zgartiradi

---

## 🚀 Soft Launch Protokol

```
1. Birinchi 10 foydalanuvchi (do'stlar, oila)
   → Xatolar yig'ing
   → Feedback yig'ing
   → 48 soat kuzating

2. Agar 48 soat stable bo'lsa → 50 foydalanuvchi
   → Real to'lov test (kichik summa)
   → Load monitoring

3. Agar 50 foydalanuvchi stable → Full launch
   → Marketing boshlash
   → Referral aktiv qilish
```

---

## Post-Launch Improvement Checklist

### 1-hafta ichida
- [ ] Critical bug fix lar
- [ ] User feedback asosida UX yaxshilash
- [ ] Error rate < 1% maqsad

### 2-hafta ichida
- [ ] Saqlangan manzillar qo'shish
- [ ] Reorder funksiyasi
- [ ] Admin analytics

### 1-oy ichida
- [ ] Promo kod tizimi
- [ ] Referral tizimi
- [ ] Unit + API testlar

### 2-oy ichida
- [ ] Performance optimization
- [ ] Load testing
- [ ] Backup va monitoring to'liq

---

## Launch Progress

| Kategoriya | Jami | Tayyor | % |
|-----------|------|--------|---|
| Kritik | 18 | 11 | 61% |
| Muhim | 13 | 0 | 0% |
| Kerakli | 6 | 0 | 0% |
| **Jami** | **37** | **11** | **30%** |

> Launch uchun: Kritik 100% + Muhim 80%+ = **tayyor**

---

[← Timeline](./09_timeline.md) | [← README](./README.md)

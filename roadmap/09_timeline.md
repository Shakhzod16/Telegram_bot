# 09 — 30 / 60 / 90 Kunlik Reja

---

## 30 Kunlik Reja — Foundation + Core

> **Maqsad:** Kod mustahkam, payment to'liq, admin ishlaydi, launch mumkin

### Hafta 1 (Kun 1–7)
- [ ] **P0-T1** Loyiha strukturasi qayta tartib (`refactor/project-structure`)
- [ ] **P0-T2** Settings / .env management (`feat/config-env`)
- [ ] **P0-T3** Logging (`feat/logging`)
- [ ] **P0-T4** Global error handling (`feat/error-handling`)

**Hafta 1 natijalari:**
- [ ] Bot crash bo'lmaydi
- [ ] Log yozilmoqda
- [ ] Config `.env` dan o'qiladi
- [ ] Hech qanday hardcoded secret yo'q

---

### Hafta 2 (Kun 8–14)
- [ ] **P0-T5** Alembic migration (`feat/alembic-migrations`)
- [ ] **P1-T1** Repository pattern (`refactor/repository-pattern`)
- [ ] **P1-T2** Service layer (`refactor/service-layer`)
- [ ] **P1-T3** Pydantic schemas (`feat/pydantic-schemas`)

**Hafta 2 natijalari:**
- [ ] DB migration ishlaydi
- [ ] Layered architecture bor
- [ ] API typed

---

### Hafta 3 (Kun 15–21)
- [ ] **P2-T1** Order status state machine (`feat/order-status-flow`)
- [ ] **P2-T2** Click signature verify (`feat/click-signature-verify`)
- [ ] **P2-T3** Payme JSONRPC (`feat/payme-payment`)

**Hafta 3 natijalari:**
- [ ] To'lov signature verify ishlaydi
- [ ] Status machine to'liq
- [ ] `order_status_history` to'ldirilmoqda

---

### Hafta 4 (Kun 22–30)
- [ ] **P2-T4** Cash payment (`feat/cash-payment`)
- [ ] **P4-T1** Admin panel yaxshilash (`feat/admin-panel-enhanced`)
- [ ] Bug fix + integration test

**Hafta 4 natijalari:**
- [ ] Cash payment ishlaydi
- [ ] Admin panel kuchaytirilgan
- [ ] Real foydalanuvchilar bilan test mumkin

### ✅ 30 kun oxirida:
```
✅ Bot barqaror ishlaydi
✅ Payment to'liq (Click + Payme + Cash)
✅ Order status machine ishlaydi
✅ Admin buyurtma boshqaradi
✅ Soft launch mumkin
```

---

## 60 Kunlik Reja — UX + Growth

> **Maqsad:** Foydalanuvchi loyal bo'lishi uchun feature lar + o'sish

### Hafta 5 (Kun 31–37)
- [ ] **P3-T1** Saqlangan manzillar (`feat/saved-addresses`)
- [ ] **P3-T2** Qayta buyurtma (`feat/reorder`)

**Natijalari:**
- [ ] Manzil saqlanadi
- [ ] 1 click bilan qayta buyurtma

---

### Hafta 6 (Kun 38–44)
- [ ] **P3-T3** i18n centralizatsiya (`refactor/i18n`)
- [ ] WebApp UI yaxshilash (loading, animatsiya, ux)
- [ ] Brend nomi birlashtirish (FoodFlow yoki FoodExpress)

**Natijalari:**
- [ ] Barcha til strings lokallashtirilgan
- [ ] WebApp professional ko'rinadi
- [ ] Brend nomi bir xil hamma yerda

---

### Hafta 7 (Kun 45–51)
- [ ] **P5-T1** Promo kod tizimi (`feat/promo-codes`)

**Natijalari:**
- [ ] Promo kod ishlaydi
- [ ] Admin kod yaratadi
- [ ] Chegirma to'g'ri hisoblanadi

---

### Hafta 8 (Kun 52–60)
- [ ] **P5-T2** Referral tizimi (`feat/referral-system`)
- [ ] Bug fix + analytics

**Natijalari:**
- [ ] Referral link ishlaydi
- [ ] Bonus beriladi
- [ ] O'sish mexanizmi bor

### ✅ 60 kun oxirida:
```
✅ Saqlangan manzillar
✅ Reorder
✅ Promo kod
✅ Referral
✅ Professional UX
✅ O'sish mexanizmi bor
```

---

## 90 Kunlik Reja — Launch + Scale

> **Maqsad:** Test, deploy, monitoring, haqiqiy foydalanuvchilar

### Hafta 9 (Kun 61–67)
- [ ] **P6-T1** Unit tests (`feat/unit-tests`)
- [ ] **P6-T2** API tests (`feat/api-tests`)
- [ ] **P6-T3** Payment sandbox tests

**Natijalari:**
- [ ] 60%+ coverage
- [ ] Barcha service test qilingan
- [ ] Payment flow test qilingan

---

### Hafta 10 (Kun 68–74)
- [ ] Deployment setup (VPS yoki Render pro)
- [ ] Nginx + SSL (VPS uchun) yoki Render pro sozlama
- [ ] Webhook mode sozlash
- [ ] PostgreSQL ga o'tish (agar SQLite ishlatilsa)
- [ ] Sentry monitoring

**Natijalari:**
- [ ] Production server tayyor
- [ ] Webhook ishlaydi
- [ ] Monitoring dashboard bor

---

### Hafta 11 (Kun 75–81)
- [ ] Backup script
- [ ] Load testing (locust bilan 50 concurrent user)
- [ ] Security audit (RULE-S1 dan S4 gacha tekshirish)
- [ ] **Soft launch** — 20–50 real foydalanuvchi

**Natijalari:**
- [ ] Real foydalanuvchilar bor
- [ ] Xatolar monitored
- [ ] Performance OK

---

### Hafta 12–13 (Kun 82–90)
- [ ] User feedback to'plash
- [ ] Critical bug fix
- [ ] UX yaxshilash (feedback asosida)
- [ ] Admin analytics dashboard
- [ ] **Full launch**

**Natijalari:**
- [ ] 100+ aktiv foydalanuvchi
- [ ] Error rate < 1%
- [ ] 72 soat stable

### ✅ 90 kun oxirida:
```
✅ Production da ishlaydi (webhook, SSL, monitoring)
✅ 60%+ test coverage
✅ Real to'lov ishlaydi
✅ 100+ foydalanuvchi
✅ Feedback asosida UX yaxshilangan
✅ O'sish mexanizmi (promo + referral)
```

---

## Kunlik Progress (Optional)

> Har kuni bu joyni to'ldiring

| Sana | Bajarilaganlar | Muammolar | Keyingi kun |
|------|---------------|-----------|-------------|
| | | | |
| | | | |
| | | | |

---

[← Deployment](./08_deployment_security.md) | [Keyingi: MVP Checklist →](./10_mvp_checklist.md)

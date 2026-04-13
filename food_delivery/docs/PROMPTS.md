# Cursor Promptlari To'plami

## Qanday ishlatiladi

1. Cursor ni oching
2. `Cmd+Shift+I` (Mac) yoki `Ctrl+Shift+I` (Windows) — Composer
3. Kerakli promptni toping
4. `[...]` qavslardagi joylarni o'zingizniki bilan almashtiring
5. Paste qilib Enter bosing

---

## ASOSIY PROMPTLAR

### P-001: Loyihani noldan yaratish

```
@docs/ARCHITECTURE.md @docs/RULES.md ni o'qib chiq.

food_delivery loyihasini noldan yarat. Quyidagi tartibda barcha fayllarni yoz:

1. docker-compose.yml
2. requirements.txt
3. .env.example
4. run_dev.py
5. app/core/config.py — pydantic-settings
6. app/core/security.py — HMAC verify, JWT
7. app/core/logging.py — JSON structured
8. app/core/exceptions.py — custom exceptions
9. app/db/session.py — async SQLAlchemy
10. app/main.py — FastAPI app

Har bir faylni to'liq, ishga tayyor holda yoz. "pass" yoki "TODO" qolmasin.
```

### P-002: Yangi DB modeli va migration

```
@app/models/ papkasiga qarab, [MODEL_NOMI] uchun yangi model yarat.

Fields:
[fieldlar ro'yxati]

Keyin:
1. app/models/[model_nomi].py — to'liq SQLAlchemy modeli
2. alembic/versions/[XXX]_create_[table_nomi].py — migration
3. app/__init__.py ga import qo'sh

Mavjud modellar bilan bog'liqliklarni to'g'ri qo'y.
```

### P-003: Yangi API modul

```
@app/models/ @app/services/ @docs/RULES.md

[MODUL_NOMI] uchun to'liq modul yarat:

1. app/repositories/[modul].py — Repository sinfi
2. app/schemas/[modul].py — Request/Response sxemalar
3. app/services/[modul].py — Service sinfi (business logic)
4. app/api/v1/[modul].py — FastAPI router

Endpointlar:
[endpointlar ro'yxati]

app/main.py ga router ni ulashni unutma.
```

### P-004: Xatoni tuzatish

```
Quyidagi xato chiqyapti. Tuzat.

Xato:
```
[XATO MATNI]
```

Fayl: [fayl nomi]
Qilayotgan narsam: [nima qilayotgan edim]

1. Xato sababini tushuntir
2. To'g'rilan
3. @codebase da xuddi shunday muammo boshqa joyda bormi? Tekshir
4. @docs/RULES.md qoidalarini buzmadingmi?
```

### P-005: WebApp ekrani

```
@app/webapp/templates/base.html @app/webapp/static/js/api.js

[EKRAN_NOMI] ekranini yarat.

API endpoint: [endpoint]
Ma'lumotlar: [qanday ma'lumotlar ko'rsatiladi]

Yaratilishi kerak:
1. app/webapp/templates/[ekran].html — to'liq HTML
2. app/webapp/static/js/[ekran].js — JS logic
3. app/webapp/static/css/[ekran].css (agar kerak bo'lsa)

Shart:
- Loading skeleton bo'lishi shart
- Empty state bo'lishi shart
- Error state bo'lishi shart
- Telegram WebApp theme variables ishlatilsin
- Haptic feedback tugmalarda
- Mobile-first, 375px
```

### P-006: Test yozish

```
@tests/conftest.py @app/services/[servis].py

[SERVIS_NOMI] uchun testlar yoz.

Test scenarios:
1. [scenario 1]
2. [scenario 2]
3. [scenario 3]

tests/test_[servis_nomi].py faylini to'liq yoz.
Barcha edge caselarni qamrab ol.
```

### P-007: Redis cache qo'shish

```
@app/services/[servis].py ga Redis caching qo'sh.

Cache strategy:
- Key: [key format]
- TTL: [necha sekund]
- Invalidation: [qachon cache o'chiriladi]

1. Servis da cache_get va cache_set qo'sh
2. Cache miss bo'lganda DB dan o'qisin
3. Yangilanishda cache invalidate qilinsin
```

### P-008: Bot notification

```
@bot/handlers/notifications.py @app/services/notification.py

[HODISA] uchun bot notification qo'sh.

Xabar formati:
[xabar ko'rinishi]

1. app/services/notification.py ga yangi method
2. Trigger: [qayerdan chaqiriladi]
3. Error handling: bot offline bo'lsa ham order fail bo'lmasin
```

### P-009: Admin panel feature

```
@app/api/v1/admin/ @docs/RULES.md

Admin panel uchun [FEATURE] qo'sh.

1. app/api/v1/admin/[fayl].py — endpoint
2. app/schemas/admin.py ga sxema
3. app/services/admin.py ga logic
4. app/webapp/templates/admin/[sahifa].html (agar UI kerak bo'lsa)

Admin middleware allaqachon bor, ishlatilsin.
```

### P-010: Performance optimizatsiya

```
@codebase

[FEATURE/ENDPOINT] sekin ishlayapti. Optimizatsiya qil.

Muammo: [nima sekin]

Tekshir va tuzat:
1. N+1 query muammolari (selectinload/joinedload)
2. Kerakli DB indexlar bormi?
3. Redis cache qo'shsa bo'ladimi?
4. Pagination to'g'ri ishlayaptimi?

Har o'zgartirish uchun sabab tushuntir.
```

---

## MAXSUS VAZIYATLAR

### Migratsiya muvaffaqiyatsiz bo'lsa

```
Alembic migration xato berayapti:

```
[XATO]
```

1. Xatoni tushuntir
2. Migration faylini to'g'rila
3. Agar head ni reset qilish kerak bo'lsa ko'rsatib ber
```

### Import xatolari

```
ImportError chiqyapti:
[XATO]

@codebase Barcha import yo'llarini tekshir va to'g'rila.
Circular import bor bo'lsa, qanday hal qilish kerak?
```

### Docker muammolari

```
docker-compose up da xato:
[XATO]

docker-compose.yml va bog'liq konfiguratsiyalarni tekshir.
```

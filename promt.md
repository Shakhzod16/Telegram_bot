# Phase Prompts (Execution Board)

Quyidagi promptlar `02_execution_board.md` bo'yicha ishlash uchun tayyorlangan.
Har promptda:
- phase yakunida checkboxlarni `[x]` ga o'tkazish
- ishga tushirish (run)
- tekshirish (verification)
majburiy qilib berilgan.

## Majburiy Pre-Read (har safar)
Phase ishini boshlashdan oldin quyidagilarni majburiy o'qing:
- `rg --files -g "*.md"` orqali barcha `.md` fayllarni toping
- Root fayllar: `README.md`, `02_execution_board.md`, `10_mvp_checklist.md`, `promt.md`
- Roadmap fayllar: `roadmap/README.md`, `roadmap/01_project_audit.md` ... `roadmap/10_mvp_checklist.md`

Pre-read tugagach hisobot format:
1. O'qilgan `.md` fayllar ro'yxati
2. Tanlangan phase scope (nimalar kiradi / nimalar kirmaydi)
3. Acceptance criteria va tekshirish usuli
4. Keyin implementatsiya

## Phase Selector Prompt (eng muhim, copy-paste)
```text
Siz 02_execution_board.md bo'yicha faqat PHASE {N} ni bajarasiz.

Majburiy tartib:
1. Avval repo ichidagi barcha `.md` fayllarni toping va o'qing:
   - rg --files -g "*.md"
2. O'qilgan fayllar bo'yicha qisqa pre-read hisobot bering:
   - qaysi fayllar o'qildi
   - PHASE {N} ga tegishli tasklar
   - acceptance criteria
3. Shundan keyin faqat PHASE {N} tasklarini ketma-ket implement qiling.
4. Har task tugagach:
   - 02_execution_board.md dagi mos checkboxlarni [x] ga o'tkazing
   - agar roadmap/02_execution_board.md bo'lsa, uni ham sinxron yangilang
5. Har taskdan keyin run + verification qiling.
6. Phase yakunida:
   - o'zgargan fayllar
   - ishga tushirish buyruqlari
   - test/tekshiruv natijalari
   - qolgan risklar
   - keyingi phasega tayyorlik

Muhim:
- Regression bo'lmasin.
- Scope dan chiqilmang (faqat PHASE {N}).
- Testdan o'tmagan kodni tugallangan deb belgilamang.
```

## Universal Prompt (har phase uchun boshiga qo'shish mumkin)
```text
Siz bu loyihada 02_execution_board.md bo'yicha ishlaysiz.
Majburiy qoidalar:
1. Avval barcha `.md` fayllarni toping va o'qing (`rg --files -g "*.md"`), keyin ishlashni boshlang.
2. Faqat so'ralgan PHASE tasklarini bajaring.
3. Har bir task yakunida 02_execution_board.md ichidagi mos checkboxlarni [x] ga o'tkazing.
4. Agar roadmap/02_execution_board.md ham ishlatilayotgan bo'lsa, undagi mos checkboxlarni ham sinxron yangilang.
5. Har phase oxirida:
   - O'zgargan fayllar ro'yxati
   - Ishga tushirish buyruqlari
   - Tekshirish/test natijalari
   - Qolgan risk yoki blockerlar
   ni aniq yozing.
6. Kodni regressiyasiz qiling: mavjud ishlayotgan funksiyalar buzilmasin.
7. Har phase oxirida git diff qisqacha xulosasini bering.
```

## PHASE 0 Prompt
```text
02_execution_board.md bo'yicha PHASE 0 (P0-T1 dan P0-T5 gacha) ni to'liq bajaring.
Talablar:
- Tasklar ketma-ketligi: P0-T1 -> P0-T2 -> P0-T3 -> P0-T4 -> P0-T5.
- Har task yakunida 02_execution_board.md dagi checkboxlarni [x] ga o'tkazing.
- Har taskdan keyin ishlashini tekshiring.
- Har task uchun alohida commit message tavsiya qiling (yoki user xohlasa commit ham qiling).

Ishga tushirish:
- python -m bot.main
- python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

Tekshirish:
- http://127.0.0.1:8000/docs ochilishi
- pytest
- import xatolar yo'qligi
- .env boshqaruvi va log yozilishi
- alembic upgrade head

Phase yakunida:
- Bajarilgan tasklar ro'yxati
- Belgilangan checkboxlar
- Test natijalari
- Keyingi phasega tayyorlik holati
```

## PHASE 1 Prompt
```text
02_execution_board.md bo'yicha PHASE 1 (P1-T1, P1-T2, P1-T3) ni to'liq implement qiling.
Maqsad: Router -> Service -> Repository arxitekturasi.

Majburiylar:
- backend/repositories, backend/services, backend/schemas ni ishlab turing.
- backend/main.py dan biznes logikani qatlamlarga ajrating.
- Har task yakunida checkboxlarni [x] ga o'tkazing.
- Regression bo'lmasin.

Ishga tushirish:
- python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
- python -m bot.main

Tekshirish:
- /docs da endpoint va schema lar ko'rinishi
- mavjud order/payment oqimi ishlashi
- pytest
- kamida smoke test: bootstrap -> order -> payment/create

Phase yakunida:
- arxitektura xaritasi (qaysi fayl nima qiladi)
- checkboxlar yangilangan holati
- test va run natijalari
```

## PHASE 2 Prompt
```text
02_execution_board.md bo'yicha PHASE 2 (P2-T1, P2-T2, P2-T3, P2-T4) ni bajaring.
Maqsad: Order flow va paymentni production-ready qilish.

Majburiylar:
- Status transition validation qo'shing.
- order_status_history yozuvlari ishlasin.
- Click signature verify to'liq ishlasin.
- Payme flow to'liq bo'lsin (kerakli metodlar).
- Cash payment qo'shilsin.
- Har taskdan keyin checkboxlarni [x] ga o'tkazing.

Ishga tushirish:
- python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
- python -m bot.main

Tekshirish:
- pytest tests/test_api.py -q
- callback idempotency testi
- order status o'tish testi
- cash payment flow testi
- manual: create order -> payment -> delivered

Phase yakunida:
- payment xavfsizlik holati
- bajarilgan checkboxlar
- test loglari va natija
```

## PHASE 3 Prompt
```text
02_execution_board.md bo'yicha PHASE 3 (P3-T1, P3-T2, P3-T3) ni implement qiling.
Maqsad: UX va foydalanuvchi qulayligi.

Majburiylar:
- Saved addresses (CRUD, default, max 5)
- Reorder funksiyasi
- i18n centralizatsiya (locale fayllarga ko'chirish)
- Har task yakunida checkboxlarni [x] ga o'tkazing.

Ishga tushirish:
- python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
- python -m bot.main

Tekshirish:
- address create/list/delete/default
- reorder endpoint va WebApp cart to'lishi
- 3 tilda matnlar to'g'ri chiqishi
- pytest

Phase yakunida:
- UX bo'yicha nimalar yaxshilangani
- checkbox holati
- manual test checklist natijasi
```

## PHASE 4 Prompt
```text
02_execution_board.md bo'yicha PHASE 4 (P4-T1, P4-T2) ni bajaring.
Maqsad: Admin boshqaruvini kuchaytirish.

Majburiylar:
- Admin Telegram panelni kengaytirish
- Admin web panel (FastAPI + Jinja2) MVP
- Faqat adminlar kira olishi (auth/filter)
- Har taskdan keyin checkboxlarni [x] ga o'tkazing.

Ishga tushirish:
- python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
- python -m bot.main

Tekshirish:
- admin bo'lmagan user uchun 403
- admin orders/stats ishlashi
- web admin login va sahifalar ishlashi
- pytest

Phase yakunida:
- admin funksiyalar ro'yxati
- checkbox yangilanishi
- security tekshiruv natijalari
```

## PHASE 5 Prompt
```text
02_execution_board.md bo'yicha PHASE 5 (P5-T1, P5-T2) ni implement qiling.
Maqsad: Growth features (promo + referral).

Majburiylar:
- Promo code tizimi (validate/apply/limit/expiry)
- Referral tizimi (deep link, bonus, stats)
- Har task yakunida checkboxlarni [x] ga o'tkazing.

Ishga tushirish:
- python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
- python -m bot.main

Tekshirish:
- promo valid/invalid/expired/use-limit holatlari
- referral code bilan onboarding va bonus berilishi
- pytest

Phase yakunida:
- growth flow demo
- checkbox holati
- edge-case natijalari
```

## PHASE 6 Prompt
```text
02_execution_board.md bo'yicha PHASE 6 (P6-T1, P6-T2, P6-T3) ni to'liq bajaring.
Maqsad: test qamrovi va release ishonchliligi.

Majburiylar:
- Unit tests
- API tests
- Payment sandbox tests
- Har task yakunida checkboxlarni [x] ga o'tkazing.

Ishga tushirish:
- pytest tests/unit -v
- pytest tests/api -v
- pytest --cov=backend

Tekshirish:
- failing tests = 0
- payment sandbox oqimi tasdiqlangan
- coverage hisobotini chiqaring

Phase yakunida:
- test summary (passed/failed/skipped)
- coverage foizi
- checkboxlar to'liq yangilangan holat
```

## To'liq Avtopilot Prompt (Phase 0 -> 6)
```text
02_execution_board.md dagi PHASE 0 dan PHASE 6 gacha ketma-ket bajaring.
Qoidalar:
1. Har phase tugagach to'xtab hisobot bering.
2. Har phase tugagach mos checkboxlarni [x] ga o'tkazing.
3. Har phase uchun run + verification buyruqlarini amalda bajaring.
4. Testdan o'tmagan kodni keyingi phasega o'tkazmang.
5. Yakunda launch readiness report bering:
   - Nima bitdi
   - Nima qoldi
   - Blockerlar
   - Tavsiya etilgan keyingi 3 qadam
```

# O'rnatish va ishga tushirish

## Talablar

- Python 3.12+
- Docker + Docker Compose
- Git

## 1. Loyihani klonlash

```bash
git clone <repo-url>
cd food_delivery
```

## 2. Environment sozlash

```bash
cp .env.example .env
```

`.env` faylini oching va to'ldiring:

```bash
# Bu qiymatlarni o'zingizniki bilan almashtiring:
TELEGRAM_BOT_TOKEN=<@BotFather dan olingan token>
SECRET_KEY=<32+ belgilik tasodifiy string>
ADMIN_TELEGRAM_IDS=<sizning Telegram ID ingiz>
```

Telegram ID ni bilish uchun: @userinfobot ga `/start` yuboring.

## 3. Docker services ishga tushirish

```bash
docker-compose up -d db redis
```

Tekshirish:
```bash
docker-compose ps
# db va redis "Up" ko'rsatishi kerak
```

## 4. Python dependencies o'rnatish

```bash
pip install -r requirements.txt
```

## 5. Database migratsiyalar

```bash
alembic upgrade head
```

## 6. Test ma'lumotlari (ixtiyoriy)

```bash
python scripts/seed.py
```

Bu quyidagilarni yaratadi:
- 5 kategoriya
- 20 mahsulot
- 2 filial (Toshkent)
- 3 promo kod: `FIRST10`, `SUMMER20`, `FIXED5000`

## 7. Ishga tushirish

**Variant A — barcha birga:**
```bash
python run_dev.py
```

`run_dev.py` tunnel rejimlari:
- `DEV_TUNNEL_PROVIDER=auto` (tavsiya) -> avval `cloudflared`, kerak bo'lsa `localtunnel`
- `DEV_TUNNEL_PROVIDER=none` -> tunnel ochilmaydi
- `DEV_TUNNEL_PROVIDER=cloudflared` -> faqat Cloudflare quick tunnel
- `DEV_TUNNEL_PROVIDER=localtunnel` -> faqat localtunnel

**Variant B — alohida (debugging uchun):**
```bash
# Terminal 1:
uvicorn app.main:app --reload --port 8000

# Terminal 2:
python -m bot.main
```

## 8. Tekshirish

```bash
# API health check:
curl http://localhost:8000/health

# API docs:
# http://localhost:8000/docs

# WebApp:
# http://localhost:8000/webapp/
```

## Ngrok (Telegram WebApp uchun HTTPS kerak)

```bash
ngrok http 8000
```

Ngrok URL ni `.env` ga yozing:
```
WEBAPP_URL=https://xxxx.ngrok.io/webapp
BACKEND_URL=https://xxxx.ngrok.io
```

Botga webhook set qiling:
```bash
curl "https://api.telegram.org/bot{TOKEN}/setWebhook?url=https://xxxx.ngrok.io/bot/webhook"
```

## Testlar

```bash
pytest tests/ -v
pytest tests/ -v --cov=app
```

## Keng tarqalgan xatolar

| Xato | Sabab | Yechim |
|------|-------|--------|
| `Connection refused 5432` | DB ishlamayapti | `docker-compose up -d db` |
| `Connection refused 6379` | Redis ishlamayapti | `docker-compose up -d redis` |
| `401 Unauthorized` | initData invalid | BOT_TOKEN to'g'riligini tekshiring |
| `ModuleNotFoundError` | Package o'rnatilmagan | `pip install -r requirements.txt` |
| Bot javob bermayapti | Token noto'g'ri | .env da TOKEN ni tekshiring |

# 08 — Deployment & Security

---

## 8.1 Hozirgi Deployment Holati

| Komponent | Hozir | Maqsad |
|-----------|-------|--------|
| Backend | ✅ Render da (`telegram-bot-1-8a3a.onrender.com`) | Render yoki VPS |
| Frontend | ✅ Backend orqali serve | Shu holat OK |
| Bot | 🟡 Polling (taxminan) | Webhook ga o'tish |
| SSL | ✅ Render avtomatik | VPS da certbot kerak |
| DB | 🟡 SQLite (taxminan) | PostgreSQL ga o'tish |

---

## 8.2 Deployment Stack Tavsiyalar

| Komponent | Tavsiya | Alternativ |
|-----------|---------|-----------|
| Backend hosting | Render (hozir bor) yoki VPS | Hetzner, DigitalOcean |
| DB | PostgreSQL | SQLite (production da yaxshi emas) |
| Web server | Nginx (VPS da) | Render built-in |
| SSL | Let's Encrypt certbot | Render avtomatik |
| Bot mode | Webhook | Polling (faqat dev da) |
| Process mgr | Systemd | PM2, Supervisor |
| Monitoring | Sentry (free tier) | — |
| Backup | pg_dump cron | — |

---

## 8.3 Webhook vs Polling

### Hozirgi holat
```bash
# bot/main.py da qaysi ishlatilayotganini tekshiring:
grep -n "polling\|webhook\|start_polling\|start_webhook" bot/main.py
```

### Webhook afzallik
- Server resurslarini tejaydi
- Production da standart
- Tezroq (Telegram push qiladi)

### Webhook sozlash
```python
# bot/main.py — webhook mode
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

WEBHOOK_PATH = f"/webhook/{settings.BOT_TOKEN}"
WEBHOOK_URL = f"{settings.WEBHOOK_URL}{WEBHOOK_PATH}"

async def on_startup(bot: Bot):
    await bot.set_webhook(
        url=WEBHOOK_URL,
        secret_token=settings.WEBHOOK_SECRET,  # qo'shimcha xavfsizlik
        drop_pending_updates=True
    )

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()

# FastAPI da webhook endpoint qo'shish:
@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    # aiogram webhook handler
```

- [ ] Webhook URL sozlangan
- [ ] `BOT_TOKEN` path da (yoki secret_token)
- [ ] SSL sertifikat bor (HTTPS majburiy)
- [ ] `setWebhook` chaqirilgan
- [ ] `getWebhookInfo` tekshirilgan

---

## 8.4 Environment Variables To'liq Ro'yxati

```bash
# .env.production

# ═══ BOT ═══
BOT_TOKEN=1234567890:AAExxxxxxxxxxxxxxxxxxxxxx
WEB_APP_URL=https://telegram-bot-1-8a3a.onrender.com
WEBHOOK_URL=https://telegram-bot-1-8a3a.onrender.com
WEBHOOK_SECRET=random_strong_secret_here
ADMIN_IDS=123456789,987654321  # vergul bilan ajratilgan

# ═══ DATABASE ═══
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/fooddelivery
# SQLite uchun: sqlite+aiosqlite:///./food_delivery.db

# ═══ CLICK ═══
CLICK_MERCHANT_ID=12345
CLICK_SERVICE_ID=67890
CLICK_SECRET_KEY=your_click_secret

# ═══ PAYME ═══
PAYME_MERCHANT_ID=abc123
PAYME_SECRET_KEY=your_payme_key

# ═══ APP ═══
ENVIRONMENT=production
SECRET_KEY=super_random_secret_key_64_chars
ALLOWED_ORIGINS=https://telegram-bot-1-8a3a.onrender.com
SENTRY_DSN=https://xxx@sentry.io/yyy

# ═══ DEV faqat ═══
# ENVIRONMENT=development
# DATABASE_URL=sqlite+aiosqlite:///./dev.db
```

### .env.example (git da bo'ladi)
```bash
BOT_TOKEN=
WEB_APP_URL=
WEBHOOK_URL=
WEBHOOK_SECRET=
ADMIN_IDS=
DATABASE_URL=sqlite+aiosqlite:///./food_delivery.db
CLICK_MERCHANT_ID=
CLICK_SERVICE_ID=
CLICK_SECRET_KEY=
PAYME_MERCHANT_ID=
PAYME_SECRET_KEY=
ENVIRONMENT=development
SECRET_KEY=
ALLOWED_ORIGINS=
SENTRY_DSN=
```

---

## 8.5 Nginx Config (VPS uchun)

```nginx
# /etc/nginx/sites-available/fooddelivery
server {
    listen 80;
    server_name yourdomain.uz;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.uz;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.uz/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.uz/privkey.pem;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/m;
    
    location / {
        limit_req zone=api burst=10 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 8.6 Systemd Service (VPS uchun)

```ini
# /etc/systemd/system/fooddelivery.service
[Unit]
Description=FoodDelivery Bot Backend
After=network.target postgresql.service

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/fooddelivery
ExecStart=/home/ubuntu/fooddelivery/venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=3
EnvironmentFile=/home/ubuntu/fooddelivery/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable fooddelivery
sudo systemctl start fooddelivery
sudo systemctl status fooddelivery
```

---

## 8.7 Backup Script

```bash
#!/bin/bash
# scripts/backup.sh
DATE=$(date +%Y-%m-%d_%H-%M)
BACKUP_DIR="/home/ubuntu/backups"

mkdir -p $BACKUP_DIR

# PostgreSQL backup
pg_dump $DATABASE_URL > "$BACKUP_DIR/db_$DATE.sql"

# Faqat oxirgi 30 ta backup saqlash
ls -t $BACKUP_DIR/db_*.sql | tail -n +31 | xargs rm -f

echo "Backup done: db_$DATE.sql"
```

```bash
# Crontab (har kecha 02:00 da)
0 2 * * * /home/ubuntu/fooddelivery/scripts/backup.sh >> /var/log/backup.log 2>&1
```

---

## 8.8 Sentry Monitoring

```python
# backend/main.py ga qo'shish
import sentry_sdk
from config.settings import settings

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.1,
        environment=settings.ENVIRONMENT,
        before_send=scrub_sensitive_data  # token/password larni o'chirish
    )
```

- [ ] Sentry account yaratilgan (free tier)
- [ ] `SENTRY_DSN` `.env` da
- [ ] Sentry dashboard ishlaydi
- [ ] Sensitive data scrub qilinadi

---

## 8.9 Security Checklist

### HTTPS / SSL
- [ ] HTTPS ishlaydi (Render avtomatik yoki certbot)
- [ ] Webhook URL HTTPS
- [ ] Mixed content yo'q (HTTP + HTTPS aralash emas)

### Bot Xavfsizligi
- [ ] Webhook secret token o'rnatilgan (`setWebhook(secret_token=...)`)
- [ ] WebApp initData HMAC verify
- [ ] Admin ID lar `.env` da, DB da emas
- [ ] Bot token git da yo'q

### Payment Xavfsizligi
- [ ] Click HMAC sign verify qo'shilgan
- [ ] Payme Basic Auth verify
- [ ] Payment idempotency (UNIQUE constraint)
- [ ] Sandbox test o'tgan

### API Xavfsizligi
- [ ] Rate limiting (`slowapi` yoki nginx)
- [ ] CORS faqat o'z domenidan (`ALLOWED_ORIGINS`)
- [ ] Input validation (Pydantic)
- [ ] SQL injection himoya (ORM)

### Frontend Xavfsizligi
- [ ] XSS: `innerHTML` o'rniga `textContent` ishlatilgan
- [ ] API URL `.env` dan (hardcoded emas)
- [ ] Foydalanuvchi inputi sanitize qilinadi

### Logging Xavfsizligi
- [ ] Log da token/password yo'q
- [ ] Log da to'lov card raqami yo'q
- [ ] Log fayllar faqat server da

### Secrets Management
- [ ] `.env` `.gitignore` da
- [ ] `.env.example` git da (qiymatlar bo'sh)
- [ ] Render/VPS da environment variables GUI orqali
- [ ] Secret rotation rejasi bor

### Database
- [ ] DB password kuchli (default `postgres` emas)
- [ ] DB faqat localhost dan accessible (VPS da)
- [ ] Backup har kecha ishlaydi

---

## 8.10 Render.com Sozlamalar

```yaml
# render.yaml (agar ishlatilsa)
services:
  - type: web
    name: fooddelivery
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        sync: false    # Render dashboard da kiritiladi
      - key: BOT_TOKEN
        sync: false
      - key: CLICK_SECRET_KEY
        sync: false
```

**Render dashboard da o'rnatish:**
- [ ] Environment → Add Environment Variable
- [ ] Barcha `.env` qiymatlarini Render da kiritish
- [ ] Deploy trigger sozlash (github push → auto deploy)

---

## 8.11 PostgreSQL ga O'tish (SQLite dan)

```python
# Hozir (taxminan): sqlite:///./food_delivery.db
# Maqsad: postgresql+asyncpg://user:pass@host/dbname

# 1. PostgreSQL o'rnatish (VPS da)
sudo apt install postgresql postgresql-contrib

# 2. DB va user yaratish
sudo -u postgres psql
CREATE DATABASE fooddelivery;
CREATE USER fooduser WITH PASSWORD 'strongpassword';
GRANT ALL PRIVILEGES ON DATABASE fooddelivery TO fooduser;

# 3. requirements.txt ga qo'shish
asyncpg
psycopg2-binary

# 4. .env da o'zgartirish
DATABASE_URL=postgresql+asyncpg://fooduser:strongpassword@localhost:5432/fooddelivery

# 5. Migration
alembic upgrade head
```

- [ ] PostgreSQL o'rnatilgan
- [ ] DB yaratilgan
- [ ] `DATABASE_URL` yangilangan
- [ ] `alembic upgrade head` xatosiz

---

[← API Roadmap](./07_api_roadmap.md) | [Keyingi: Timeline →](./09_timeline.md)

# Telegram Food Delivery Platform

Full-stack Telegram food delivery system with:

- async Telegram bot on `python-telegram-bot`
- FastAPI backend
- Telegram WebApp frontend
- SQLite database
- multilingual UX: Uzbek, Russian, English
- onboarding flow
- cart, location, payment link generation, and admin notifications

## Structure

```text
telegram-Bot/
├── bot/
│   ├── handlers/
│   │   ├── onboarding.py
│   │   └── webapp.py
│   └── main.py
├── backend/
│   └── main.py
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── database/
│   └── models.py
├── utils/
│   ├── keyboards.py
│   └── texts.py
├── config.py
├── requirements.txt
└── .env
```

## Environment

Create `.env`:

```env
BOT_TOKEN=your_real_bot_token
WEB_APP_URL=https://your-public-webapp-url
ADMIN_CHAT_ID=0
DATABASE_PATH=food_delivery.db
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
CLICK_PAYMENT_URL_TEMPLATE=https://my.click.uz/services/pay?service_id={provider}&merchant_id={order_id}&amount={amount}
PAYME_PAYMENT_URL_TEMPLATE=https://checkout.paycom.uz/{provider}?id={order_id}&amount={amount}
PAYME_MERCHANT_API_URL=https://checkout.paycom.uz/api
LOG_LEVEL=INFO
```

## Run

Start backend:

```powershell
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Start bot:

```powershell
python -m bot.main
```

## Flow

1. User starts the bot
2. Selects language
3. Enters name, shares phone, enters city
4. Receives persistent menu with WebApp button
5. Opens WebApp, manages cart, detects location, creates order
6. Backend recalculates totals from DB and stores order
7. WebApp sends order payload back to the bot
8. Bot sends summary to user and admin
9. User chooses Click or Payme payment link

## Notes

- Prices are validated server-side from SQLite.
- Payment integration here is adapter-based and requires your real Click/Payme merchant parameters and webhook mapping in production.
- Payme public merchant docs were available at `https://developer.help.paycom.uz/`.
- A public HTTPS `WEB_APP_URL` is required for Telegram Web Apps.

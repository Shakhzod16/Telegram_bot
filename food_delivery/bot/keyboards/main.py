from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


def main_keyboard(webapp_url: str, admin_url: str | None = None) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text="Buyurtma berish",
                web_app=WebAppInfo(url=webapp_url),
            )
        ]
    ]
    if admin_url:
        rows.append(
            [
                InlineKeyboardButton(
                    text="Admin panel",
                    web_app=WebAppInfo(url=admin_url),
                )
            ]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=rows
    )

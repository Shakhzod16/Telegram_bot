from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_from_telegram(self, telegram_user: dict) -> User:
        telegram_id = int(telegram_user["id"])
        first_name = str(telegram_user.get("first_name") or "")
        last_name = telegram_user.get("last_name")
        username = telegram_user.get("username")
        language = str(telegram_user.get("language_code") or "uz")
        is_admin = telegram_id in settings.admin_telegram_id_set
        return await self.create(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            language=language,
            is_admin=is_admin,
        )

    async def update_last_seen(self, user_id: int) -> None:
        user = await self.get_by_id(user_id)
        if user is None:
            return
        user.updated_at = datetime.now(timezone.utc)
        await self.session.flush()

    async def list_all(self, offset: int, limit: int) -> list[User]:
        stmt = select(User).order_by(User.id.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self) -> int:
        stmt = select(func.count()).select_from(User)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

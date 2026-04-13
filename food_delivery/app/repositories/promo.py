from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.promo import Promo
from app.repositories.base import BaseRepository


class PromoRepository(BaseRepository[Promo]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Promo)

    async def get_by_code(self, code: str) -> Promo | None:
        stmt = select(Promo).where(Promo.code == code.upper().strip())
        res = await self._session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_all(self) -> list[Promo]:
        stmt = select(Promo).order_by(Promo.id.desc())
        res = await self._session.execute(stmt)
        return list(res.scalars().all())

    def is_promo_valid_now(self, promo: Promo, now: datetime | None = None) -> bool:
        if not promo.is_active:
            return False
        if now is None:
            now = datetime.now(timezone.utc)
        if promo.starts_at and now < promo.starts_at:
            return False
        if promo.ends_at and now > promo.ends_at:
            return False
        if promo.max_uses is not None and promo.used_count >= promo.max_uses:
            return False
        return True

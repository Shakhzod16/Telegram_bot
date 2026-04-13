from __future__ import annotations

from datetime import datetime, time
from math import asin, cos, radians, sin, sqrt
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.order import Order


class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    lat: Mapped[float] = mapped_column(Float(), nullable=False)
    lng: Mapped[float] = mapped_column(Float(), nullable=False)
    radius_km: Mapped[float] = mapped_column(Float(), nullable=False, default=5.0)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=True)
    open_time: Mapped[time] = mapped_column(Time(), nullable=False)
    close_time: Mapped[time] = mapped_column(Time(), nullable=False)
    delivery_fee: Mapped[int] = mapped_column(Integer(), nullable=False, default=5000)

    orders: Mapped[list["Order"]] = relationship(back_populates="branch")

    def distance_km(self, lat: float, lng: float) -> float:
        r = 6371.0
        lat1, lon1, lat2, lon2 = map(radians, [self.lat, self.lng, lat, lng])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        return r * c

    def is_open_now(self, now: datetime | None = None) -> bool:
        if not self.is_active:
            return False
        if now is None:
            now = datetime.now().astimezone()
        t = now.timetz().replace(tzinfo=None) if now.tzinfo else now.time()
        ot = self.open_time
        ct = self.close_time
        if ot <= ct:
            return ot <= t <= ct
        return t >= ot or t <= ct

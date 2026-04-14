from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AdminWhitelistCreate(BaseModel):
    telegram_id: int
    note: Optional[str] = None


class AdminWhitelistResponse(BaseModel):
    id: int
    telegram_id: int
    added_by: Optional[int]
    added_at: datetime
    is_active: bool
    note: Optional[str]
    user_full_name: Optional[str] = None
    user_phone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AdminWhitelistUpdate(BaseModel):
    is_active: Optional[bool] = None
    note: Optional[str] = None

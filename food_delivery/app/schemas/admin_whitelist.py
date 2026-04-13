from datetime import datetime
import re
from typing import Optional

from pydantic import BaseModel, validator


class AdminWhitelistCreate(BaseModel):
    phone: str
    note: Optional[str] = None

    @validator("phone")
    def validate_phone(cls, v):
        v = v.strip()
        if not re.match(r"^\+998\d{9}$", v):
            raise ValueError("Telefon raqam +998XXXXXXXXX formatida bo'lishi kerak")
        return v


class AdminWhitelistResponse(BaseModel):
    id: int
    phone: str
    added_by: Optional[int]
    added_at: datetime
    is_active: bool
    note: Optional[str]

    class Config:
        orm_mode = True


class AdminWhitelistUpdate(BaseModel):
    is_active: bool
    note: Optional[str] = None

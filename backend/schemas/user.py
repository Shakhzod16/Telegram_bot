# -*- coding: utf-8 -*-
from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    telegram_user_id: int
    first_name: str = ""
    last_name: str = ""
    username: str = ""
    language: str = "en"


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    phone: str | None = None
    language: str | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_user_id: int
    first_name: str
    last_name: str
    username: str
    phone: str
    language: str

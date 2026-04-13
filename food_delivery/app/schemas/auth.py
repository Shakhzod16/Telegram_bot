from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TelegramInitRequest(BaseModel):
    init_data: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    telegram_id: int
    first_name: str
    last_name: str | None
    username: str | None
    language: str
    is_admin: bool
    is_superadmin: bool
    owner_id: int | None

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Backward-compatible schemas used by existing endpoints.
class PhoneRequestBody(BaseModel):
    phone: str = Field(..., min_length=9, max_length=32)


class PhoneVerifyBody(BaseModel):
    phone: str = Field(..., min_length=9, max_length=32)
    code: str = Field(..., min_length=4, max_length=8)


class MessageResponse(BaseModel):
    message: str
    debug_code: str | None = None

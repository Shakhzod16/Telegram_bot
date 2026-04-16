from pydantic import BaseModel, Field


class UserPublic(BaseModel):
    id: int
    telegram_id: int
    first_name: str
    last_name: str | None
    username: str | None
    phone: str | None
    language: str
    is_admin: bool
    is_superadmin: bool
    owner_id: int | None

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    first_name: str | None = Field(None, max_length=255)
    last_name: str | None = Field(None, max_length=255)
    language: str | None = Field(None, pattern="^(uz|ru|en)$")

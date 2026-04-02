# -*- coding: utf-8 -*-
from pydantic import BaseModel, ConfigDict, Field


class AddressCreate(BaseModel):
    # Used in order payloads for backward compatibility.
    label: str | None = None
    address_text: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class SavedAddressCreate(BaseModel):
    label: str = Field(min_length=1, max_length=80)
    address_text: str = Field(min_length=1, max_length=400)
    latitude: float | None = None
    longitude: float | None = None
    is_default: bool = False


class AddressRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    label: str
    address_text: str
    latitude: float | None = None
    longitude: float | None = None
    is_default: bool


class AddressActionRead(BaseModel):
    ok: bool
    address_id: int

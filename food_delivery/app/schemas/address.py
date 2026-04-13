from pydantic import BaseModel, Field


class AddressCreate(BaseModel):
    title: str | None = Field(None, max_length=64)
    address_line: str = Field(..., min_length=3, max_length=512)
    lat: float | None = None
    lng: float | None = None
    apartment: str | None = Field(None, max_length=32)
    floor: str | None = Field(None, max_length=32)
    entrance: str | None = Field(None, max_length=32)
    door_code: str | None = Field(None, max_length=32)
    landmark: str | None = Field(None, max_length=255)
    comment: str | None = Field(None, max_length=512)
    is_default: bool = False


class AddressUpdate(BaseModel):
    title: str | None = Field(None, max_length=64)
    address_line: str | None = Field(None, min_length=3, max_length=512)
    lat: float | None = None
    lng: float | None = None
    apartment: str | None = Field(None, max_length=32)
    floor: str | None = Field(None, max_length=32)
    entrance: str | None = Field(None, max_length=32)
    door_code: str | None = Field(None, max_length=32)
    landmark: str | None = Field(None, max_length=255)
    comment: str | None = Field(None, max_length=512)
    is_default: bool | None = None


class AddressOut(BaseModel):
    id: int
    title: str | None
    address_line: str
    lat: float | None
    lng: float | None
    apartment: str | None
    floor: str | None
    entrance: str | None
    door_code: str | None
    landmark: str | None
    comment: str | None
    is_default: bool

    model_config = {"from_attributes": True}

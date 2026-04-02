# -*- coding: utf-8 -*-
from pydantic import BaseModel, ConfigDict


class PaymentCreate(BaseModel):
    order_id: int
    provider: str


class PaymentRead(BaseModel):
    payment_id: int
    order_id: int
    provider: str
    payment_url: str
    status: str


class ClickCallback(BaseModel):
    click_trans_id: str
    service_id: str
    merchant_trans_id: int
    amount: float
    action: str
    sign_time: str
    sign_string: str


class PaymeRPC(BaseModel):
    method: str
    params: dict
    id: int | str | None = None


class PaymeRPCResponse(BaseModel):
    id: int | str | None = None
    result: dict | None = None
    error: dict | None = None


class PaymentCallbackPayload(BaseModel):
    provider: str
    transaction_id: str
    order_id: int
    status: str
    amount: int | None = None
    signature: str | None = None
    payload: dict | None = None


class PaymentCallbackRead(BaseModel):
    ok: bool
    order_id: int
    status: str


class ClickPrepareRead(BaseModel):
    click_trans_id: str
    merchant_trans_id: str
    error: int
    error_note: str


class ClickCompleteRead(BaseModel):
    click_trans_id: str
    merchant_trans_id: str
    error: int
    error_note: str
    status: str


class PaymentEntityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    provider: str
    amount: int
    status: str
    payment_url: str

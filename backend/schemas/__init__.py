# -*- coding: utf-8 -*-
from backend.schemas.address import AddressActionRead, AddressCreate, AddressRead, SavedAddressCreate
from backend.schemas.bootstrap import BootstrapResponse, BootstrapUser
from backend.schemas.cart import CartItemAdd, CartItemRead, CartRead
from backend.schemas.order import (
    OrderActionRead,
    OrderAdminRead,
    OrderCreate,
    OrderDetailsRead,
    OrderItemAdminRead,
    OrderRead,
    OrderStatusUpdate,
    OrderUserSummary,
)
from backend.schemas.payment import (
    ClickCallback,
    ClickCompleteRead,
    ClickPrepareRead,
    PaymentCallbackPayload,
    PaymentCallbackRead,
    PaymentCreate,
    PaymentEntityRead,
    PaymentRead,
    PaymeRPC,
    PaymeRPCResponse,
)
from backend.schemas.product import CategoryRead, ProductRead
from backend.schemas.reorder import ReorderItemRead, ReorderRead
from backend.schemas.user import UserCreate, UserRead, UserUpdate

# Backward-compatible aliases used in existing routes/tests.
LocationPayload = AddressCreate
CartItemPayload = CartItemAdd
OrderPayload = OrderCreate
PaymentPayload = PaymentCreate

__all__ = [
    "AddressCreate",
    "AddressRead",
    "AddressActionRead",
    "BootstrapResponse",
    "BootstrapUser",
    "CartItemAdd",
    "CartItemPayload",
    "CartItemRead",
    "CartRead",
    "CategoryRead",
    "ClickCallback",
    "ClickCompleteRead",
    "ClickPrepareRead",
    "LocationPayload",
    "OrderAdminRead",
    "OrderActionRead",
    "OrderCreate",
    "OrderDetailsRead",
    "OrderItemAdminRead",
    "OrderPayload",
    "OrderRead",
    "OrderStatusUpdate",
    "OrderUserSummary",
    "PaymentCallbackPayload",
    "PaymentCallbackRead",
    "PaymentCreate",
    "PaymentEntityRead",
    "PaymentPayload",
    "PaymentRead",
    "PaymeRPC",
    "PaymeRPCResponse",
    "ProductRead",
    "ReorderItemRead",
    "ReorderRead",
    "SavedAddressCreate",
    "UserCreate",
    "UserRead",
    "UserUpdate",
]

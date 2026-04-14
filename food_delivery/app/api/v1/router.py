from fastapi import APIRouter

from app.api.v1 import (
    addresses,
    cart,
    catalog,
    checkout,
    orders,
    profile,
)
from app.api.v1.admin.router import router as admin_router

api_router = APIRouter()
api_router.include_router(catalog.router)
api_router.include_router(catalog.legacy_router)
api_router.include_router(cart.router, prefix="/cart", tags=["cart"])
api_router.include_router(addresses.router, prefix="/addresses", tags=["addresses"])
api_router.include_router(checkout.router, prefix="/checkout", tags=["checkout"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
api_router.include_router(admin_router)

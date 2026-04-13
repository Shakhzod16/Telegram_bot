from fastapi import APIRouter

from app.api.v1 import (
    addresses,
    cart,
    catalog,
    checkout,
    orders,
    profile,
)
from app.api.v1.admin import branches as admin_branches
from app.api.v1.admin import categories as admin_categories
from app.api.v1.admin import orders as admin_orders
from app.api.v1.admin import products as admin_products
from app.api.v1.admin import promos as admin_promos
from app.api.v1.admin import users as admin_users

api_router = APIRouter()
api_router.include_router(catalog.router)
api_router.include_router(catalog.legacy_router)
api_router.include_router(cart.router, prefix="/cart", tags=["cart"])
api_router.include_router(addresses.router, prefix="/addresses", tags=["addresses"])
api_router.include_router(checkout.router, prefix="/checkout", tags=["checkout"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])

api_router.include_router(admin_products.router, prefix="/admin/products", tags=["admin-products"])
api_router.include_router(admin_categories.router, prefix="/admin/categories", tags=["admin-categories"])
api_router.include_router(admin_branches.router, prefix="/admin/branches", tags=["admin-branches"])
api_router.include_router(admin_promos.router, prefix="/admin/promos", tags=["admin-promos"])
api_router.include_router(admin_orders.router, prefix="/admin/orders", tags=["admin-orders"])
api_router.include_router(admin_users.router, prefix="/admin/users", tags=["admin-users"])

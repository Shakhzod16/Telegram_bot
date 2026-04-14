from __future__ import annotations

from fastapi import APIRouter

from . import branches, categories, orders, products, promos, settings, users

router = APIRouter(prefix="/admin")
router.include_router(products.router, prefix="/products", tags=["admin-products"])
router.include_router(categories.router, prefix="/categories", tags=["admin-categories"])
router.include_router(branches.router, prefix="/branches", tags=["admin-branches"])
router.include_router(promos.router, prefix="/promos", tags=["admin-promos"])
router.include_router(orders.router, prefix="/orders", tags=["admin-orders"])
router.include_router(users.router, prefix="/users", tags=["admin-users"])
router.include_router(settings.router)

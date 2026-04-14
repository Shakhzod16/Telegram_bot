from fastapi import APIRouter

from . import admins, stats, whitelist

router = APIRouter(prefix="/superadmin", tags=["superadmin"])
router.include_router(whitelist.router)
router.include_router(admins.router)
router.include_router(stats.router)


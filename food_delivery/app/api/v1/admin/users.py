from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserPublic
from app.services.admin import AdminService

router = APIRouter()


@router.get("")
async def list_users(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
) -> dict:
    rows, total = await AdminService(db).list_users(page, size)
    return {
        "items": [UserPublic.model_validate(u) for u in rows],
        "total": total,
        "page": page,
        "size": size,
    }

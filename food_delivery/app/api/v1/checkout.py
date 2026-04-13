from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.db.session import get_db
from app.models.user import User
from app.schemas.order import CheckoutPreviewRequest, CheckoutPreviewResponse
from app.services.checkout import CheckoutService

router = APIRouter()


@router.post("/preview", response_model=CheckoutPreviewResponse)
async def preview(
    body: CheckoutPreviewRequest,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    user: User = Depends(get_current_user),
) -> CheckoutPreviewResponse:
    return await CheckoutService(db, redis).preview(user.id, body)

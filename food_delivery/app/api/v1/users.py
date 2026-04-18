from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserPublic

router = APIRouter()


@router.get("/me", response_model=UserPublic)
async def get_me(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UserPublic:
    return UserPublic.model_validate(user)

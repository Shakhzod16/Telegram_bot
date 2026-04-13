from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import ProfileUpdate, UserPublic

router = APIRouter()


@router.get("", response_model=UserPublic)
async def get_profile(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UserPublic:
    return UserPublic.model_validate(user)


@router.patch("", response_model=UserPublic)
async def patch_profile(
    body: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UserPublic:
    repo = UserRepository(db)
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(user, k, v)
    await db.commit()
    await db.refresh(user)
    return UserPublic.model_validate(user)

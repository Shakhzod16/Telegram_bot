from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import User

router = APIRouter(prefix="/settings", tags=["admin-settings"])


class GroupLinkRequest(BaseModel):
    group_chat_id: int


@router.get("")
async def get_settings(current_user: User = Depends(require_admin)) -> dict:
    return {
        "group_chat_id": current_user.group_chat_id,
        "has_group": current_user.group_chat_id is not None,
    }


@router.post("/group")
async def link_group(
    body: GroupLinkRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one()
    user.group_chat_id = body.group_chat_id
    await db.commit()
    return {"message": "Guruh ulandi", "group_chat_id": body.group_chat_id}


@router.delete("/group")
async def unlink_group(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one()
    user.group_chat_id = None
    await db.commit()
    return {"message": "Guruh uzildi"}

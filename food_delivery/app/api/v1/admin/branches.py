from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import User
from app.repositories.branch import BranchRepository
from app.schemas.admin import BranchCreateAdmin, BranchUpdateAdmin
from app.services.admin import AdminService

router = APIRouter()


@router.get("")
async def list_branches(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> list:
    return await BranchRepository(db).list_all()


@router.post("")
async def create_branch(
    body: BranchCreateAdmin,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return await AdminService(db).create_branch(body)


@router.put("/{branch_id}")
async def update_branch(
    branch_id: int,
    body: BranchUpdateAdmin,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return await AdminService(db).update_branch(branch_id, body)


@router.delete("/{branch_id}")
async def delete_branch(
    branch_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    await AdminService(db).delete_branch(branch_id)
    return {"success": True}

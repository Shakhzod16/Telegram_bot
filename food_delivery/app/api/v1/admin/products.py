from __future__ import annotations

import re
import secrets
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.api.deps import check_resource_ownership, get_owner_filter, require_admin
from app.db.session import get_db
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.schemas.admin import ProductCreateAdmin, ProductUpdate

router = APIRouter()
PRODUCT_IMAGE_DIR = Path("app/webapp/static/images/products")
ALLOWED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


def _product_to_dict(product: Product) -> dict:
    return {
        "id": product.id,
        "category_id": product.category_id,
        "owner_id": product.owner_id,
        "name_uz": product.name_uz,
        "name_ru": product.name_ru,
        "description_uz": product.description_uz,
        "description_ru": product.description_ru,
        "base_price": str(product.base_price),
        "weight_grams": product.weight_grams,
        "image_url": product.image_url,
        "is_active": product.is_active,
    }


async def get_product_or_404(product_id: int, db: AsyncSession) -> Product:
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product


def _validation_error(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


def _check_category_access(category_owner_id: int | None, current_user: User) -> None:
    """
    Admin can use:
    - own category (owner_id == current_user.id)
    - legacy shared category (owner_id is NULL)
    Superadmin can use any category.
    """
    if current_user.is_superadmin:
        return
    if category_owner_id in (None, current_user.id):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Bu kategoriya sizga tegishli emas",
    )


def _parse_int(raw: Any, *, field: str, allow_none: bool = False) -> int | None:
    if raw in (None, ""):
        if allow_none:
            return None
        raise _validation_error(f"{field} majburiy")
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError) as exc:
        raise _validation_error(f"{field} noto'g'ri formatda") from exc


def _parse_bool(raw: Any, *, default: bool = True) -> bool:
    if raw in (None, ""):
        return default
    if isinstance(raw, bool):
        return raw
    text = str(raw).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    raise _validation_error("is_active true yoki false bo'lishi kerak")


async def _save_product_image(image: UploadFile | None) -> str | None:
    if image is None or not image.filename:
        return None

    suffix = Path(image.filename).suffix.lower() or ".jpg"
    if suffix not in ALLOWED_IMAGE_SUFFIXES:
        raise _validation_error("Rasm formati qo'llab-quvvatlanmaydi (jpg, jpeg, png, webp)")

    data = await image.read()
    if not data:
        raise _validation_error("Yuklangan rasm bo'sh")
    if len(data) > MAX_IMAGE_BYTES:
        raise _validation_error("Rasm hajmi 5MB dan oshmasligi kerak")

    PRODUCT_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    safe_stem = re.sub(r"[^a-zA-Z0-9_-]+", "-", Path(image.filename).stem).strip("-") or "product"
    filename = f"{safe_stem}-{int(time.time())}-{secrets.token_hex(4)}{suffix}"
    (PRODUCT_IMAGE_DIR / filename).write_bytes(data)
    return f"/static/images/products/{filename}"


def _build_body_from_json(payload: dict[str, Any]) -> ProductCreateAdmin:
    try:
        return ProductCreateAdmin.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(),
        ) from exc


def _build_body_from_form(form_data: Any, *, image_url: str | None) -> ProductCreateAdmin:
    payload: dict[str, Any] = {
        "category_id": _parse_int(form_data.get("category_id"), field="category_id"),
        "name_uz": (form_data.get("name_uz") or "").strip(),
        "name_ru": (form_data.get("name_ru") or "").strip(),
        "description_uz": (form_data.get("description_uz") or "").strip() or None,
        "description_ru": (form_data.get("description_ru") or "").strip() or None,
        "base_price": form_data.get("base_price") or form_data.get("price"),
        "weight_grams": _parse_int(form_data.get("weight_grams"), field="weight_grams", allow_none=True),
        "image_url": image_url or ((form_data.get("image_url") or "").strip() or None),
        "is_active": _parse_bool(form_data.get("is_active"), default=True),
    }

    owner_id_raw = form_data.get("owner_id")
    if owner_id_raw not in (None, ""):
        payload["owner_id"] = _parse_int(owner_id_raw, field="owner_id")

    try:
        return ProductCreateAdmin.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(),
        ) from exc


@router.get("")
async def list_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> list[dict]:
    owner_filter = get_owner_filter(current_user)
    query = select(Product)
    if owner_filter is not None:
        query = query.where(Product.owner_id == owner_filter)

    query = query.order_by(Product.id.desc()).limit(500)
    res = await db.execute(query)
    rows = list(res.scalars().all())
    return [_product_to_dict(p) for p in rows]


@router.post("")
async def create_product(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    content_type = request.headers.get("content-type", "").lower()
    if content_type.startswith("multipart/form-data"):
        form_data = await request.form()
        image_value = form_data.get("image")
        if image_value is not None and not isinstance(image_value, (UploadFile, StarletteUploadFile)):
            raise _validation_error("image fayl ko'rinishida yuborilishi kerak")
        image_obj = image_value if isinstance(image_value, (UploadFile, StarletteUploadFile)) else None
        image_url = await _save_product_image(image_obj)
        body = _build_body_from_form(form_data, image_url=image_url)
    else:
        try:
            raw_payload = await request.json()
        except Exception as exc:
            raise _validation_error("JSON noto'g'ri formatda") from exc
        body = _build_body_from_json(raw_payload if isinstance(raw_payload, dict) else {})

    category_result = await db.execute(select(Category).where(Category.id == body.category_id))
    category = category_result.scalar_one_or_none()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    _check_category_access(category.owner_id, current_user)

    product_data = body.model_dump()
    requested_owner_id = product_data.pop("owner_id", None)
    owner_id = current_user.id
    if current_user.is_superadmin and requested_owner_id is not None:
        owner_id = requested_owner_id

    new_product = Product(**product_data, owner_id=owner_id)
    db.add(new_product)
    await db.flush()
    await db.refresh(new_product)
    return _product_to_dict(new_product)


@router.get("/{product_id}")
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    product = await get_product_or_404(product_id, db)
    check_resource_ownership(product.owner_id, current_user)
    return _product_to_dict(product)


@router.put("/{product_id}")
async def update_product(
    product_id: int,
    body: ProductUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Mahsulot topilmadi")

    check_resource_ownership(product.owner_id, current_user)

    update_data = body.model_dump(exclude_unset=True)
    if "description" in update_data:
        update_data["description_uz"] = update_data.pop("description")
    update_data.pop("sort_order", None)

    for key, value in update_data.items():
        setattr(product, key, value)
    await db.commit()
    await db.refresh(product)
    return _product_to_dict(product)


@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Mahsulot topilmadi")

    check_resource_ownership(product.owner_id, current_user)

    await db.delete(product)
    await db.commit()
    return {"message": f"Mahsulot #{product_id} o'chirildi"}

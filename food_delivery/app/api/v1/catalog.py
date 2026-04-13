from __future__ import annotations

import json
from urllib.parse import quote_plus

from fastapi import APIRouter, Depends, Query, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.catalog import CategoryOut, PaginatedProducts, ProductDetailOut
from app.services.catalog import CatalogService

router = APIRouter(prefix="/catalog", tags=["catalog"])

# Legacy routes kept for compatibility with existing webapp clients.
legacy_router = APIRouter(tags=["catalog"])

CATALOG_CATEGORIES_CACHE_TTL_SECONDS = 5 * 60
CATALOG_PRODUCTS_CACHE_TTL_SECONDS = 2 * 60
CATALOG_PRODUCT_DETAIL_CACHE_TTL_SECONDS = 5 * 60


def _from_cache(raw: bytes | str | None):
    if raw is None:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return json.loads(raw)


async def _to_cache(redis: Redis | None, key: str, payload: dict | list, ttl_seconds: int) -> None:
    if redis is None:
        return
    await redis.setex(key, ttl_seconds, json.dumps(payload, ensure_ascii=False))


@router.get("/categories", response_model=list[CategoryOut])
@legacy_router.get("/categories", response_model=list[CategoryOut], include_in_schema=False)
async def categories(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> list[CategoryOut]:
    redis: Redis | None = getattr(request.app.state, "redis", None)
    cache_key = "catalog:categories:v1"
    cached = _from_cache(await redis.get(cache_key)) if redis is not None else None
    if cached is not None:
        return [CategoryOut.model_validate(item) for item in cached]

    rows = await CatalogService(db).list_categories()
    payload = [item.model_dump(mode="json") for item in rows]
    await _to_cache(redis, cache_key, payload, CATALOG_CATEGORIES_CACHE_TTL_SECONDS)
    return rows


@router.get("/products", response_model=PaginatedProducts)
@legacy_router.get("/products", response_model=PaginatedProducts, include_in_schema=False)
async def products(
    request: Request,
    db: AsyncSession = Depends(get_db),
    category_id: int | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> PaginatedProducts:
    redis: Redis | None = getattr(request.app.state, "redis", None)
    normalized_search = (search or "").strip().lower()
    category_key = str(category_id) if category_id is not None else "all"
    search_key = quote_plus(normalized_search) if normalized_search else "-"
    cache_key = f"catalog:products:v1:c={category_key}:s={search_key}:p={page}:n={size}"

    cached = _from_cache(await redis.get(cache_key)) if redis is not None else None
    if cached is not None:
        return PaginatedProducts.model_validate(cached)

    data = await CatalogService(db).list_products(
        category_id=category_id,
        search=normalized_search or None,
        page=page,
        size=size,
    )
    payload = data.model_dump(mode="json")
    await _to_cache(redis, cache_key, payload, CATALOG_PRODUCTS_CACHE_TTL_SECONDS)
    return data


@router.get("/products/{product_id}", response_model=ProductDetailOut)
@legacy_router.get("/products/{product_id}", response_model=ProductDetailOut, include_in_schema=False)
async def product_detail(
    request: Request,
    product_id: int,
    db: AsyncSession = Depends(get_db),
) -> ProductDetailOut:
    redis: Redis | None = getattr(request.app.state, "redis", None)
    cache_key = f"catalog:product:{product_id}:v1"
    cached = _from_cache(await redis.get(cache_key)) if redis is not None else None
    if cached is not None:
        return ProductDetailOut.model_validate(cached)

    data = await CatalogService(db).get_product(product_id)
    payload = data.model_dump(mode="json")
    await _to_cache(redis, cache_key, payload, CATALOG_PRODUCT_DETAIL_CACHE_TTL_SECONDS)
    return data

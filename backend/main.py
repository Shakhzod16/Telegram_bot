# -*- coding: utf-8 -*-
import json
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.db import Base, SessionLocal, engine
from backend.exceptions import AppException
from backend.repositories.product_repo import ProductRepository
from backend.repositories.user_repo import UserRepository
from backend.repositories.address_repo import AddressRepository
from backend.routers import admin_router, api_router
from backend.services.bootstrap_service import BootstrapService
from config.settings import settings
from utils.logger import get_logger, setup_logging

setup_logging(settings.environment, settings.log_level)
log = get_logger("backend.main")

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="Food Delivery API", version="3.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "X-Init-Data", "X-Admin-Key", "Authorization"],
)
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="assets")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        elapsed = (time.perf_counter() - started) * 1000
        log.error(
            "HTTP %s %s -> 500 in %.2fms (exception)",
            request.method,
            request.url.path,
            elapsed,
            exc_info=True,
        )
        raise
    elapsed = (time.perf_counter() - started) * 1000
    log.info("HTTP %s %s -> %s in %.2fms", request.method, request.url.path, response.status_code, elapsed)
    return response


@app.exception_handler(AppException)
async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
    log.error("Application exception: %s", exc.message, exc_info=True)
    return JSONResponse(status_code=exc.code, content={"error": exc.message, "code": exc.code})


@app.exception_handler(HTTPException)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else "HTTP error"
    if exc.status_code == 404:
        detail = "Not found"
    log.error("HTTP exception status=%s detail=%s", exc.status_code, detail, exc_info=True)
    return JSONResponse(status_code=exc.status_code, content={"error": detail, "code": exc.status_code})


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    log.error("Unhandled API exception: %s", str(exc), exc_info=True)
    return JSONResponse(status_code=500, content={"error": "Internal server error", "code": 500})


@app.on_event("startup")
async def startup() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        bootstrap_service = BootstrapService(
            user_repo=UserRepository(session),
            product_repo=ProductRepository(session),
            address_repo=AddressRepository(session),
            cache_ttl_seconds=settings.cache_ttl_seconds,
        )
        await bootstrap_service.seed_products_if_needed()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/app-config.js")
async def app_config_js() -> Response:
    payload = {"apiBaseUrl": settings.api_base_url}
    content = f"window.APP_CONFIG = Object.assign({{}}, window.APP_CONFIG, {json.dumps(payload)});"
    return Response(content=content, media_type="application/javascript")


@app.get("/styles.css")
async def styles() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "styles.css")


@app.get("/app.js")
async def app_js() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "app.js")


app.include_router(api_router)
app.include_router(admin_router)

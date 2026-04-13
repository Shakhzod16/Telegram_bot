from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.v1.auth import router as auth_router
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import add_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.webapp.router import webapp_router

templates = Jinja2Templates(directory="app/webapp/templates")
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("application_startup")
    owns_redis = False
    redis_client = getattr(app.state, "redis", None)
    if redis_client is None:
        redis_client = Redis.from_url(
            settings.redis_url,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        app.state.redis = redis_client
        owns_redis = True
    try:
        if redis_client is not None:
            try:
                await redis_client.ping()
            except Exception:
                logger.warning("redis_unavailable")
                if owns_redis and redis_client is not None:
                    await redis_client.aclose()
                from fakeredis.aioredis import FakeRedis

                redis_client = FakeRedis(decode_responses=False)
                app.state.redis = redis_client
                owns_redis = True
                logger.warning("redis_fallback_enabled")
        yield
    finally:
        if owns_redis and redis_client is not None:
            await redis_client.aclose()
        logger.info("application_shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Food Delivery API",
        version="1.0.0",
        lifespan=lifespan,
    )

    add_exception_handlers(app)

    allowed_origins = ["*"] if settings.debug else [settings.webapp_url]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Keep both static paths for backward compatibility with existing templates/clients.
    app.mount("/static", StaticFiles(directory="app/webapp/static"), name="static")
    app.mount("/webapp/static", StaticFiles(directory="app/webapp/static"), name="webapp-static")

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": "1.0.0"}

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(api_router, prefix="/api/v1")
    app.include_router(webapp_router)

    return app


app = create_app()

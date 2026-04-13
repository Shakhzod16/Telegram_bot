from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Any:
        if request.url.path.startswith("/static") or "static" in request.url.path:
            return await call_next(request)
        redis = getattr(request.app.state, "redis", None)
        if redis is None:
            return await call_next(request)
        client = request.client.host if request.client else "unknown"
        path = request.url.path
        is_auth = path.startswith("/api/v1/auth")
        limit = 5 if is_auth else 60
        window = 60
        key = f"rl:{client}:{'auth' if is_auth else 'pub'}"
        n = await redis.incr(key)
        if n == 1:
            await redis.expire(key, window)
        if n > limit:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"success": False, "error": {"code": "rate_limit", "message": "Too many requests"}},
            )
        return await call_next(request)

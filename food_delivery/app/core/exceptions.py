from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)


class AppException(Exception):
    status_code: int = 500
    code: str = "INTERNAL_ERROR"
    message: str = "Internal server error"

    def __init__(self, message: str | None = None, *, field: str | None = None) -> None:
        self.detail = message or self.message
        self.field = field
        super().__init__(self.detail)


class NotFoundError(AppException):
    status_code = 404
    code = "NOT_FOUND"


class ValidationError(AppException):
    status_code = 422
    code = "VALIDATION_ERROR"


class UnauthorizedError(AppException):
    status_code = 401
    code = "UNAUTHORIZED"


class ForbiddenError(AppException):
    status_code = 403
    code = "FORBIDDEN"


class ConflictError(AppException):
    status_code = 409
    code = "CONFLICT"


class RateLimitError(AppException):
    status_code = 429
    code = "RATE_LIMIT"


class EmptyCartError(AppException):
    status_code = 400
    code = "EMPTY_CART"
    message = "Cart is empty"


class MinOrderAmountError(AppException):
    status_code = 400
    code = "MIN_ORDER_AMOUNT"


class BranchClosedError(AppException):
    status_code = 400
    code = "BRANCH_CLOSED"
    message = "Branch is currently closed"


class DeliveryZoneError(AppException):
    status_code = 422
    code = "DELIVERY_ZONE"
    message = "Address is outside delivery zone"


class DuplicateOrderError(AppException):
    status_code = 409
    code = "DUPLICATE_ORDER"
    message = "Order already exists"


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.warning(
        "app_exception",
        extra={
            "path": request.url.path,
            "code": exc.code,
            "detail": exc.detail,
            "field": exc.field,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.code, "field": exc.field},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "unhandled_exception",
        extra={"path": request.url.path},
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "code": "INTERNAL_ERROR", "field": None},
    )


def add_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)


class ExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Any:
        try:
            return await call_next(request)
        except AppException as exc:
            return await app_exception_handler(request, exc)
        except Exception as exc:
            return await unhandled_exception_handler(request, exc)


# Backward-compatibility aliases used by existing services.
AppError = AppException
ValidationAppError = ValidationError
OutOfDeliveryZoneError = DeliveryZoneError
app_error_handler = app_exception_handler

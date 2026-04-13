from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings

templates = Jinja2Templates(directory="app/webapp/templates")

webapp_router = APIRouter()


@webapp_router.get("/webapp/", response_class=HTMLResponse)
async def webapp_index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "backend_url": settings.BACKEND_URL.rstrip("/"), "active": "home"},
    )


@webapp_router.get("/webapp/cart", response_class=HTMLResponse)
async def webapp_cart(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "cart.html",
        {"request": request, "backend_url": settings.BACKEND_URL.rstrip("/"), "active": "cart"},
    )


@webapp_router.get("/webapp/checkout", response_class=HTMLResponse)
async def webapp_checkout(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "checkout.html",
        {"request": request, "backend_url": settings.BACKEND_URL.rstrip("/"), "active": "cart"},
    )


@webapp_router.get("/webapp/orders", response_class=HTMLResponse)
async def webapp_orders(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "orders.html",
        {"request": request, "backend_url": settings.BACKEND_URL.rstrip("/"), "active": "orders"},
    )


@webapp_router.get("/webapp/orders/{order_id}", response_class=HTMLResponse)
async def webapp_order_detail(request: Request, order_id: int) -> HTMLResponse:
    return templates.TemplateResponse(
        "order_detail.html",
        {
            "request": request,
            "backend_url": settings.BACKEND_URL.rstrip("/"),
            "order_id": order_id,
            "active": "orders",
        },
    )


@webapp_router.get("/webapp/profile", response_class=HTMLResponse)
async def webapp_profile(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "backend_url": settings.BACKEND_URL.rstrip("/"), "active": "profile"},
    )


@webapp_router.get("/webapp/address", response_class=HTMLResponse)
async def webapp_address(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "address.html",
        {"request": request, "backend_url": settings.BACKEND_URL.rstrip("/"), "active": "profile"},
    )


@webapp_router.get("/webapp/admin", response_class=HTMLResponse)
async def webapp_admin_dashboard(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {"request": request, "backend_url": settings.BACKEND_URL.rstrip("/")},
    )


@webapp_router.get("/webapp/admin/orders", response_class=HTMLResponse)
async def webapp_admin_orders(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "admin/orders.html",
        {"request": request, "backend_url": settings.BACKEND_URL.rstrip("/")},
    )

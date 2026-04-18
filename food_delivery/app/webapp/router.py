from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings

templates = Jinja2Templates(directory="app/webapp/templates")

webapp_router = APIRouter()

NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}


def _render(
    request: Request,
    template_name: str,
    context: dict,
) -> HTMLResponse:
    response = templates.TemplateResponse(
        template_name,
        {"request": request, **context},
    )
    for key, value in NO_CACHE_HEADERS.items():
        response.headers[key] = value
    return response


@webapp_router.get("/", include_in_schema=False)
async def root_redirect() -> RedirectResponse:
    return RedirectResponse(url="/webapp/", status_code=307)


@webapp_router.get("/webapp", include_in_schema=False)
async def webapp_redirect() -> RedirectResponse:
    return RedirectResponse(url="/webapp/", status_code=307)


@webapp_router.get("/webapp/", response_class=HTMLResponse)
async def webapp_index(request: Request) -> HTMLResponse:
    return _render(
        request,
        "index.html",
        {"backend_url": settings.BACKEND_URL.rstrip("/"), "active": "home"},
    )


@webapp_router.get("/webapp/cart", response_class=HTMLResponse)
async def webapp_cart(request: Request) -> HTMLResponse:
    return _render(
        request,
        "cart.html",
        {"backend_url": settings.BACKEND_URL.rstrip("/"), "active": "cart"},
    )


@webapp_router.get("/webapp/checkout", response_class=HTMLResponse)
async def webapp_checkout(request: Request) -> HTMLResponse:
    return _render(
        request,
        "checkout.html",
        {"backend_url": settings.BACKEND_URL.rstrip("/"), "active": "cart"},
    )


@webapp_router.get("/webapp/map", response_class=HTMLResponse)
async def webapp_map(request: Request) -> HTMLResponse:
    return _render(
        request,
        "map.html",
        {"backend_url": settings.BACKEND_URL.rstrip("/"), "active": "cart"},
    )


@webapp_router.get("/webapp/orders", response_class=HTMLResponse)
async def webapp_orders(request: Request) -> HTMLResponse:
    return _render(
        request,
        "orders.html",
        {"backend_url": settings.BACKEND_URL.rstrip("/"), "active": "orders"},
    )


@webapp_router.get("/webapp/orders/{order_id}", response_class=HTMLResponse)
async def webapp_order_detail(request: Request, order_id: int) -> HTMLResponse:
    return _render(
        request,
        "order_detail.html",
        {
            "backend_url": settings.BACKEND_URL.rstrip("/"),
            "order_id": order_id,
            "active": "orders",
        },
    )


@webapp_router.get("/webapp/profile", response_class=HTMLResponse)
async def webapp_profile(request: Request) -> HTMLResponse:
    return _render(
        request,
        "profile.html",
        {"backend_url": settings.BACKEND_URL.rstrip("/"), "active": "profile"},
    )


@webapp_router.get("/webapp/address", response_class=HTMLResponse)
async def webapp_address(request: Request) -> HTMLResponse:
    return RedirectResponse(url="/webapp/map", status_code=307)


@webapp_router.get("/webapp/admin", response_class=HTMLResponse)
async def webapp_admin_dashboard(request: Request) -> HTMLResponse:
    return _render(
        request,
        "admin/dashboard.html",
        {"backend_url": settings.BACKEND_URL.rstrip("/"), "active": "dashboard"},
    )


@webapp_router.get("/webapp/admin/orders", response_class=HTMLResponse)
async def webapp_admin_orders(request: Request) -> HTMLResponse:
    return _render(
        request,
        "admin/orders.html",
        {"backend_url": settings.BACKEND_URL.rstrip("/"), "active": "orders"},
    )


@webapp_router.get("/webapp/admin/products/new", response_class=HTMLResponse)
async def webapp_admin_product_new(request: Request) -> HTMLResponse:
    return _render(
        request,
        "admin/product_new.html",
        {"backend_url": settings.BACKEND_URL.rstrip("/"), "active": "products"},
    )


@webapp_router.get("/webapp/admin/broadcast", response_class=HTMLResponse)
async def webapp_admin_broadcast(request: Request) -> HTMLResponse:
    return _render(
        request,
        "admin/broadcast.html",
        {"backend_url": settings.BACKEND_URL.rstrip("/"), "active": "broadcast"},
    )

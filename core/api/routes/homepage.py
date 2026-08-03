from importlib.resources import files

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, Response

from core.dashboard.api import DashboardAPI
from core.homepage.projection import apply_standalone_contract
from core.homepage.status import HomepageStatusService


router = APIRouter()

homepage = HomepageStatusService()
dashboard = DashboardAPI()


def _ui_asset(name: str) -> str:
    return (
        files("core.homepage.ui")
        .joinpath(name)
        .read_text(encoding="utf-8")
    )


@router.get(
    "/homepage",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def homepage_browser() -> str:
    """Serve the internal, read-only operator Homepage."""
    return _ui_asset("index.html")


@router.get(
    "/homepage/assets/homepage.css",
    include_in_schema=False,
)
def homepage_styles() -> Response:
    return Response(_ui_asset("homepage.css"), media_type="text/css")


@router.get(
    "/homepage/assets/homepage.js",
    include_in_schema=False,
)
def homepage_script() -> Response:
    return Response(
        _ui_asset("homepage.js"),
        media_type="application/javascript",
    )


@router.get(
    "/homepage/product-management",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def product_management_browser() -> str:
    """Serve the internal, read-only ProductDraft console."""
    return _ui_asset("product-management.html")


@router.get(
    "/homepage/assets/product-management.css",
    include_in_schema=False,
)
def product_management_styles() -> Response:
    return Response(_ui_asset("product-management.css"), media_type="text/css")


@router.get(
    "/homepage/assets/product-management.js",
    include_in_schema=False,
)
def product_management_script() -> Response:
    return Response(
        _ui_asset("product-management.js"),
        media_type="application/javascript",
    )


@router.get("/homepage/status")
def homepage_status():
    return apply_standalone_contract(
        homepage.status(),
        dashboard.status(["ubuntu-main"]),
    )

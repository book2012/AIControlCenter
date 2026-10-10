from importlib.resources import files
from pathlib import Path
import re

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, Response

from core.dashboard.api import DashboardAPI
from core.homepage.projection import apply_standalone_contract
from core.homepage.status import HomepageStatusService
from core.homepage import storefront, storefront_media
from core.api.dependencies.shopping import get_shopping_service
from core.shopping.service import ShoppingService


router = APIRouter()

homepage = HomepageStatusService()
dashboard = DashboardAPI()


def _ui_asset(name: str) -> str:
    if name.startswith("storefront") and name.endswith(".html"):
        raise ValueError("Storefront templates require the read-only presentation renderer")
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


@router.get("/homepage/storefront", response_class=HTMLResponse, include_in_schema=False)
def storefront_browser(category: str = "", q: str = "", page: str = "1", collection: str = "",
                       service: ShoppingService = Depends(get_shopping_service)) -> Response:
    """Render the unified agachichi editorial feed with shareable filters."""
    state = storefront.browse_state(category, q, page, collection)
    content, status = storefront.home(service, state)
    return HTMLResponse(content, status_code=status)


@router.get("/homepage/storefront/search", response_class=HTMLResponse, include_in_schema=False)
def storefront_search_browser(category: str = "", q: str = "", page: str = "1",
                              service: ShoppingService = Depends(get_shopping_service)) -> HTMLResponse:
    """Keep catalog discovery separate from the editorial storefront home."""
    content, status = storefront.search(service, storefront.browse_state(category, q, page))
    return HTMLResponse(content, status_code=status)


@router.get("/homepage/storefront/product/{product_id}", response_class=HTMLResponse, include_in_schema=False)
def storefront_product_browser(product_id: str, return_to: str = "",
                               service: ShoppingService = Depends(get_shopping_service)) -> HTMLResponse:
    """Use the same detail service as canonical GET /shopping/products/{id}."""
    content, status = storefront.detail(service, product_id, return_to)
    return HTMLResponse(content, status_code=status)


@router.get("/homepage/assets/storefront.css", include_in_schema=False)
def storefront_styles() -> Response:
    return Response(_ui_asset("storefront.css"), media_type="text/css")


@router.get("/homepage/assets/storefront.js", include_in_schema=False)
def storefront_script() -> Response:
    return Response(_ui_asset("storefront.js"), media_type="application/javascript")


@router.get("/homepage/assets/storefront-commerce.js", include_in_schema=False)
def storefront_commerce_script() -> Response:
    return Response(_ui_asset("storefront-commerce.js"), media_type="application/javascript")


@router.get("/homepage/assets/storefront-guest-chat.js", include_in_schema=False)
def storefront_guest_chat_script() -> Response:
    # Guest UI is versioned with the homepage release; order endpoints stay on the API.
    path = Path(__file__).resolve().parents[3] / "deploy/shopping/wordpress/plugins/ai-shopping-storefront/assets/storefront-guest-chat.js"
    return Response(path.read_text(encoding="utf-8"), media_type="application/javascript")


@router.get("/homepage/assets/storefront-chat.js", include_in_schema=False)
def storefront_chat_script() -> Response:
    return Response(_ui_asset("storefront-chat.js"), media_type="application/javascript")


@router.get("/homepage/assets/storefront/gallery/{filename}", include_in_schema=False)
def storefront_gallery_photo(filename: str) -> FileResponse:
    from core.homepage.storefront_gallery import assets
    asset=assets().get(filename)
    if asset is None:raise HTTPException(status_code=404, detail="Photo not found")
    return FileResponse(asset["path"], media_type="image/webp" if asset["path"].suffix == ".webp" else "image/jpeg")


@router.get("/homepage/assets/storefront-orders.js", include_in_schema=False)
def storefront_orders_script() -> Response:
    return Response(_ui_asset("storefront-orders.js"), media_type="application/javascript")


@router.get("/homepage/storefront/cart", response_class=HTMLResponse, include_in_schema=False)
def storefront_cart_browser(service: ShoppingService = Depends(get_shopping_service)) -> HTMLResponse:
    from core.homepage.storefront_chat import widget
    return HTMLResponse(storefront.template("storefront-cart.html").replace("</body>", widget(service) + "</body>"))


@router.get("/homepage/storefront/checkout", response_class=HTMLResponse, include_in_schema=False)
def storefront_checkout_browser() -> HTMLResponse:
    return HTMLResponse(storefront.template("storefront-checkout.html"),
        headers={"Cache-Control":"no-store","X-Robots-Tag":"noindex, nofollow"})


@router.get("/homepage/storefront/my-orders", response_class=HTMLResponse, include_in_schema=False)
def storefront_orders_browser(service: ShoppingService = Depends(get_shopping_service)) -> HTMLResponse:
    from core.homepage.storefront_chat import widget
    return HTMLResponse(storefront.template("storefront-orders.html").replace("</body>",widget(service)+"</body>"))


@router.get("/homepage/assets/storefront/hero-sunlit-home-v1.jpg", include_in_schema=False)
def storefront_sunlit_hero() -> FileResponse:
    hero = Path(__file__).resolve().parents[3] / "brands/agachichi/assets/media/storefront/hero-sunlit-home-v1.jpg"
    if not hero.is_file():
        raise HTTPException(status_code=404, detail="Hero not found")
    return FileResponse(hero, media_type="image/jpeg")


@router.get("/homepage/assets/storefront/hero-boutique.jpg", include_in_schema=False)
def storefront_hero() -> FileResponse:
    """One brand-owned local hero; no plugin deployment dependency or proxy."""
    hero = (Path(__file__).resolve().parents[3] /
            "brands/agachichi/assets/media/storefront/hero-agachichi.jpg")
    if not hero.is_file():
        raise HTTPException(status_code=404, detail="Hero not found")
    return FileResponse(hero, media_type="image/jpeg")


@router.get("/homepage/assets/storefront/photos/{category}/{filename}", include_in_schema=False)
def storefront_photo(category: str, filename: str) -> FileResponse:
    """Read only repository demo JPEGs; never proxy or contact a CMS host."""
    if category not in {"top", "bottom", "outer", "dress", "bag", "acc"} or not re.fullmatch(
        rf"oc-demo-{category}-[0-9]{{4}}\.jpg", filename
    ):
        raise HTTPException(status_code=404, detail="Photo not found")
    root = (Path(__file__).resolve().parents[3] / "deploy/shopping/wordpress/plugins/"
            "ai-shopping-storefront/assets/demo/orange-coco-v1/products").resolve()
    photo = (root / category / filename).resolve()
    if not photo.is_relative_to(root) or not photo.is_file():
        raise HTTPException(status_code=404, detail="Photo not found")
    return FileResponse(photo, media_type="image/jpeg")


@router.get("/homepage/assets/storefront/catalog/{category}/{filename}", include_in_schema=False)
def storefront_catalog_photo(category: str, filename: str) -> FileResponse:
    """Serve only manifest-approved brand-owned JPEGs. No remote resolution."""
    asset = storefront_media.assets().get(filename.removesuffix(".jpg"))
    if not asset or asset["category"] != category or asset["path"].name != filename:
        raise HTTPException(status_code=404, detail="Photo not found")
    return FileResponse(asset["path"], media_type="image/jpeg")


@router.get("/homepage/status")
def homepage_status():
    return apply_standalone_contract(
        homepage.status(),
        dashboard.status(["ubuntu-main"]),
    )

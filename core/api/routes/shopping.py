import json
import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute

from core.api.dependencies.shopping import (
    get_product_draft_query_service,
    get_shopping_service,
)

from core.shopping.schemas import (
    ProductSearchResponse,
    FeaturedProductListResponse,
    ShoppingCategoryListResponse,
    ProductListResponse,
    ProductResponse,
    ProductReadErrorResponse,
    ShoppingCapabilitiesResponse,
    ShoppingHealthResponse,
    ShoppingReadPathHealthResponse,
    ShoppingIntegrationResponse,
    ShoppingReadinessResponse,
)
from core.shopping.service import (
    ProductNotFoundError,
    ShoppingService,
)
from core.shopping.ports import CatalogReadQueryError, CatalogReadUnavailable
from core.shopping.inquiries import (InquiryCreateRequest, InquiryMessageRequest, InquiryRepository,
                                     InquiryResponse, configured_contact_channels, sanitize_message)
from core.api.dependencies.inquiries import get_inquiry_repository
from core.api.dependencies.inquiries import (
    OwnedInquiryRoute, get_owned_inquiry_authority, get_owned_inquiry_repository,
)
from core.shopping.inquiries import InquirySessionAuthority, OwnedInquiryMessageRequest, SQLiteInquiryRepository
from core.shopping.customer_persistence import AuthorizationConflict, PersistenceError
from core.shopping.product_drafts.read import (
    ProductDraftQueryService,
    ProductDraftReadUnavailable,
    ProductDraftRevisionNotFound,
)


router = APIRouter(
    prefix="/shopping",
    tags=["shopping"],
)

ProductDraftQuery = Annotated[ProductDraftQueryService, Depends(get_product_draft_query_service)]
ShoppingCatalog = Annotated[ShoppingService, Depends(get_shopping_service)]
InquiryStore = Annotated[InquiryRepository, Depends(get_inquiry_repository)]


class ProductJSONResponse(JSONResponse):
    """Stable UTF-8 JSON for the existing AIControlCenter product contract."""

    def render(self, content: object) -> bytes:
        return json.dumps(content, ensure_ascii=False, allow_nan=False,
                          sort_keys=True, separators=(",", ":")).encode("utf-8")


class CatalogReadRoute(APIRoute):
    """Keep framework query errors within the deterministic product contract."""

    def get_route_handler(self):
        handler = super().get_route_handler()

        async def handle(request):
            try:
                return await handler(request)
            except RequestValidationError:
                return _catalog_error(CatalogReadQueryError())

        return handle


def _catalog_error(error: Exception) -> ProductJSONResponse:
    if isinstance(error, CatalogReadQueryError):
        return ProductJSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                                   content={"detail": {"code": "shopping_invalid_product_query"}})
    return ProductJSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                               content={"detail": {"code": "shopping_catalog_unavailable"}})


def _product_draft_error(error: Exception) -> HTTPException:
    if isinstance(error, ProductDraftReadUnavailable):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                             detail={"code": "product_draft_read_unavailable", "retryable": True})
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                         detail={"code": "product_draft_revision_not_found"})


@router.get("/product-drafts")
def product_draft_collection(
    service: ProductDraftQuery,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    lifecycle_state: str | None = Query(default=None),
):
    try:
        return service.list_revisions(page=page, page_size=page_size, lifecycle_state=lifecycle_state)
    except ProductDraftReadUnavailable as error:
        raise _product_draft_error(error) from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                            detail={"code": "product_draft_invalid_query"}) from error


@router.get("/product-drafts/{draft_id}")
def product_draft_current(draft_id: str, service: ProductDraftQuery):
    try:
        return service.current_revision(draft_id)
    except (ProductDraftReadUnavailable, ProductDraftRevisionNotFound) as error:
        raise _product_draft_error(error) from error


@router.get("/product-drafts/{draft_id}/revisions/{revision_id}")
def product_draft_revision(draft_id: str, revision_id: str, service: ProductDraftQuery):
    try:
        return service.exact_revision(draft_id, revision_id)
    except (ProductDraftReadUnavailable, ProductDraftRevisionNotFound) as error:
        raise _product_draft_error(error) from error


@router.get(
    "/health",
    response_model=ShoppingHealthResponse,
)
def shopping_health(service: ShoppingCatalog):
    return service.health()


@router.get(
    "/health/read-path",
    response_model=ShoppingReadPathHealthResponse,
    response_class=ProductJSONResponse,
    responses={503: {"model": ShoppingReadPathHealthResponse}},
)
def shopping_read_path_health(service: ShoppingCatalog):
    result = service.read_path_health()
    return ProductJSONResponse(content=result, status_code=200 if result["healthy"] else 503)


@router.get(
    "/readiness",
    response_model=ShoppingReadinessResponse,
)
def shopping_readiness(service: ShoppingCatalog):
    return service.readiness()


@router.get(
    "/capabilities",
    response_model=ShoppingCapabilitiesResponse,
)
def shopping_capabilities(service: ShoppingCatalog):
    return service.capabilities()



@router.get(
    "/integrations",
    response_model=ShoppingIntegrationResponse,
)
def shopping_integrations(service: ShoppingCatalog):
    return service.integration_status()





@router.get(
    "/search",
    response_model=ProductSearchResponse,
)
def shopping_search(
    service: ShoppingCatalog,
    q: str | None = Query(
        default=None,
        min_length=1,
        max_length=200,
    ),
    category: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    minimum_price: float | None = Query(
        default=None,
        ge=0,
    ),
    maximum_price: float | None = Query(
        default=None,
        ge=0,
    ),
    in_stock: bool | None = Query(
        default=None,
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
):
    if (
        minimum_price is not None
        and maximum_price is not None
        and minimum_price > maximum_price
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "shopping_invalid_price_range",
                "minimum_price": minimum_price,
                "maximum_price": maximum_price,
            },
        )

    return service.search_products(
        query=q,
        category=category,
        minimum_price=minimum_price,
        maximum_price=maximum_price,
        in_stock=in_stock,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/featured-products",
    response_model=FeaturedProductListResponse,
)
def shopping_featured_products(
    service: ShoppingCatalog,
    limit: int = Query(
        default=4,
        ge=1,
        le=20,
    ),
):
    return service.list_featured_products(
        limit=limit,
    )


@router.get(
    "/categories",
    response_model=ShoppingCategoryListResponse,
)
def shopping_categories(service: ShoppingCatalog):
    return service.list_categories()


def shopping_products(
    service: ShoppingCatalog,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    try:
        return service.list_products(page=page, page_size=page_size)
    except (CatalogReadQueryError, CatalogReadUnavailable) as error:
        return _catalog_error(error)


def shopping_product(product_id: str, service: ShoppingCatalog):
    try:
        return service.get_product(product_id)
    except (CatalogReadQueryError, CatalogReadUnavailable) as error:
        return _catalog_error(error)
    except ProductNotFoundError as error:
        return ProductJSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": {
                "code": "shopping_product_not_found",
                "product_id": str(error),
            }},
        )


# Apply canonical validation errors only to the public product reads.
router.add_api_route(
    "/products", shopping_products, methods=["GET"],
    response_model=ProductListResponse, response_class=ProductJSONResponse,
    route_class_override=CatalogReadRoute,
    responses={422: {"model": ProductReadErrorResponse}, 503: {"model": ProductReadErrorResponse}},
)


@router.get("/contact-channels")
def contact_channels():
    return {"items": configured_contact_channels()}


@router.post("/inquiries", response_model=InquiryResponse)
def create_inquiry(request: InquiryCreateRequest, service: ShoppingCatalog, repository: InquiryStore):
    try:
        product = service.get_product(request.product_id)
    except ProductNotFoundError:
        raise HTTPException(status_code=404, detail={"code": "shopping_product_not_found", "product_id": request.product_id}) from None
    except (CatalogReadQueryError, CatalogReadUnavailable):
        raise HTTPException(status_code=503, detail={"code": "shopping_catalog_unavailable"}) from None
    variants = getattr(product, "get", lambda key, default=None: default)("variants", []) or []
    variant = next((item for item in variants if item["id"] == request.variant_id), None) if request.variant_id else None
    if variants and request.variant_id is None:
        raise HTTPException(status_code=422, detail={"code": "shopping_variant_required"})
    if request.variant_id and variant is None:
        raise HTTPException(status_code=422, detail={"code": "shopping_invalid_variant"})
    if variant and not variant["available"]:
        raise HTTPException(status_code=422, detail={"code": "shopping_variant_unavailable"})
    from core.shopping.models import ProductVariant, Product
    canonical_variant = ProductVariant(**variant) if variant else None
    canonical_product = Product(**{key: product[key] for key in Product.__dataclass_fields__})
    return repository.create(canonical_product, canonical_variant, sanitize_message(request.message))


@router.get("/inquiries/{inquiry_id}", response_model=InquiryResponse)
def get_inquiry(inquiry_id: str, request: Request, repository: InquiryStore):
    result = _legacy_inquiry(repository, inquiry_id, _customer_token(request))
    if result is None:
        raise HTTPException(status_code=403, detail={"code": "inquiry_access_denied"})
    if not re.fullmatch(r"AG-INQ-[0-9]{6,18}", inquiry_id):
        raise HTTPException(status_code=404, detail={"code": "inquiry_not_found"})
    return result.model_copy(update={"public_access_token": None})


def _legacy_inquiry(repository, inquiry_id, token):
    try:
        return repository.get_legacy_authorized(inquiry_id, token)
    except (PersistenceError, ValueError):
        raise HTTPException(status_code=503, detail={"code": "inquiry_storage_unavailable"}) from None


def _customer_token(request) -> str:
    token = request.headers.get("x-inquiry-access-token", "")
    if not token or len(token) > 256:
        raise HTTPException(status_code=401, detail={"code": "inquiry_access_required"})
    return token


@router.post("/inquiries/{inquiry_id}/messages")
def create_customer_message(inquiry_id: str, body: InquiryMessageRequest, request: Request, repository: InquiryStore):
    token = _customer_token(request)
    try:
        result = repository.append_legacy_authorized(inquiry_id, token, body.body)
    except (PersistenceError, ValueError):
        raise HTTPException(status_code=503, detail={"code": "inquiry_storage_unavailable"}) from None
    if result is None:
        raise HTTPException(status_code=403, detail={"code": "inquiry_access_denied"})
    return result


@router.get("/inquiries/{inquiry_id}/messages")
def customer_messages(inquiry_id: str, request: Request, repository: InquiryStore):
    result = _legacy_inquiry(repository, inquiry_id, _customer_token(request))
    if result is None:
        raise HTTPException(status_code=403, detail={"code": "inquiry_access_denied"})
    return {"items": result.messages}


def _operator(request: Request):
    import os
    expected = os.getenv("AICC_OPERATOR_TOKEN", "")
    supplied = request.headers.get("authorization", "")
    if not expected or supplied != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail={"code": "operator_authorization_required"})


@router.get("/operator/inquiries")
def operator_inquiries(request: Request, repository: InquiryStore):
    _operator(request)
    return {"items": [item.model_copy(update={"public_access_token": None}) for item in repository.list()]}


@router.get("/operator/inquiries/{inquiry_id}")
def operator_inquiry(inquiry_id: str, request: Request, repository: InquiryStore):
    _operator(request)
    result = repository.get(inquiry_id)
    if result is None: raise HTTPException(status_code=404, detail={"code": "inquiry_not_found"})
    return result.model_copy(update={"public_access_token": None})


@router.post("/operator/inquiries/{inquiry_id}/messages")
def operator_message(inquiry_id: str, body: InquiryMessageRequest, request: Request, repository: InquiryStore):
    _operator(request)
    try:
        result = repository.append_message(inquiry_id, body.body, "operator")
    except AuthorizationConflict:
        raise HTTPException(status_code=409, detail={"code": "owned_inquiry_versioned_mutation_required"}) from None
    except (PersistenceError, ValueError):
        raise HTTPException(status_code=503, detail={"code": "inquiry_storage_unavailable"}) from None
    if result is None: raise HTTPException(status_code=404, detail={"code": "inquiry_not_found"})
    return result
router.add_api_route(
    "/products/{product_id}", shopping_product, methods=["GET"],
    response_model=ProductResponse, response_class=ProductJSONResponse,
    route_class_override=CatalogReadRoute,
    responses={code: {"model": ProductReadErrorResponse} for code in (404, 422, 503)},
)


# Explicit isolated opt-in only. The default app includes `router`, never this
# router. Importing this module provisions no owned store or authentication.
owned_inquiry_router = APIRouter(prefix="/shopping/owned-inquiries", tags=["owned-inquiries"],
                                 route_class=OwnedInquiryRoute)
OwnedStore = Annotated[SQLiteInquiryRepository, Depends(get_owned_inquiry_repository)]
OwnedAuthority = Annotated[InquirySessionAuthority, Depends(get_owned_inquiry_authority)]


def _owned_projection(item, version):
    return {"inquiry": item.model_dump(exclude={"public_access_token"}), "version": version}


@owned_inquiry_router.post("", status_code=201)
def create_owned_inquiry(body: InquiryCreateRequest, authority: OwnedAuthority,
                         repository: OwnedStore, service: ShoppingCatalog):
    item, version = repository.create_owned(body, authority=authority, product_loader=service.get_product)
    return _owned_projection(item, version)


@owned_inquiry_router.get("/{inquiry_id}")
def owned_inquiry_detail(inquiry_id: str, authority: OwnedAuthority, repository: OwnedStore):
    return _owned_projection(*repository.get_owned(inquiry_id, authority=authority))


@owned_inquiry_router.get("/{inquiry_id}/messages")
def owned_inquiry_messages(inquiry_id: str, authority: OwnedAuthority, repository: OwnedStore):
    item, version = repository.get_owned(inquiry_id, authority=authority)
    return {"items": [message.model_dump() for message in item.messages], "version": version}


@owned_inquiry_router.post("/{inquiry_id}/messages")
def append_owned_inquiry_message(inquiry_id: str, body: OwnedInquiryMessageRequest,
                                 authority: OwnedAuthority, repository: OwnedStore):
    message = repository.append_owned_message(inquiry_id, body, authority=authority)
    return {"message": message.model_dump(), "version": body.expected_version + 1}

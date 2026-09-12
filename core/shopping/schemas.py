from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from core.shopping.observability.health_probe import HealthFailureCode, HealthState


class ShoppingHealthResponse(BaseModel):
    service: str
    status: str
    environment: str
    runtime: str
    deployment_target: str
    control_plane: str
    write_mode: str


class ShoppingReadPathHealthResponse(BaseModel):
    service: str
    healthy: bool
    state: HealthState
    failure_code: HealthFailureCode
    read_only: bool


class ShoppingReadinessChecks(BaseModel):
    enabled: bool
    write_mode_supported: bool
    safe_default_mode: bool
    deployment_target_configured: bool


class ShoppingReadinessResponse(BaseModel):
    service: str
    ready: bool
    status: str
    checks: ShoppingReadinessChecks


class ShoppingCapabilitiesResponse(BaseModel):
    service: str
    read_catalog: bool
    write_catalog: bool
    generate_ai_content: bool
    execute_automation: bool
    approval_required: bool
    configured_write_mode: str
    write_executor_available: bool
    production_mutation_authorized: bool


class ProductResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    price: Decimal = Field(ge=0, allow_inf_nan=False)
    currency: str
    category: str
    in_stock: bool
    source: str
    image_url: str | None = None

class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)


class ProductReadErrorDetail(BaseModel):
    code: Literal["shopping_invalid_product_query", "shopping_catalog_unavailable",
                  "shopping_product_not_found"]
    product_id: str | None = None


class ProductReadErrorResponse(BaseModel):
    detail: ProductReadErrorDetail


class ShoppingIntegrationResponse(BaseModel):
    catalog_adapter: str
    configured: bool
    read_only: bool
    source: str


class ShoppingCategoryResponse(BaseModel):
    id: str
    name: str
    slug: str
    count: int


class ShoppingCategoryListResponse(BaseModel):
    items: list[ShoppingCategoryResponse]
    total: int


class FeaturedProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    available_catalog_total: int
    limit: int
    strategy: str


class FeaturedProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    available_catalog_total: int
    limit: int
    strategy: str


class ProductSearchFilters(BaseModel):
    query: str | None = None
    category: str | None = None
    minimum_price: float | None = None
    maximum_price: float | None = None
    in_stock: bool | None = None


class ProductSearchResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int
    filters: ProductSearchFilters

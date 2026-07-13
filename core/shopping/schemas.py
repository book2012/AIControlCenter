from decimal import Decimal

from pydantic import BaseModel, Field


class ShoppingHealthResponse(BaseModel):
    service: str
    status: str
    environment: str
    runtime: str
    deployment_target: str
    control_plane: str
    write_mode: str


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


class ProductResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    price: Decimal
    currency: str
    category: str
    in_stock: bool
    source: str
    image_url: str | None = None

class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)


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

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


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)

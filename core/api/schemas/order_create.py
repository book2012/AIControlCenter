"""Closed public request/response schemas for isolated Order create composition."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

_CATALOG_ID=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$"
_IDEMPOTENCY=r"^[A-Za-z0-9_-]{1,128}$"


class OrderCreateLineRequest(BaseModel):
    model_config=ConfigDict(extra="forbid")
    product_id: str=Field(strict=True,pattern=_CATALOG_ID)
    variation_id: str | None=Field(default=None,strict=True,pattern=_CATALOG_ID)
    quantity: int=Field(default=1,strict=True,ge=1,le=1000)


class OrderCreateRequest(BaseModel):
    model_config=ConfigDict(extra="forbid")
    line_items: tuple[OrderCreateLineRequest,...]=Field(min_length=1,max_length=100)
    idempotency_key: str=Field(strict=True,pattern=_IDEMPOTENCY)


class OrderCreateLineProjection(BaseModel):
    model_config=ConfigDict(extra="forbid")
    product_id: str
    variation_id: str | None
    quantity: int


class OrderCreateProjection(BaseModel):
    model_config=ConfigDict(extra="forbid")
    order_number: str
    status: str
    currency: str
    total: str
    line_items: tuple[OrderCreateLineProjection,...]


class OrderCreateResponse(BaseModel):
    model_config=ConfigDict(extra="forbid")
    order: OrderCreateProjection
    idempotent_replay: bool


__all__=("OrderCreateLineRequest","OrderCreateProjection","OrderCreateRequest","OrderCreateResponse")

"""Bounded public order-create result; internal identity/audit stay private."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class OrderCreateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    outcome: Literal["COMPLETED"] = "COMPLETED"
    provider_order_id: int = Field(gt=0)
    status: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    currency: str = Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    total: str = Field(min_length=1, max_length=128, pattern=r"^[0-9]+(?:\.[0-9]+)?$")
    total_tax: str = Field(min_length=1, max_length=128, pattern=r"^[0-9]+(?:\.[0-9]+)?$")
    idempotent_replay: bool

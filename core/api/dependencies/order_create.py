"""Isolated SHOP_ORDER_001C composition; no route or runtime registration.

The existing session boundary owns credentials, durable session validity,
origin and CSRF. Only its authenticated output supplies customer/session IDs.
Explicit injection is required; there are no credential, writer or DB defaults.
"""
from datetime import timedelta
import uuid

from fastapi import Request
from pydantic import BaseModel, ConfigDict, Field

from core.api.dependencies.customer_session import CustomerSessionBoundary
from core.shopping.order_core import (
    OrderCreateAuthority, OrderCreateCommand, OrderCreateLine,
    OrderCreateResult, OrderCreateService,
)


class OrderCreateIntentLine(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, revalidate_instances="always",
                              hide_input_in_errors=True)
    product_id: str = Field(strict=True, min_length=1, max_length=128,
                            pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    variation_id: str | None = Field(default=None, strict=True, min_length=1,
                                      max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    quantity: int = Field(default=1, strict=True, ge=1, le=1000)


class OrderCreateIntent(BaseModel):
    """Browser intent only; identity, timestamps and audit are server-owned."""
    model_config = ConfigDict(extra="forbid", frozen=True, revalidate_instances="always",
                              hide_input_in_errors=True)
    line_items: tuple[OrderCreateIntentLine, ...] = Field(min_length=1, max_length=100)
    idempotency_key: str = Field(strict=True, min_length=1, max_length=128,
                                 pattern=r"^[A-Za-z0-9_-]+$")


class SessionBoundOrderCreateApplication:
    """Internal isolated composition, never mounted by the production app.

    The injected order service requires an explicit governed writer composition.
    Passing a public SafeSessionProjection or internal authority is not an API.
    """
    def __init__(self, *, session_boundary: CustomerSessionBoundary,
                 order_service: OrderCreateService):
        if type(session_boundary) is not CustomerSessionBoundary:
            raise TypeError("an existing CustomerSessionBoundary is required")
        if type(order_service) is not OrderCreateService:
            raise TypeError("an explicit OrderCreateService is required")
        self._boundary = session_boundary
        self._orders = order_service

    def execute(self, request: Request, intent: OrderCreateIntent) -> OrderCreateResult:
        if type(intent) is not OrderCreateIntent:
            raise TypeError("an OrderCreateIntent is required")
        # Revalidation also closes model_construct/model_copy bypasses.
        intent = OrderCreateIntent.model_validate(intent)
        authority = self._authenticate(request, write=True)
        command = OrderCreateCommand(
            customer_id=authority.customer_id,
            line_items=tuple(OrderCreateLine(line.product_id, line.variation_id, line.quantity)
                             for line in intent.line_items),
            idempotency_key=intent.idempotency_key,
            correlation_id="order-corr-" + uuid.uuid4().hex,
            audit_reference="order-audit-" + uuid.uuid4().hex,
            requested_at=authority.authorized_at,
        )
        return self._orders.execute(command, authority)

    def operation_status(self, request: Request, key: str):
        return self._orders.operation_status(key, self._authenticate(request, write=False))

    def _authenticate(self, request: Request, *, write: bool):
        boundary = self._boundary
        boundary.check_origin(request, required=write)
        now = boundary.now()
        secret = boundary.cookie_secret(request)
        authenticated = boundary.authenticate(secret, now=now)
        boundary.check_csrf(request, secret, authenticated)
        authority = OrderCreateAuthority(
            customer_id=authenticated.customer_id,
            session_id=authenticated.id,
            authorization_reference="order-auth-" + uuid.uuid4().hex,
            authorized_at=now,
            expires_at=min(authenticated.idle_expires_at,
                           authenticated.absolute_expires_at, now + timedelta(seconds=30)),
        )
        return authority

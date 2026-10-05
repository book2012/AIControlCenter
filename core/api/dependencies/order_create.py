"""Explicit opt-in customer-session authority for Order create routes."""
from __future__ import annotations

from typing import Annotated
import uuid

from fastapi import Depends, Request

from core.api.dependencies.customer_session import (
    CustomerSessionBoundary, get_customer_session_boundary,
)
from core.shopping.order_core import OrderCreateAuthority, OrderCreateService


class OrderCreateAPIUnavailable(RuntimeError):
    pass


def get_order_create_service() -> OrderCreateService:
    """No default runtime composition; tests/operators must explicitly inject."""
    raise OrderCreateAPIUnavailable("order create service is not composed")


def get_order_create_authority(
    request: Request,
    boundary: Annotated[CustomerSessionBoundary, Depends(get_customer_session_boundary)],
) -> OrderCreateAuthority:
    boundary.check_origin(request, required=True)
    secret=boundary.cookie_secret(request)
    now=boundary.now()
    projection=boundary.authenticate(secret, now=now)
    boundary.check_csrf(request, secret, projection)
    expires_at=min(projection.idle_expires_at, projection.absolute_expires_at)
    return OrderCreateAuthority(
        customer_id=projection.customer_id,
        session_id=projection.id,
        authorization_reference="order-auth-"+uuid.uuid4().hex,
        authorized_at=now,
        expires_at=expires_at,
    )


__all__=("OrderCreateAPIUnavailable","get_order_create_authority","get_order_create_service")

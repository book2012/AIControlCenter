"""Unregistered order-create HTTP contract for isolated fake-writer tests only.

Importing this module provides no runtime, database, credential or write adapter.
The production app does not include this router; injection is fail-closed.
"""
from typing import Annotated
import sqlite3

from fastapi import APIRouter, Depends, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from core.api.dependencies.customer_session import COOKIE_NAME, SessionAPIDenied
from core.api.dependencies.order_create import OrderCreateIntent, SessionBoundOrderCreateApplication
from core.api.schemas.customer_sessions import SessionAPIError
from core.api.schemas.order_create import OrderCreateResponse
from core.shopping.order_core import (
    OrderCreateAmbiguousFailure, OrderCreateCatalogResolutionError,
    OrderCreateContractError, OrderCreateDefinitiveFailure, OrderCreateOperationConflict,
    OrderCreateOperationInFlight, OrderCreateOperationTerminalFailure,
    OrderCreateOperationUnknownOutcome, OrderLedgerError,
)
from core.shopping.customer_persistence import PersistenceError
from core.shopping.customer_session_service import SessionServiceError


MAX_REQUEST_BYTES = 32768
_ERRORS = {
    "invalid_request": (422, "Invalid order request."),
    "denied": (401, "Customer session denied."),
    "origin_denied": (403, "Request origin denied."),
    "csrf_denied": (403, "Request verification denied."),
    "conflict": (409, "Order operation conflicts."),
    "in_flight": (409, "Order operation is already claimed."),
    "unknown_outcome": (409, "Order outcome requires reconciliation."),
    "terminal_failed": (409, "Order operation failed terminally."),
    "catalog_rejected": (422, "Order catalog intent rejected."),
    "provider_rejected": (422, "Order creation rejected."),
    "unavailable": (503, "Order service unavailable."),
    "internal_error": (500, "Order request failed."),
    "method_denied": (405, "Request method denied."),
    "request_too_large": (413, "Order request is too large."),
}
_SESSION_ERRORS = {
    SessionAPIError.DENIED: "denied", SessionAPIError.ORIGIN_DENIED: "origin_denied",
    SessionAPIError.CSRF_DENIED: "csrf_denied", SessionAPIError.UNAVAILABLE: "unavailable",
}


class OrderApplicationUnavailable(RuntimeError):
    pass


def get_order_create_application() -> SessionBoundOrderCreateApplication:
    """Explicit isolated dependency override required; no default composition."""
    raise OrderApplicationUnavailable()


def _error(code: str, *, clear_cookie: bool = False) -> JSONResponse:
    status, message = _ERRORS[code]
    headers = {"Cache-Control": "no-store"}
    if status == 405: headers["Allow"] = "POST"
    response = JSONResponse(status_code=status,
        content={"detail": {"code": "order_create_" + code, "message": message}}, headers=headers)
    if clear_cookie:
        response.delete_cookie(COOKIE_NAME, path="/", secure=True, httponly=True, samesite="strict")
    return response


class OrderCreateRoute(APIRoute):
    def matches(self, scope):
        if scope["type"] == "http" and scope["path"].endswith("/"):
            scope = {**scope, "path": scope["path"].rstrip("/")}
        return super().matches(scope)

    async def handle(self, scope, receive, send):
        if self.methods and scope["method"] not in self.methods:
            await _error("method_denied")(scope, receive, send)
            return
        await super().handle(scope, receive, send)

    def get_route_handler(self):
        handler = super().get_route_handler()
        async def bounded(request: Request):
            try:
                # Bound actual streamed bytes, not the untrusted Content-Length.
                body = bytearray()
                async for chunk in request.stream():
                    if len(body) + len(chunk) > MAX_REQUEST_BYTES:
                        return _error("request_too_large")
                    body.extend(chunk)
                # Starlette body cache lets FastAPI parse this same bounded body.
                request._body = bytes(body)
                response = await handler(request)
            except SessionAPIDenied as exc:
                response = _error(_SESSION_ERRORS.get(exc.code, "denied"), clear_cookie=exc.clear_cookie)
            except OrderCreateCatalogResolutionError:
                response = _error("catalog_rejected")
            except OrderCreateContractError as exc:
                response = _error("unknown_outcome" if str(exc).startswith("order_creator:") else "invalid_request")
            except RequestValidationError:
                response = _error("invalid_request")
            except OrderCreateOperationConflict:
                response = _error("conflict")
            except OrderCreateOperationInFlight:
                response = _error("in_flight")
            except (OrderCreateOperationUnknownOutcome, OrderCreateAmbiguousFailure):
                response = _error("unknown_outcome")
            except OrderCreateOperationTerminalFailure:
                response = _error("terminal_failed")
            except OrderCreateDefinitiveFailure:
                response = _error("provider_rejected")
            except (OrderApplicationUnavailable, OrderLedgerError, sqlite3.Error,
                    PersistenceError, SessionServiceError):
                response = _error("unavailable")
            except Exception:
                response = _error("internal_error")
            response.headers["Cache-Control"] = "no-store"
            return response
        return bounded


router = APIRouter(prefix="/shopping", tags=["isolated-order-create"], route_class=OrderCreateRoute)
Application = Annotated[SessionBoundOrderCreateApplication, Depends(get_order_create_application)]


@router.post("/orders", response_model=OrderCreateResponse, status_code=201)
def create_order(payload: OrderCreateIntent, request: Request, application: Application):
    result = application.execute(request, payload)
    snapshot = result.snapshot
    response = OrderCreateResponse(
        provider_order_id=snapshot.provider_order_id, status=snapshot.status,
        currency=snapshot.currency, total=format(snapshot.total, "f"),
        total_tax=format(snapshot.total_tax, "f"), idempotent_replay=result.idempotent_replay,
    )
    return JSONResponse(status_code=200 if result.idempotent_replay else 201,
                        content=response.model_dump(mode="json"))

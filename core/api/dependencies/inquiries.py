from typing import Annotated

from fastapi import Depends, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import SecretStr

from core.shopping.inquiries import InquiryRepository, InquirySessionAuthority, SQLiteInquiryRepository
from core.shopping.customer_persistence import (
    AuthorizationConflict, IdempotencyConflict, InquiryVersionConflict, PersistenceError, StorageUnavailable,
)
from core.shopping.customer_session_service import SessionServiceError
from core.shopping.ports import CatalogReadQueryError, CatalogReadUnavailable
from core.shopping.service import ProductNotFoundError
from core.api.dependencies.customer_session import (
    COOKIE_NAME, CustomerSessionBoundary, SessionAPIDenied, get_customer_session_boundary,
)
from core.api.schemas.customer_sessions import SessionAPIError


def get_inquiry_repository(request: Request) -> InquiryRepository:
    repository = getattr(request.app.state, "inquiry_repository", None)
    if repository is None:
        raise RuntimeError("Inquiry repository is not composed")
    return repository


def get_owned_inquiry_repository() -> SQLiteInquiryRepository:
    """Explicit opt-in injection only; never reuse the default operational store."""
    raise StorageUnavailable("owned inquiry repository is not composed")


def get_owned_inquiry_authority(
    request: Request,
    boundary: Annotated[CustomerSessionBoundary, Depends(get_customer_session_boundary)],
) -> InquirySessionAuthority:
    mutation = request.method not in {"GET", "HEAD"}
    boundary.check_origin(request, required=mutation)
    secret = boundary.cookie_secret(request)
    projection = boundary.authenticate(secret, now=boundary.now())
    if mutation:
        boundary.check_csrf(request, secret, projection)
    return InquirySessionAuthority(
        boundary.service, SecretStr(secret), projection.customer_id, projection.id, boundary.now,
    )


def _owned_error(status: int, code: str, *, clear_cookie: bool = False) -> JSONResponse:
    response = JSONResponse(status_code=status, content={"detail": {"code": code}},
                            headers={"Cache-Control": "no-store"})
    if clear_cookie:
        response.delete_cookie(COOKIE_NAME, path="/", secure=True, httponly=True, samesite="strict")
    return response


class OwnedInquiryRoute(APIRoute):
    """Local fixed errors; no credential, record, body, or exception projection."""

    def matches(self, scope):
        if scope["type"] == "http" and scope["path"].endswith("/"):
            scope = {**scope, "path": scope["path"].rstrip("/")}
        return super().matches(scope)

    async def handle(self, scope, receive, send):
        if self.methods and scope["method"] not in self.methods:
            await _owned_error(405, "owned_inquiry_method_denied")(scope, receive, send)
            return
        await super().handle(scope, receive, send)

    def get_route_handler(self):
        handler = super().get_route_handler()

        async def handle(request):
            try:
                response = await handler(request)
            except SessionAPIDenied as error:
                code, status = {
                    SessionAPIError.ORIGIN_DENIED: ("owned_inquiry_origin_denied", 403),
                    SessionAPIError.CSRF_DENIED: ("owned_inquiry_csrf_denied", 403),
                    SessionAPIError.UNAVAILABLE: ("owned_inquiry_unavailable", 503),
                }.get(error.code, ("owned_inquiry_session_denied", 401))
                response = _owned_error(status, code, clear_cookie=error.clear_cookie)
            except AuthorizationConflict:
                response = _owned_error(403, "owned_inquiry_access_denied")
            except InquiryVersionConflict:
                response = _owned_error(409, "owned_inquiry_version_conflict")
            except IdempotencyConflict:
                response = _owned_error(409, "owned_inquiry_idempotency_conflict")
            except (PersistenceError, SessionServiceError, CatalogReadQueryError, CatalogReadUnavailable):
                response = _owned_error(503, "owned_inquiry_unavailable")
            except ProductNotFoundError:
                response = _owned_error(404, "owned_inquiry_product_not_found")
            except (RequestValidationError, ValueError):
                response = _owned_error(422, "owned_inquiry_invalid_request")
            except Exception:
                response = _owned_error(500, "owned_inquiry_request_failed")
            response.headers["Cache-Control"] = "no-store"
            return response

        return handle

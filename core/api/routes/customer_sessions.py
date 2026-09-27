"""Unregistered customer session routes, usable only with explicit composition."""
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from core.api.dependencies.customer_session import (
    COOKIE_NAME, CSRF_HEADER, CustomerSessionBoundary, SessionAPIDenied,
    get_customer_session_boundary,
)
from core.api.schemas.customer_auth import VerificationReceiptConsumeRequest
from core.api.schemas.customer_sessions import LogoutResponse, SessionAPIError
from core.shopping.customer_persistence import PersistenceError
from core.shopping.customer_session_service import (
    CustomerNotEligible, ReceiptAlreadyConsumed, ReceiptPolicyDenied, SessionServiceError,
)
from core.shopping.customer_sessions import SafeSessionProjection


_ERRORS = {
    SessionAPIError.INVALID_REQUEST: (422, "Invalid session request."),
    SessionAPIError.DENIED: (401, "Customer session denied."),
    SessionAPIError.ORIGIN_DENIED: (403, "Request origin denied."),
    SessionAPIError.CSRF_DENIED: (403, "Request verification denied."),
    SessionAPIError.UNAVAILABLE: (503, "Customer session unavailable."),
    SessionAPIError.INTERNAL: (500, "Customer session request failed."),
    SessionAPIError.METHOD_DENIED: (405, "Request method denied."),
}


def _clear_cookie(response: JSONResponse) -> None:
    response.delete_cookie(COOKIE_NAME, path="/", secure=True, httponly=True, samesite="strict")


def _error(code: SessionAPIError, *, clear_cookie: bool = False) -> JSONResponse:
    status, message = _ERRORS[code]
    response = JSONResponse(status_code=status, content={"detail": {"code": code.value, "message": message}},
                            headers={"Cache-Control": "no-store"})
    if clear_cookie:
        _clear_cookie(response)
    return response


class CustomerSessionRoute(APIRoute):
    """Bound validation, dependency, serialization and unexpected failures locally."""

    def matches(self, scope):
        # Handle slash variants locally: a framework redirect would bypass the
        # no-store/error boundary and could construct Location from request Host.
        if scope["type"] == "http" and scope["path"].endswith("/"):
            scope = {**scope, "path": scope["path"].rstrip("/")}
        return super().matches(scope)

    async def handle(self, scope, receive, send):
        if self.methods and scope["method"] not in self.methods:
            await _error(SessionAPIError.METHOD_DENIED)(scope, receive, send)
            return
        await super().handle(scope, receive, send)

    def get_route_handler(self):
        handler = super().get_route_handler()

        async def handle(request: Request):
            try:
                response = await handler(request)
            except SessionAPIDenied as error:
                response = _error(error.code, clear_cookie=error.clear_cookie)
            except RequestValidationError:
                response = _error(SessionAPIError.INVALID_REQUEST)
            except (ReceiptPolicyDenied, ReceiptAlreadyConsumed, CustomerNotEligible):
                response = _error(SessionAPIError.DENIED)
            except (SessionServiceError, PersistenceError):
                response = _error(SessionAPIError.UNAVAILABLE)
            except Exception:
                # Never serialize or log verifier, database, or framework details.
                response = _error(SessionAPIError.INTERNAL)
            response.headers["Cache-Control"] = "no-store"
            return response

        return handle


router = APIRouter(prefix="/shopping/auth", tags=["customer-session"], route_class=CustomerSessionRoute)
Boundary = Annotated[CustomerSessionBoundary, Depends(get_customer_session_boundary)]


@router.post("/session", response_model=SafeSessionProjection, status_code=201)
def create_session(payload: VerificationReceiptConsumeRequest, request: Request, boundary: Boundary):
    boundary.check_origin(request, required=True)
    now = boundary.now()
    if boundary.has_cookie(request):
        current_secret = boundary.cookie_secret(request)
        current = boundary.authenticate(current_secret, now=now)
        boundary.check_csrf(request, current_secret, current)
    issued = boundary.issue(payload, now=now)
    projection = issued.projection
    expires = min(projection.idle_expires_at, projection.absolute_expires_at)
    max_age = int((expires - boundary.now()).total_seconds())
    if max_age <= 0:
        raise SessionAPIDenied(SessionAPIError.DENIED, clear_cookie=True)
    secret = issued.session_secret.get_secret_value()
    response = JSONResponse(status_code=201, content=projection.model_dump(mode="json"),
                            headers={CSRF_HEADER: boundary.csrf_token(secret, projection)})
    response.set_cookie(COOKIE_NAME, secret, max_age=max_age, expires=expires,
                        path="/", secure=True, httponly=True, samesite="strict")
    return response


@router.get("/session", response_model=SafeSessionProjection)
def session_status(request: Request, boundary: Boundary):
    boundary.check_origin(request, required=False)
    secret = boundary.cookie_secret(request)
    projection = boundary.authenticate(secret, now=boundary.now())
    # SOP protects this dedicated header; no CORS or token in the public model.
    return JSONResponse(content=projection.model_dump(mode="json"),
                        headers={CSRF_HEADER: boundary.csrf_token(secret, projection)})


@router.post("/logout", response_model=LogoutResponse)
def logout(request: Request, boundary: Boundary):
    boundary.check_origin(request, required=True)
    now = boundary.now()
    secret = boundary.cookie_secret(request)
    projection = boundary.authenticate(secret, now=now)
    boundary.check_csrf(request, secret, projection)
    boundary.revoke(secret, projection, now=now)
    response = JSONResponse(content=LogoutResponse().model_dump(mode="json"))
    _clear_cookie(response)
    return response

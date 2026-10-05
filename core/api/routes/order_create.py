"""Isolated opt-in Order create API candidate; not registered by the default app."""
from __future__ import annotations

from typing import Annotated
import sqlite3
import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from core.api.dependencies.customer_session import (
    COOKIE_NAME, SessionAPIDenied, get_customer_session_boundary,
)
from core.api.dependencies.order_create import (
    OrderCreateAPIUnavailable, get_order_create_authority, get_order_create_service,
)
from core.api.schemas.customer_sessions import SessionAPIError
from core.api.schemas.order_create import OrderCreateRequest
from core.shopping.order_core import (
    OrderCreateAmbiguousFailure, OrderCreateAuthority, OrderCreateCatalogResolutionError,
    OrderCreateCommand, OrderCreateContractError, OrderCreateDefinitiveFailure,
    OrderCreateLine, OrderCreateOperationConflict, OrderCreateOperationInFlight,
    OrderCreateOperationTerminalFailure, OrderCreateOperationUnknownOutcome,
    OrderCreateService, OrderLedgerError,
)
from core.shopping.ports import CatalogReadQueryError, CatalogReadUnavailable
from core.shopping.service import ProductNotFoundError


def _error(status:int,code:str,*,clear_cookie:bool=False)->JSONResponse:
    response=JSONResponse(status_code=status,content={"detail":{"code":code}},
                          headers={"Cache-Control":"no-store"})
    if clear_cookie:
        response.delete_cookie(COOKIE_NAME,path="/",secure=True,httponly=True,samesite="strict")
    return response


class OwnedOrderRoute(APIRoute):
    """Fixed bounded errors; never project credentials, request bodies or provider exceptions."""

    def matches(self,scope):
        if scope["type"]=="http" and scope["path"].endswith("/"):
            scope={**scope,"path":scope["path"].rstrip("/")}
        return super().matches(scope)

    async def handle(self,scope,receive,send):
        if self.methods and scope["method"] not in self.methods:
            await _error(405,"owned_order_method_denied")(scope,receive,send);return
        await super().handle(scope,receive,send)

    def get_route_handler(self):
        handler=super().get_route_handler()
        async def handle(request):
            try:
                response=await handler(request)
            except SessionAPIDenied as error:
                code,status={
                    SessionAPIError.ORIGIN_DENIED:("owned_order_origin_denied",403),
                    SessionAPIError.CSRF_DENIED:("owned_order_csrf_denied",403),
                    SessionAPIError.UNAVAILABLE:("owned_order_unavailable",503),
                }.get(error.code,("owned_order_session_denied",401))
                response=_error(status,code,clear_cookie=error.clear_cookie)
            except OrderCreateOperationConflict:
                response=_error(409,"owned_order_idempotency_conflict")
            except OrderCreateOperationInFlight:
                response=_error(409,"owned_order_in_progress")
            except OrderCreateOperationUnknownOutcome:
                response=_error(409,"owned_order_unknown_outcome")
            except OrderCreateOperationTerminalFailure:
                response=_error(409,"owned_order_terminal_failure")
            except OrderCreateCatalogResolutionError:
                response=_error(409,"owned_order_product_unavailable")
            except ProductNotFoundError:
                response=_error(404,"owned_order_product_not_found")
            except (CatalogReadUnavailable,OrderLedgerError,sqlite3.Error,OrderCreateAPIUnavailable):
                response=_error(503,"owned_order_unavailable")
            except CatalogReadQueryError:
                response=_error(422,"owned_order_invalid_product")
            except OrderCreateAmbiguousFailure:
                response=_error(503,"owned_order_outcome_unknown")
            except OrderCreateDefinitiveFailure:
                response=_error(409,"owned_order_provider_rejected")
            except (RequestValidationError,OrderCreateContractError,ValueError,TypeError):
                response=_error(422,"owned_order_invalid_request")
            except Exception:
                response=_error(500,"owned_order_request_failed")
            response.headers["Cache-Control"]="no-store"
            return response
        return handle


router=APIRouter(prefix="/shopping/owned-orders",tags=["owned-orders"],route_class=OwnedOrderRoute)
Authority=Annotated[OrderCreateAuthority,Depends(get_order_create_authority)]
Service=Annotated[OrderCreateService,Depends(get_order_create_service)]


def _projection(body:OrderCreateRequest,result)->dict:
    return {
        "order":{
            "order_number":result.snapshot.order_number,
            "status":result.snapshot.status,
            "currency":result.snapshot.currency,
            "total":format(result.snapshot.total,"f"),
            "line_items":[
                {"product_id":item.product_id,"variation_id":item.variation_id,"quantity":item.quantity}
                for item in body.line_items
            ],
        },
        "idempotent_replay":result.idempotent_replay,
    }


@router.post("")
def create_owned_order(body:OrderCreateRequest,authority:Authority,service:Service):
    command=OrderCreateCommand(
        customer_id=authority.customer_id,
        line_items=tuple(OrderCreateLine(item.product_id,item.variation_id,item.quantity)
                         for item in body.line_items),
        idempotency_key=body.idempotency_key,
        correlation_id="order-corr-"+uuid.uuid4().hex,
        audit_reference="order-audit-"+uuid.uuid4().hex,
        requested_at=authority.authorized_at,
    )
    result=service.execute(command,authority)
    return JSONResponse(
        status_code=200 if result.idempotent_replay else 201,
        content=_projection(body,result),
        headers={"Cache-Control":"no-store"},
    )


__all__=("OwnedOrderRoute","create_owned_order","router")

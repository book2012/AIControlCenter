"""Customer-bound production checkout routes; shipping and tax policy is injected."""
from fastapi import Request
from fastapi.responses import JSONResponse
from core.shopping.order_core.guest_checkout import CheckoutPrepare,CheckoutConfirm,fingerprint
from core.shopping.order_core.guest_chat import GuestCart
from core.api.dependencies.order_create import OrderCreateIntent

def mount_checkout_routes(app,*,store,verified_phone,application,catalog,ledger,quote):
    quote_policy=quote
    def authority(request,write=True):
        value=application._authenticate(request,write=write)
        verified_phone(value.customer_id)
        return value
    async def payload(request,model):
        raw=bytearray()
        async for chunk in request.stream():
            if len(raw)+len(chunk)>8192:raise ValueError("BODY_TOO_LARGE")
            raw.extend(chunk)
        return model.model_validate_json(bytes(raw))
    @app.get("/shopping/checkout/session",include_in_schema=False)
    def session(request:Request):
        try:authority(request,write=False)
        except Exception:return JSONResponse({"verified":False},status_code=401,headers={"Cache-Control":"no-store"})
        return JSONResponse({"verified":True},headers={"Cache-Control":"no-store"})
    @app.post("/shopping/checkout/prepare",include_in_schema=False)
    async def prepare(request:Request):
        try:
            auth=authority(request);data=await payload(request,CheckoutPrepare)
            quote=await __import__("asyncio").to_thread(quote_policy,catalog,data.cart)
            draft=store.prepare(auth.customer_id,auth.session_id,data.cart,data.delivery,quote,verified_phone(auth.customer_id))
            return JSONResponse({"draft_id":draft["draft_id"],"operation_key":draft["operation_key"],
                "delivery":data.delivery.model_dump(),"quote":quote,"order_created":False},headers={"Cache-Control":"no-store"})
        except Exception:return JSONResponse({"message":"휴대폰 인증, 배송정보와 상품 재고를 확인해 주세요."},status_code=422,headers={"Cache-Control":"no-store"})
    @app.post("/shopping/checkout/confirm",include_in_schema=False)
    async def confirm(request:Request):
        try:
            auth=authority(request);data=await payload(request,CheckoutConfirm)
            draft=store.get(data.draft_id,auth.customer_id,auth.session_id,allow_expired=True)
            operation=ledger.inspect_operation(draft["operation_key"])
            if operation is None:
                draft=store.get(data.draft_id,auth.customer_id,auth.session_id)
                current=await __import__("asyncio").to_thread(quote_policy,catalog,GuestCart.model_validate({"line_items":draft["body"]["line_items"]}))
                if fingerprint(current)!=fingerprint(draft["body"]["quote"]):raise ValueError("QUOTE_CHANGED")
                store.confirm(data.draft_id,auth.customer_id,auth.session_id)
            if draft["state"]!="CONFIRMED" and operation is not None:raise ValueError("CONFIRMATION_REQUIRED")
            intent=OrderCreateIntent.model_validate({"line_items":draft["body"]["line_items"],"idempotency_key":draft["operation_key"]})
            result=await __import__("asyncio").to_thread(application.execute,request,intent)
            current_status=application.operation_status(request,draft["operation_key"])
            return JSONResponse({"provider_order_id":result.snapshot.provider_order_id,"order_number":str(result.snapshot.provider_order_id),"total":str(result.snapshot.total),
                "currency":result.snapshot.currency,"idempotent_replay":result.idempotent_replay,"state":"COMPLETED","review_state":current_status["review_state"],
                "operation_key":draft["operation_key"]},status_code=200 if result.idempotent_replay else 201,headers={"Cache-Control":"no-store"})
        except Exception:
            # A lost response, claimed operation or ambiguous provider dispatch never permits new POST/key.
            return JSONResponse({"message":"주문 결과를 확정하지 못했습니다. 같은 주문의 상태를 확인하고 새 주문을 만들지 마세요."},
                status_code=409,headers={"Cache-Control":"no-store"})


def mount_order_lookup(app,*,store,application,verified_phone):
    @app.post("/shopping/orders/lookup",include_in_schema=False)
    async def lookup(request:Request):
        try:
            auth=application._authenticate(request,write=True)
            phone=verified_phone(auth.customer_id)
            raw=bytearray()
            async for chunk in request.stream():
                if len(raw)+len(chunk)>1024:raise ValueError("BODY_TOO_LARGE")
                raw.extend(chunk)
            import json
            data=json.loads(raw)
            if type(data) is not dict or set(data)!={"order_number","phone"} or any(type(v) is not str for v in data.values()):
                raise ValueError("INVALID_LOOKUP")
            order=store.lookup(auth.customer_id,data["order_number"],data["phone"],phone)
            return JSONResponse({"order":order},headers={"Cache-Control":"no-store","X-Robots-Tag":"noindex, nofollow"})
        except Exception:
            return JSONResponse({"message":"주문번호와 인증한 휴대폰 번호를 확인해 주세요."},status_code=403,headers={"Cache-Control":"no-store"})


class GuardedGuestOrderWriter:
    """Verify private confirmation and refreshed quote immediately before the provider write."""
    def __init__(self,*,writer,ledger,checkout,verified_phone,catalog,quote,clock):
        self.writer=writer;self.ledger=ledger;self.checkout=checkout
        self.verified_phone=verified_phone;self.catalog=catalog;self.quote=quote;self.clock=clock
    def create_order(self,command):
        from datetime import datetime
        from core.shopping.order_core import OrderCreateDefinitiveFailure
        try:
            operation=self.ledger.inspect_operation(command.idempotency_key)
            if not operation or operation["state"]!="CLAIMED" or operation["customer_id"]!=command.customer_id or operation["command_digest"]!=command.command_digest:
                raise ValueError("ORDER_AUTHORITY_DENIED")
            expires=datetime.fromisoformat(operation["authority_expires_at"].replace("Z","+00:00"))
            if self.clock()>=expires:raise ValueError("ORDER_AUTHORITY_EXPIRED")
            draft=self.checkout.operation(command.idempotency_key,command.customer_id,operation["session_id"])
            if draft["body"]["billing"]["phone"]!=self.verified_phone(command.customer_id):
                raise ValueError("VERIFIED_PHONE_MISMATCH")
            lines=draft["body"]["line_items"]
            expected=[(v["product_id"],v["variation_id"],v["quantity"]) for v in lines]
            actual=[(v.product_id,v.variation_id,v.quantity) for v in command.line_items]
            if actual!=expected:raise ValueError("DRAFT_LINE_MISMATCH")
            current=self.quote(self.catalog,GuestCart.model_validate({"line_items":lines}))
            if fingerprint(current)!=fingerprint(draft["body"]["quote"]):raise ValueError("QUOTE_CHANGED")
        except Exception:
            raise OrderCreateDefinitiveFailure("GUEST_PROVIDER_PREWRITE_DENIED") from None
        return self.writer.create_order(command)

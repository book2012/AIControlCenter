"""Explicit production guest API composition. No provider credentials or activation defaults."""
from pathlib import Path
from urllib.parse import urlsplit
import os,secrets,threading
from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
from pydantic import SecretBytes
from core.api.dependencies.customer_session import CustomerSessionBoundary,get_customer_session_boundary
from core.api.dependencies.order_create import SessionBoundOrderCreateApplication
from core.api.routes.customer_sessions import router as sessions
from core.shopping.customer_persistence import initialize_schema
from core.shopping.customer_session_service import CustomerSessionService
from core.shopping.guest_phone_runtime import GuestPhoneBridge,mount_phone_routes
from core.shopping.guest_checkout_runtime import mount_checkout_routes,mount_order_lookup,GuardedGuestOrderWriter
from core.shopping.order_core import OrderCreateService,SQLiteOrderCreateLedger,ShoppingServiceOrderCatalogResolver
from core.shopping.order_core.guest_checkout import PrivateCheckoutStore
from core.shopping.order_core.guest_chat import GuestShoppingChat,GuestQuestion,GuestCart

def create_guest_commerce_app(*,private_root,origin,phone_cfg,binding_key,csrf_key,catalog,
                              quote,writer_factory,lookup_store_factory,clock,port_factory=None,
                              intent_classifier=None,inquiry_queue=None,path_policy=None):
    """Explicit separate storage, per-customer verification, confirmation and inquiry.
    
    Caller must provide production catalog, shipping/tax policy, governed provider
    writer and lookup repository. This factory never starts a Telegram poller or SMS
    notification worker. No synthetic customer/session or direct order-create route.
    """
    parsed=urlsplit(origin)
    if parsed.scheme!="https" or not parsed.hostname or parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.port or parsed.hostname in {"localhost","dev.bokstory.duckdns.org"}:
        raise ValueError("PRODUCTION_ORIGIN_REQUIRED")
    root=Path(private_root).absolute()
    if root.is_symlink() or any(v in root.parts for v in ("dev-order","aicontrolcenter-dev-order")):
        raise ValueError("SEPARATE_PRODUCTION_STORAGE_REQUIRED")
    if phone_cfg.get("environment")!="PROD" or len(binding_key)<32 or len(csrf_key)<32:
        raise ValueError("PRODUCTION_IDENTITY_CONFIGURATION_REQUIRED")
    if not all(callable(v) for v in (quote,writer_factory,lookup_store_factory,clock)):
        raise ValueError("EXPLICIT_COMMERCE_PORTS_REQUIRED")
    from core.shopping.product_drafts.persistence.path_policy import DurableDatabasePathPolicy
    policy=path_policy or DurableDatabasePathPolicy()
    policy.validate(root/"orders.sqlite3")
    root.mkdir(parents=True,exist_ok=True);os.chmod(root,0o700)
    paths=[root/name for name in ("customers.sqlite3","phone-browser.sqlite3","orders.sqlite3","checkout.sqlite3")]
    if any(path.is_symlink() for path in paths):raise ValueError("PRIVATE_STORAGE_REQUIRED")
    customer_path=paths[0];initialize_schema(customer_path);os.chmod(customer_path,0o600)
    bridge=GuestPhoneBridge(cfg=phone_cfg,binding_key=binding_key,customer_path=customer_path,
                           bridge_path=paths[1],clock=clock,port_factory=port_factory)
    evidence={};lock=threading.Lock()
    def register(value):
        with lock:
            # Expired receipts cannot consume the bounded registry forever.
            now=clock()
            expired=[key for key,item in evidence.items() if item.receipt.expires_at<=now]
            for key in expired:evidence.pop(key,None)
            if len(evidence)>=100:raise ValueError("VERIFICATION_CAPACITY")
            receipt="VRF-"+secrets.token_hex(16).upper();challenge="CHL-"+secrets.token_hex(16).upper()
            evidence[receipt,challenge]=value
        return {"receipt_id":receipt,"browser_challenge":challenge}
    def resolve(payload):
        with lock:value=evidence.pop((payload.receipt_id,payload.browser_challenge),None)
        if value is None:raise ValueError("TRUSTED_RECEIPT_REQUIRED")
        return value
    boundary=CustomerSessionBoundary(service=CustomerSessionService(str(customer_path)),trusted_origin=origin,
        csrf_key=SecretBytes(csrf_key),clock=clock,resolve_evidence=resolve,recover_durable_bindings=True)
    ledger=SQLiteOrderCreateLedger(paths[2],clock=clock,path_policy=policy);ledger.initialize()
    checkout=PrivateCheckoutStore(paths[3],clock=lambda:clock().timestamp())
    writer=GuardedGuestOrderWriter(writer=writer_factory(ledger,checkout,bridge),ledger=ledger,checkout=checkout,verified_phone=bridge.verified_phone,catalog=catalog,quote=quote,clock=clock)
    application=SessionBoundOrderCreateApplication(session_boundary=boundary,
        order_service=OrderCreateService(catalog_resolver=ShoppingServiceOrderCatalogResolver(catalog),
                                        order_creator=writer,coordinator=ledger))
    store=lookup_store_factory(ledger,checkout,catalog)
    app=FastAPI(title="agachichi guest commerce",docs_url=None,redoc_url=None,openapi_url=None)
    app.include_router(sessions);app.dependency_overrides[get_customer_session_boundary]=lambda:boundary
    mount_phone_routes(app,bridge=bridge,boundary=boundary,register_evidence=register)
    mount_checkout_routes(app,store=checkout,verified_phone=bridge.verified_phone,application=application,
                          catalog=catalog,ledger=ledger,quote=quote)
    mount_order_lookup(app,store=store,application=application,verified_phone=bridge.verified_phone)
    @app.get("/shopping/orders/operations/{key}",include_in_schema=False)
    def status(key:str,request:Request):
        try:
            from core.api.schemas.order_create import OrderOperationStatus
            value=application.operation_status(request,key)
            if value is None:raise ValueError("ORDER_NOT_FOUND")
            return JSONResponse(OrderOperationStatus.model_validate(value).model_dump(mode="json"),headers={"Cache-Control":"no-store"})
        except Exception:return JSONResponse({"message":"주문 상태를 확인할 수 없습니다."},status_code=403,headers={"Cache-Control":"no-store"})
    chat=GuestShoppingChat(catalog,intent_classifier=intent_classifier)
    async def body(request,model):
        boundary.check_origin(request,required=True);raw=bytearray()
        async for chunk in request.stream():
            if len(raw)+len(chunk)>8192:raise ValueError("BODY_TOO_LARGE")
            raw.extend(chunk)
        return model.model_validate_json(bytes(raw))
    @app.post("/shopping/chat/inquiry",include_in_schema=False)
    async def inquiry(request:Request):
        try:
            question=await body(request,GuestQuestion)
            result=await __import__("asyncio").to_thread(chat.answer,question)
            if result["action"]=="OPERATOR_REQUIRED" and inquiry_queue is not None:
                answer=await __import__("asyncio").to_thread(inquiry_queue.lookup,question.product_id,question.message)
                if answer is not None:result={**result,"message":answer,"action":"ANSWER","answer_engine":"OPERATOR_APPROVED_FAQ"}
                else:
                    ticket=await __import__("asyncio").to_thread(inquiry_queue.submit,question.product_id,question.message)
                    result={**result,**ticket,"message":"운영자에게 문의를 전달했습니다.","action":"OPERATOR_QUEUED"}
            return JSONResponse(result,headers={"Cache-Control":"no-store"})
        except Exception:return JSONResponse({"message":"문의 내용을 확인해 주세요."},status_code=422,headers={"Cache-Control":"no-store"})
    @app.post("/shopping/chat/quote",include_in_schema=False)
    async def cart_quote(request:Request):
        try:
            cart=await body(request,GuestCart)
            result=await __import__("asyncio").to_thread(quote,catalog,cart)
            return JSONResponse(result,headers={"Cache-Control":"no-store"})
        except Exception:return JSONResponse({"message":"상품·옵션·수량을 확인해 주세요."},status_code=422,headers={"Cache-Control":"no-store"})
    @app.get("/shopping/chat/capabilities",include_in_schema=False)
    def capabilities():
        return JSONResponse({"guest_inquiry":True,"cart_quote":True,"phone_verification":True,"delivery_capture":True,"order_confirmation":True,"transaction_sms":False,"message":"휴대폰 인증 후 배송정보와 주문 내용을 확인해 주세요."},headers={"Cache-Control":"no-store"})
    app.state.guest_phone=bridge;app.state.order_application=application
    app.state.order_ledger=ledger;app.state.checkout=checkout;app.state.lookup_store=store
    return app

"""Scoped DEV checkout composition; private delivery does not enter public ledger/outbox."""
from decimal import Decimal
import hashlib,json,secrets,base64,subprocess,os
from pathlib import Path
from fastapi import Request
from fastapi.responses import JSONResponse
from core.shopping.order_core.guest_checkout import PrivateCheckoutStore,CheckoutPrepare,CheckoutConfirm,canonical,fingerprint
from core.shopping.order_core.guest_chat import GuestCart
from core.api.dependencies.order_create import OrderCreateIntent
from core.shopping.order_core.woocommerce_writer import WooCommerceOrderWriter
from ops.macos.shopping.dev_order_transport import PinnedDevWooOrderSession

def provision_guest_provider_customer(phone_cfg,private_root):
    from ops.macos.shopping.dev_order_runtime import assert_isolation
    assert_isolation()
    username="aicc-dev-phone-"+phone_cfg["guest_customer_id"].removeprefix("AG-CUS-")
    payload=base64.b64encode(json.dumps({"username":username,"password":secrets.token_urlsafe(40)}).encode()).decode()
    code="<?php\nif(getenv('WORDPRESS_DB_NAME')!=='aicc_order_dev'){exit(2);}\nrequire '/var/www/html/wp-load.php';\nadd_filter('pre_wp_mail',fn()=>false);\n"
    code+="$cfg=json_decode(base64_decode('"+payload+"'),true);$u=get_user_by('login',$cfg['username']);"
    code+="if(!$u){$id=wp_create_user($cfg['username'],$cfg['password'],$cfg['username'].'@example.invalid');if(is_wp_error($id)){exit(3);}$u=get_user_by('id',$id);$u->set_role('customer');}"
    code+="if(!in_array('customer',$u->roles,true)){exit(4);}echo json_encode(['customer_id'=>$u->ID]);"
    result=subprocess.run(["docker","--context","colima-aicontrolcenter-commerce","exec","-i","aicc-order-dev-wordpress-1","php"],input=code,capture_output=True,text=True,timeout=30)
    if result.returncode:raise RuntimeError("DEV_GUEST_PROVIDER_CUSTOMER_FAILED")
    try:customer=json.loads(result.stdout)["customer_id"]
    except Exception:raise RuntimeError("DEV_GUEST_PROVIDER_CUSTOMER_FAILED") from None
    if type(customer) is not int or customer<=0:raise RuntimeError("DEV_GUEST_PROVIDER_CUSTOMER_FAILED")
    phone_cfg["provider_customer_id"]=customer
    from ops.macos.shopping.dev_order_provision import private_write
    private_write(private_root/"phone-verification.private.json",phone_cfg)
    return customer

def authoritative_quote(catalog,cart):
    # Explicit DEV free shipping/no tax; never inherit this policy into production.
    cart=GuestCart.model_validate(cart);seen=set();items=[];total=Decimal("0")
    for line in cart.line_items:
        identity=(line.product_id,line.variation_id)
        if identity in seen:raise ValueError("DUPLICATE_LINE")
        seen.add(identity);product=catalog.get_product(line.product_id)
        if product["source"]!="woocommerce" or not product["in_stock"] or not line.variation_id:raise ValueError("CATALOG_DENIED")
        variants=catalog.read("products/"+line.product_id+"/variations?per_page=100")
        matches=[v for v in variants if str(v["id"])==line.variation_id]
        if len(matches)!=1:raise ValueError("VARIATION_DENIED")
        raw=matches[0]
        if raw.get("status")!="publish" or raw.get("stock_status")!="instock" or raw.get("manage_stock") is not True or type(raw.get("stock_quantity")) is not int or raw["stock_quantity"]<line.quantity or raw.get("backorders") not in ("no",None):
            raise ValueError("STOCK_DENIED")
        price=Decimal(raw["price"])
        if not price.is_finite() or price<=0:raise ValueError("PRICE_DENIED")
        subtotal=price*line.quantity;total+=subtotal
        items.append({"product_id":line.product_id,"variation_id":line.variation_id,"quantity":line.quantity,
            "name":product["name"],"option":next(v.label for v in product["variants"] if v.id==line.variation_id),"unit_price":str(price),"subtotal":str(subtotal)})
    return {"line_items":items,"items_total":str(total),"shipping_fee":"0","total_tax":"0","final_total":str(total),
        "currency":"KRW","shipping_policy":"DEV_FREE_SHIPPING"}

class GuestCheckoutWooSession(PinnedDevWooOrderSession):
    def __init__(self,certificate,*,store,provider_customer_id):super().__init__(certificate);self.store=store;self.customer=provider_customer_id
    def post(self,url,**kwargs):
        payload=kwargs.get("json")
        if type(payload) is not dict or payload.get("customer_id")!=self.customer:return super().post(url,**kwargs)
        tags=[m["value"] for m in payload["meta_data"] if m["key"]=="_aicc_order_operation"]
        if len(tags)!=1:raise ValueError("DELIVERY_TAG_INVALID")
        draft=self.store.by_provider_tag(tags[0]);body=draft["body"]
        expected=[{"product_id":int(v["product_id"]),"variation_id":int(v["variation_id"]),"quantity":v["quantity"]} for v in body["line_items"]]
        if payload["line_items"]!=expected:raise ValueError("DELIVERY_LINE_MISMATCH")
        payload={**payload,"billing":body["billing"],"shipping":body["shipping"],
            "shipping_lines":[{"method_id":"aicc_dev_free","method_title":"DEV 무료 배송","total":"0"}],
            "meta_data":[*payload["meta_data"],{"key":"_aicc_delivery_digest","value":draft["digest"]}]}
        response=super().post(url,**{**kwargs,"json":payload})
        if response.status_code!=201:return response
        raw=WooCommerceOrderWriter._document(response)
        verify_delivery_receipt(raw,draft,self.customer)
        # Rebuild a bounded requests response for the unchanged Core writer.
        import requests
        rebuilt=requests.Response();rebuilt.status_code=201;rebuilt._content=json.dumps(raw).encode();rebuilt._content_consumed=True;rebuilt.headers["Content-Type"]="application/json"
        rebuilt.iter_content=lambda chunk_size:iter([rebuilt._content])
        return rebuilt

    def get(self,url,**kwargs):
        response=super().get(url,**kwargs)
        if response.status_code!=200:return response
        raw=WooCommerceOrderWriter._document(response)
        if raw.get("customer_id")==self.customer:
            tags=[m.get("value") for m in raw.get("meta_data",[]) if m.get("key")=="_aicc_order_operation"]
            if len(tags)!=1:raise ValueError("DELIVERY_TAG_INVALID")
            draft=self.store.by_provider_tag(tags[0],allow_expired=True)
            if draft["state"]!="CONFIRMED":raise ValueError("EXPLICIT_CONFIRMATION_REQUIRED")
            verify_delivery_receipt(raw,draft,self.customer)
        import requests
        rebuilt=requests.Response();rebuilt.status_code=200;rebuilt._content=json.dumps(raw).encode();rebuilt._content_consumed=True
        rebuilt.headers["Content-Type"]="application/json";rebuilt.iter_content=lambda chunk_size:iter([rebuilt._content])
        return rebuilt

def verify_delivery_receipt(raw,draft,customer):
    body=draft["body"]
    if raw.get("customer_id")!=customer:raise ValueError("CUSTOMER_MISMATCH")
    for field in ("billing","shipping"):
        if type(raw.get(field)) is not dict or any(raw[field].get(k)!=v for k,v in body[field].items()):raise ValueError("DELIVERY_MISMATCH")
    tags=[m.get("value") for m in raw.get("meta_data",[]) if m.get("key")=="_aicc_delivery_digest"]
    if tags!=[draft["digest"]]:raise ValueError("DELIVERY_DIGEST_MISMATCH")
    if raw.get("currency")!="KRW" or Decimal(raw["total"])!=Decimal(body["quote"]["final_total"]) or Decimal(raw["total_tax"])!=0 or Decimal(raw["shipping_total"])!=0:
        raise ValueError("FINAL_AMOUNT_MISMATCH")

def mount_checkout_routes(app,*,store,phone_cfg,boundary,application,catalog,ledger):
    def authority(request,write=True):
        value=application._authenticate(request,write=write)
        if value.customer_id!=phone_cfg["guest_customer_id"]:raise ValueError("PHONE_VERIFIED_GUEST_REQUIRED")
        return value
    async def payload(request,model):
        raw=bytearray()
        async for chunk in request.stream():
            if len(raw)+len(chunk)>8192:raise ValueError("BODY_TOO_LARGE")
            raw.extend(chunk)
        return model.model_validate_json(bytes(raw))
    @app.get("/__order-dev/checkout/session",include_in_schema=False)
    def session(request:Request):
        try:authority(request,write=False)
        except Exception:return JSONResponse({"verified":False},status_code=401,headers={"Cache-Control":"no-store"})
        return JSONResponse({"verified":True},headers={"Cache-Control":"no-store"})
    @app.post("/__order-dev/checkout/prepare",include_in_schema=False)
    async def prepare(request:Request):
        try:
            auth=authority(request);data=await payload(request,CheckoutPrepare)
            quote=await __import__("asyncio").to_thread(authoritative_quote,catalog,data.cart)
            draft=store.prepare(auth.customer_id,auth.session_id,data.cart,data.delivery,quote,phone_cfg["test_phone"])
            return JSONResponse({"draft_id":draft["draft_id"],"operation_key":draft["operation_key"],
                "delivery":data.delivery.model_dump(),"quote":quote,"order_created":False},headers={"Cache-Control":"no-store"})
        except Exception:return JSONResponse({"message":"휴대폰 인증, 배송정보와 상품 재고를 확인해 주세요."},status_code=422,headers={"Cache-Control":"no-store"})
    @app.post("/__order-dev/checkout/confirm",include_in_schema=False)
    async def confirm(request:Request):
        try:
            auth=authority(request);data=await payload(request,CheckoutConfirm)
            draft=store.get(data.draft_id,auth.customer_id,auth.session_id,allow_expired=True)
            operation=ledger.inspect_operation(draft["operation_key"])
            if operation is None:
                draft=store.get(data.draft_id,auth.customer_id,auth.session_id)
                current=await __import__("asyncio").to_thread(authoritative_quote,catalog,GuestCart.model_validate({"line_items":draft["body"]["line_items"]}))
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

"""DEV after-sales workflow: fulfillment, customer return/exchange cases and private attachments.

No payment refund, carrier API, fulfillment mutation or PROD composition exists here.
"""
from pathlib import Path
import hashlib,json,os,re,secrets,sqlite3,time
from fastapi import Request
from fastapi.responses import HTMLResponse,JSONResponse,RedirectResponse
from pydantic import BaseModel,ConfigDict,Field

RETURN_WINDOW=14*86400
MAX_ATTACHMENT=5*1024*1024
MEDIA={"image/jpeg":(".jpg",b"\xff\xd8\xff"),"image/png":(".png",b"\x89PNG\r\n\x1a\n"),"image/webp":(".webp",b"RIFF")}

from core.shopping.guest_aftersales import CaseCreate,GuestAftersalesStore as DevAftersalesStore

def mount_aftersales(app,*,store,boundary,phone_cfg):
    store.verified_phone=phone_cfg.get("test_phone")
    def auth(request,write=False):
        if write:boundary.check_origin(request,required=True)
        secret=boundary.cookie_secret(request);projection=boundary.authenticate(secret,now=boundary.now())
        if projection.customer_id!=phone_cfg["guest_customer_id"]:raise ValueError("CUSTOMER_DENIED")
        if write:boundary.check_csrf(request,secret,projection)
        return projection
    @app.post("/__order-dev/orders/lookup",include_in_schema=False)
    async def lookup(request:Request):
        try:
            projection=auth(request,write=True)
            raw=bytearray()
            async for chunk in request.stream():
                if len(raw)+len(chunk)>1024:raise ValueError("BODY_TOO_LARGE")
                raw.extend(chunk)
            data=json.loads(raw)
            if type(data) is not dict or set(data)!={"order_number","phone"} or any(type(v) is not str for v in data.values()):raise ValueError("INVALID_LOOKUP")
            order=store.lookup(projection.customer_id,data["order_number"],data["phone"],phone_cfg["test_phone"])
            return JSONResponse({"order":order},headers={"Cache-Control":"no-store","X-Robots-Tag":"noindex, nofollow"})
        except Exception:
            return JSONResponse({"message":"주문번호와 인증한 휴대폰 번호를 확인해 주세요."},status_code=403,headers={"Cache-Control":"no-store"})
    @app.get("/dev-order/my-orders",include_in_schema=False)
    def portal():return RedirectResponse("/homepage/storefront/my-orders",status_code=302,headers={"Cache-Control":"no-store","X-Robots-Tag":"noindex, nofollow"})
    @app.get("/__order-dev/aftersales/orders",include_in_schema=False)
    def orders(request:Request):
        if phone_cfg.get("test_phone"):return JSONResponse({"message":"주문번호로 조회해 주세요."},status_code=403,headers={"Cache-Control":"no-store"})
        try:return JSONResponse({"orders":store.customer_orders(auth(request).customer_id)},headers={"Cache-Control":"no-store"})
        except Exception:return JSONResponse({"message":"휴대폰 인증이 필요합니다."},status_code=401,headers={"Cache-Control":"no-store"})
    @app.get("/__order-dev/aftersales/orders/{order_id}/exchange-options",include_in_schema=False)
    def options(order_id:int,request:Request):
        try:return JSONResponse({"options":store.exchange_options(auth(request).customer_id,order_id)},headers={"Cache-Control":"no-store"})
        except Exception:return JSONResponse({"message":"교환 가능한 옵션을 확인할 수 없습니다."},status_code=422,headers={"Cache-Control":"no-store"})
    @app.post("/__order-dev/aftersales/cases",include_in_schema=False)
    async def create_case(request:Request):
        try:
            projection=auth(request,write=True);raw=await request.body()
            if len(raw)>8192:raise ValueError()
            data=CaseCreate.model_validate_json(raw);case=store.create_case(projection.customer_id,data)
            return JSONResponse({"case":case},status_code=201,headers={"Cache-Control":"no-store"})
        except Exception:return JSONResponse({"message":"환불/교환 가능 기간과 입력 내용을 확인해 주세요."},status_code=422,headers={"Cache-Control":"no-store"})
    @app.post("/__order-dev/aftersales/cases/{case_id}/attachments",include_in_schema=False)
    async def attachment(case_id:str,request:Request):
        try:
            if not re.fullmatch(r"[a-f0-9]{8}",case_id):raise ValueError()
            projection=auth(request,write=True);raw=bytearray()
            async for chunk in request.stream():
                if len(raw)+len(chunk)>MAX_ATTACHMENT:raise ValueError("ATTACHMENT_TOO_LARGE")
                raw.extend(chunk)
            value=store.attach(projection.customer_id,case_id,request.headers.get("content-type","").split(";",1)[0],bytes(raw))
            return JSONResponse(value,status_code=201,headers={"Cache-Control":"no-store"})
        except Exception:return JSONResponse({"message":"첨부는 JPEG/PNG/WebP, 파일당 5MB 이하로 최대 5개까지 가능합니다."},status_code=422,headers={"Cache-Control":"no-store"})

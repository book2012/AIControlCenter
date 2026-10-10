"""Authenticated customer return/exchange routes, without refund or carrier side effects."""
import re
from fastapi import Request
from fastapi.responses import JSONResponse
from core.shopping.guest_aftersales import CaseCreate
MAX_ATTACHMENT=5*1024*1024

def mount_customer_aftersales(app,*,store,application,verified_phone):
    def auth(request,write=False):
        projection=application._authenticate(request,write=write)
        verified_phone(projection.customer_id)
        return projection
    @app.get("/shopping/aftersales/orders/{order_id}/exchange-options",include_in_schema=False)
    def options(order_id:int,request:Request):
        try:return JSONResponse({"options":store.exchange_options(auth(request).customer_id,order_id)},headers={"Cache-Control":"no-store"})
        except Exception:return JSONResponse({"message":"교환 가능한 옵션을 확인할 수 없습니다."},status_code=422,headers={"Cache-Control":"no-store"})
    @app.post("/shopping/aftersales/cases",include_in_schema=False)
    async def create_case(request:Request):
        try:
            projection=auth(request,write=True);raw=bytearray()
            async for chunk in request.stream():
                if len(raw)+len(chunk)>8192:raise ValueError("BODY_TOO_LARGE")
                raw.extend(chunk)
            data=CaseCreate.model_validate_json(raw);case=store.create_case(projection.customer_id,data)
            return JSONResponse({"case":case},status_code=201,headers={"Cache-Control":"no-store"})
        except Exception:return JSONResponse({"message":"환불/교환 가능 기간과 입력 내용을 확인해 주세요."},status_code=422,headers={"Cache-Control":"no-store"})
    @app.post("/shopping/aftersales/cases/{case_id}/attachments",include_in_schema=False)
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

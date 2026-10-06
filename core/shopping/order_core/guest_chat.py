"""Guest shopping dialogue: catalog answers and quotes, never authentication or writes."""
from decimal import Decimal
from html import unescape
import re
from pydantic import BaseModel, ConfigDict, Field
from core.shopping.models import Product

class GuestQuestion(BaseModel):
    model_config=ConfigDict(extra="forbid",hide_input_in_errors=True)
    product_id:str=Field(strict=True,min_length=1,max_length=128,pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    message:str=Field(strict=True,min_length=1,max_length=500)

class GuestCartLine(BaseModel):
    model_config=ConfigDict(extra="forbid",hide_input_in_errors=True)
    product_id:str=Field(strict=True,min_length=1,max_length=128,pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    variation_id:str|None=Field(default=None,strict=True,min_length=1,max_length=128,pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    quantity:int=Field(strict=True,ge=1,le=10)

class GuestCart(BaseModel):
    model_config=ConfigDict(extra="forbid",hide_input_in_errors=True)
    line_items:tuple[GuestCartLine,...]=Field(min_length=1,max_length=20)

class GuestShoppingChat:
    def __init__(self,catalog,intent_classifier=None):self.catalog=catalog;self.classifier=intent_classifier
    def product(self,key):
        p=Product(**self.catalog.get_product(key))
        if p.id!=key or p.source!="woocommerce":raise ValueError("CATALOG_NOT_VERIFIED")
        amount=Decimal(p.price)
        if not amount.is_finite() or amount<0:raise ValueError("CATALOG_PRICE_INVALID")
        return p
    def answer(self,question):
        question=GuestQuestion.model_validate(question)
        p=self.product(question.product_id); text=question.message.strip().lower();engine="RULES"
        if self.classifier is not None:
            try:
                intent=("OPERATOR" if any(v in question.message for v in ("배송","교환","반품","불량","환불","맞춤","수선")) else self.classifier(question.message,p))
                text={"STOCK":"재고","PRICE":"가격","DESCRIPTION":"설명","PURCHASE":"주문","OPERATOR":""}[intent]
                engine="LOCAL_AI"
            except Exception:
                return {"message":"현재 내부 AI가 질문을 확인할 수 없습니다. 운영자 확인이 필요합니다.","action":"OPERATOR_REQUIRED","product_id":p.id,"source":"woocommerce","answer_engine":"LOCAL_AI_UNAVAILABLE"}
        pending_stock=callable(getattr(self.catalog,"inventory_pending",None)) and self.catalog.inventory_pending(p.id) is True
        temporary_price=callable(getattr(self.catalog,"temporary_price",None)) and self.catalog.temporary_price(p.id) is True
        available=[v.label for v in p.variants if v.available]
        unavailable=[v.label for v in p.variants if not v.available]
        if any(v in text for v in ("주문","살게","구매","담아")):
            message="상품 옵션을 선택하고 주문하기를 눌러 주세요. 휴대폰 인증과 배송정보 입력 후 최종 확인하면 접수됩니다."
            action="START_ORDER"
            if pending_stock:message="현재 사이즈와 실물 재고를 확인 중입니다. 확인 전에는 주문할 수 없습니다. 문의를 남겨 주세요.";action="ANSWER"
        elif any(v in text for v in ("재고","사이즈","옵션","품절","stock","size")):
            message=("현재 구매 가능한 옵션: "+", ".join(available) if p.in_stock and available else
                     "현재 재고가 있습니다." if p.in_stock else "현재 품절입니다.")
            if unavailable:message+=" / 품절 옵션: "+", ".join(unavailable)
            if pending_stock:message="등록된 색상: "+", ".join(v.label for v in p.variants)+" / 사이즈와 실물 재고 확인 중입니다. 확인 전에는 주문할 수 없습니다."
            if callable(getattr(self.catalog,"stock_summary",None)):message+=" / "+self.catalog.stock_summary(p.id)
            message+=" 주문 확정 전에 재고를 다시 확인합니다.";action="ANSWER"
        elif any(v in text for v in ("가격","얼마","price")):
            message=f"현재 상품 가격은 {Decimal(p.price):,} {p.currency}입니다. 배송비와 최종 금액은 주문 확인 단계에서 안내합니다.";action="ANSWER"
            if temporary_price:message=f"업로드 검토용 임시 가격은 {Decimal(p.price):,} {p.currency}입니다. 실제 판매 가격은 운영자 확인이 필요합니다."
        elif any(v in text for v in ("설명","소재","상품정보","material")):
            description=unescape(re.sub(r"<[^>]*>"," ",p.description))
            description=" ".join(description.split())[:1000]
            message=description or "등록된 상품 설명이 없어 운영자 확인이 필요합니다.";action="ANSWER"
        else:
            message="등록된 상품 정보에서 답을 확인할 수 없습니다. 재고·옵션·가격·상품 설명을 물어보실 수 있습니다. 그 외 질문은 운영자 확인이 필요합니다."
            action="OPERATOR_REQUIRED"
        return {"message":message,"action":action,"product_id":p.id,"source":"woocommerce","answer_engine":engine}
    def quote(self,cart):
        cart=GuestCart.model_validate(cart)
        identities=set();items=[];total=Decimal("0");currency=None
        for line in cart.line_items:
            identity=(line.product_id,line.variation_id)
            if identity in identities:raise ValueError("DUPLICATE_CART_LINE")
            identities.add(identity);p=self.product(line.product_id)
            if callable(getattr(self.catalog,"inventory_pending",None)) and self.catalog.inventory_pending(p.id) is True:raise ValueError("INVENTORY_NOT_CONFIRMED")
            if not p.in_stock:raise ValueError("OUT_OF_STOCK")
            variant=None
            if p.variants:
                matches=[v for v in p.variants if v.id==line.variation_id]
                if len(matches)!=1 or not matches[0].available:raise ValueError("VARIATION_UNAVAILABLE")
                variant=matches[0]
            elif line.variation_id is not None:raise ValueError("VARIATION_INVALID")
            if currency is not None and currency!=p.currency:raise ValueError("MIXED_CURRENCY")
            currency=p.currency
            subtotal=Decimal(p.price)*line.quantity;total+=subtotal
            items.append({"product_id":p.id,"variation_id":line.variation_id,"name":p.name,
                "option":variant.label if variant else None,"quantity":line.quantity,
                "unit_price":str(Decimal(p.price)),"subtotal":str(subtotal)})
        return {"line_items":items,"items_total":str(total),"currency":currency,
            "shipping_fee":None,"final_total":None,"order_created":False,
            "next_step":"PHONE_VERIFICATION","message":"상품 금액을 확인했습니다. 휴대폰 인증 후 배송정보와 최종 금액을 확인합니다."}

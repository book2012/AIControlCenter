from decimal import Decimal
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from core.shopping.models import ProductVariant
from core.shopping.order_core.guest_chat import GuestShoppingChat,GuestQuestion,GuestCart
from core.shopping.order_core.guest_chat_app import mount_guest_chat
class Catalog:
    def get_product(self,key):
        if key not in ("10","20"):raise ValueError()
        return dict(id=key,name="<script>unsafe</script> 블라우스",slug="blouse",description="<p>린넨 소재</p>",
          price=Decimal("29000"),currency="KRW",category="TOP",in_stock=True,source="woocommerce",
          image_url="/__order-dev/product-image",variants=(ProductVariant("11","S","size",True),ProductVariant("13","L","size",False)))
def cart(lines):return GuestCart.model_validate({"line_items":lines})
def line(product="10",variant="11",qty=1):return dict(product_id=product,variation_id=variant,quantity=qty)
def test_anonymous_answers_grounded_stock_and_missing_policy():
    chat=GuestShoppingChat(Catalog())
    answer=chat.answer(GuestQuestion(product_id="10",message="재고 있나요"))
    assert "S" in answer["message"] and "품절 옵션: L" in answer["message"]
    assert chat.answer(GuestQuestion(product_id="10",message="내일 배송 보장해"))["action"]=="OPERATOR_REQUIRED"
    assert chat.answer(GuestQuestion(product_id="10",message="이걸로 주문할게요"))["action"]=="START_ORDER"
def test_description_strips_html():
    assert chat_answer("소재 알려줘")["message"]=="린넨 소재"
def chat_answer(message):return GuestShoppingChat(Catalog()).answer(GuestQuestion(product_id="10",message=message))
def test_multi_product_cart_is_quote_only_without_price_authority():
    result=GuestShoppingChat(Catalog()).quote(cart([line(qty=2),line(product="20")]))
    assert result["items_total"]=="87000" and result["order_created"] is False
    assert result["final_total"] is None and result["shipping_fee"] is None
@pytest.mark.parametrize("lines",[[line(variant=None)],[line(variant="13")],[line(),line()],[line(qty=0)],[line(qty=11)]])
def test_invalid_unavailable_or_duplicate_lines_rejected(lines):
    with pytest.raises(ValueError):GuestShoppingChat(Catalog()).quote(cart(lines))
def test_forged_price_and_authority_rejected():
    for field in ("price","customer_id","authenticated","address"):
        with pytest.raises(ValueError):cart([{**line(),field:"forged"}])
def test_mock_catalog_never_answered_as_real_stock():
    class Mock(Catalog):
        def get_product(self,key):return {**super().get_product(key),"source":"demo"}
    with pytest.raises(ValueError):GuestShoppingChat(Mock()).answer(GuestQuestion(product_id="10",message="재고"))
class Boundary:
    def check_origin(self,request,required):
        assert required
        if request.headers.get("origin")!="https://dev.bokstory.duckdns.org":raise ValueError()
def client():
    app=FastAPI();mount_guest_chat(app,catalog=Catalog(),session_boundary=Boundary());return TestClient(app)
def test_guest_routes_need_no_customer_account_and_cannot_create_orders():
    c=client();h={"Origin":"https://dev.bokstory.duckdns.org"}
    assert c.post("/__order-dev/chat/inquiry",json={"product_id":"10","message":"재고"},headers=h).status_code==200
    assert c.post("/__order-dev/chat/quote",json={"line_items":[line()]},headers=h).json()["order_created"] is False
    caps=c.get("/__order-dev/chat/capabilities").json()
    assert caps["phone_verification"] is False and caps["order_confirmation"] is False
    assert c.post("/__order-dev/chat/confirm",json={}).status_code==404
def test_origin_large_body_html_and_quote_rejections():
    c=client();h={"Origin":"https://dev.bokstory.duckdns.org"}
    assert c.post("/__order-dev/chat/inquiry",json={"product_id":"10","message":"재고"}).status_code==422
    assert c.post("/__order-dev/chat/inquiry",content="x"*8193,headers=h).status_code==422
    assert c.post("/__order-dev/chat/quote",json={"line_items":[line(variant="13")]},headers=h).status_code==422
    page=c.get("/__order-dev/chat/product/10")
    assert page.status_code==200 and "<script>unsafe</script>" not in page.text
    assert "&lt;script&gt;unsafe&lt;/script&gt;" in page.text
    assert "/homepage/storefront/my-orders" in page.text and "내 주문·환불/교환" in page.text

from decimal import Decimal
from datetime import datetime,timezone
import json,sqlite3
import pytest
from core.shopping.order_core.guest_checkout import *
from core.shopping.order_core.guest_chat import GuestShoppingChat,GuestQuestion
from test_shop_guest_chat import Catalog
from ops.macos.shopping.dev_guest_checkout import authoritative_quote,verify_delivery_receipt
class LiveCatalog(Catalog):
 def read(self,path):return [dict(id=11,status="publish",stock_status="instock",manage_stock=True,stock_quantity=20,backorders="no",price="29000",attributes=[{"option":"S"}])]
def cart():return GuestCart.model_validate({"line_items":[{"product_id":"10","variation_id":"11","quantity":2}]})
def delivery():return Delivery(recipient="DEV 수령인",postcode="12345",address1="DEV 테스트 배송 주소",address2="테스트")
def draft(store):return store.prepare("customer","session",cart(),delivery(),authoritative_quote(LiveCatalog(),cart()),"+821012345678")
def test_private_delivery_identity_expiry_and_no_client_price(tmp_path):
 now=[100.0];store=PrivateCheckoutStore(tmp_path/"private.sqlite3",clock=lambda:now[0]);d=draft(store)
 assert d["body"]["quote"]["final_total"]=="58000"
 store.confirm(d["draft_id"],"customer","session")
 assert store.operation(d["operation_key"],"customer","session")["digest"]==d["digest"]
 with pytest.raises(ValueError):store.get(d["draft_id"],"other","session")
 with pytest.raises(ValueError):store.get(d["draft_id"],"customer","other")
 now[0]=1000
 with pytest.raises(ValueError):store.get(d["draft_id"],"customer","session")
 assert store.get(d["draft_id"],"customer","session",allow_expired=True)
 assert store.path.stat().st_mode&0o077==0
def test_corrupt_delivery_snapshot_denies(tmp_path):
 store=PrivateCheckoutStore(tmp_path/"private.sqlite3");d=draft(store)
 with sqlite3.connect(store.path) as c:c.execute("UPDATE checkout_delivery SET body='{}'")
 with pytest.raises(ValueError):store.get(d["draft_id"],"customer","session")
@pytest.mark.parametrize("field,value",[("stock_quantity",1),("price","NaN"),("status","draft"),("backorders","yes"),("manage_stock",False)])
def test_final_quote_revalidates_provider_price_and_quantity(field,value):
 class Bad(LiveCatalog):
  def read(self,path):return [{**super().read(path)[0],field:value}]
 with pytest.raises(ValueError):authoritative_quote(Bad(),cart())
def test_receipt_must_match_private_delivery_and_final_amount(tmp_path):
 store=PrivateCheckoutStore(tmp_path/"private.sqlite3");d=draft(store)
 raw={"customer_id":9,"billing":d["body"]["billing"],"shipping":d["body"]["shipping"],"meta_data":[{"key":"_aicc_delivery_digest","value":d["digest"]}],"currency":"KRW","total":"58000","total_tax":"0","shipping_total":"0"}
 verify_delivery_receipt(raw,d,9)
 for field,value in [("total","59000"),("customer_id",8),("shipping",{}),("meta_data",[])]:
  with pytest.raises(ValueError):verify_delivery_receipt({**raw,field:value},d,9)
def test_local_ai_judges_paraphrase_but_cannot_supply_prices_or_authority():
 chat=GuestShoppingChat(Catalog(),intent_classifier=lambda message,product:"STOCK")
 result=chat.answer(GuestQuestion(product_id="10",message="이 옷 작은 걸로 가능한가요"))
 assert result["answer_engine"]=="LOCAL_AI" and "품절 옵션: L" in result["message"]
 for classifier in [lambda m,p:{"intent":"PRICE","price":"1"},lambda m,p:"DELETE_ORDERS"]:
  result=GuestShoppingChat(Catalog(),intent_classifier=classifier).answer(GuestQuestion(product_id="10",message="anything"))
  assert result["answer_engine"]=="LOCAL_AI_UNAVAILABLE" and result["action"]=="OPERATOR_REQUIRED"
def test_delivery_and_confirm_closed_contracts():
 with pytest.raises(ValueError):Delivery(recipient="test",postcode="123",address1="address",phone="forged")
 with pytest.raises(ValueError):CheckoutConfirm(draft_id="a"*48,customer_id="forged")

def test_prepared_delivery_is_not_order_confirmation(tmp_path):
 store=PrivateCheckoutStore(tmp_path/"private.sqlite3");d=draft(store)
 with pytest.raises(ValueError,match="EXPLICIT_CONFIRMATION_REQUIRED"):store.operation(d["operation_key"],"customer","session")
 store.confirm(d["draft_id"],"customer","session")
 assert store.operation(d["operation_key"],"customer","session")["state"]=="CONFIRMED"

@pytest.mark.parametrize("mismatch",[False,True])
def test_delivery_transport_adds_private_snapshot_and_checks_receipt(tmp_path,monkeypatch,mismatch):
 from ops.macos.shopping.dev_guest_checkout import GuestCheckoutWooSession
 from ops.macos.shopping.dev_order_transport import PinnedDevWooOrderSession
 from core.shopping.order_core.woocommerce_writer import WooCommerceOrderWriter
 import requests
 store=PrivateCheckoutStore(tmp_path/"private.sqlite3");d=draft(store);store.confirm(d["draft_id"],"customer","session")
 tag=hashlib.sha256(("aicc-order:"+d["operation_key"]).encode()).hexdigest();captured=[]
 def fake_post(self,url,**kwargs):
  payload=kwargs["json"];captured.append(payload)
  raw={**payload,"currency":"KRW","total":"58000","total_tax":"0","shipping_total":"0"}
  if mismatch:raw["shipping"]={**raw["shipping"],"postcode":"99999"}
  r=requests.Response();r.status_code=201;r._content=json.dumps(raw).encode();r._content_consumed=True;r.iter_content=lambda chunk_size:iter([r._content]);return r
 monkeypatch.setattr(PinnedDevWooOrderSession,"post",fake_post)
 session=GuestCheckoutWooSession(tmp_path/"cert.pem",store=store,provider_customer_id=9)
 payload={"customer_id":9,"line_items":[{"product_id":10,"variation_id":11,"quantity":2}],"meta_data":[{"key":"_aicc_order_operation","value":tag}]}
 if mismatch:
  with pytest.raises(ValueError,match="DELIVERY_MISMATCH"):session.post("https://localhost/wp-json/wc/v3/orders",json=payload)
 else:
  response=session.post("https://localhost/wp-json/wc/v3/orders",json=payload)
  raw=WooCommerceOrderWriter._document(response);assert raw["billing"]["phone"]=="+821012345678"
 assert captured[0]["shipping"]==d["body"]["shipping"]

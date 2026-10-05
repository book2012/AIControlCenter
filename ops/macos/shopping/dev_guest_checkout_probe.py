"""One synthetic-delivery DEV order using an actually phone-verified private session."""
from pathlib import Path
import json,sqlite3,time,requests
from ops.macos.shopping.dev_order_provision import private_write
ROOT=Path("/Users/kyouhan/.config/aicontrolcenter-dev-order")
DATA=Path("/Users/kyouhan/AIControlCenterRuntime/dev-order/data")
def main():
    path=ROOT/"guest-order-live.private.json"
    if path.exists() and json.loads(path.read_text()).get("confirm_attempted"):raise RuntimeError("EXISTING_GUEST_ORDER_INSPECT_ONLY")
    auth=json.loads((ROOT/"phone-live.private.json").read_text())
    cfg=json.loads((ROOT/"commerce.private.json").read_text())
    h={"Origin":"https://dev.bokstory.duckdns.org","Cookie":"__Host-aicc_customer="+auth["customer_cookie"],"X-CSRF-Token":auth["csrf"]}
    base="http://127.0.0.1:18445"
    checked=requests.get(base+"/__order-dev/checkout/session",headers=h,timeout=5)
    if checked.status_code!=200:raise RuntimeError("PHONE_SESSION_REQUIRED_NO_ORDER")
    payload={"cart":{"line_items":[{"product_id":str(cfg["test_product"]["product_id"]),"variation_id":str(cfg["test_product"]["variation_id"]),"quantity":1}]},
        "delivery":{"recipient":"DEV 테스트 수령인","postcode":"12345","address1":"DEV 테스트 배송 주소 · 실제 배송 금지","address2":"테스트 전용"}}
    prepared=requests.post(base+"/__order-dev/checkout/prepare",headers=h,json=payload,timeout=25)
    if prepared.status_code!=200:raise RuntimeError("DEV_DELIVERY_PREPARATION_DENIED")
    state=prepared.json();state["confirm_attempted"]=True;private_write(path,state)
    response=requests.post(base+"/__order-dev/checkout/confirm",headers=h,json={"draft_id":state["draft_id"]},timeout=60)
    state["confirm_http"]=response.status_code;state["result"]=response.json();private_write(path,state)
    if response.status_code!=201:raise RuntimeError("GUEST_ORDER_INSPECTION_REQUIRED_NO_RETRY")
    replay=requests.post(base+"/__order-dev/checkout/confirm",headers=h,json={"draft_id":state["draft_id"]},timeout=15)
    if replay.status_code!=200 or replay.json().get("idempotent_replay") is not True:raise RuntimeError("GUEST_REPLAY_INSPECTION_REQUIRED")
    with sqlite3.connect("file:"+str(DATA/"orders.sqlite3")+"?mode=ro",uri=True) as c:
        reference=c.execute("SELECT reference FROM shopping_order_operator_review WHERE operation_key=?",(state["operation_key"],)).fetchone()[0]
    state["operator_reference"]=reference;private_write(path,state)
    outbox=None
    for _ in range(20):
        with sqlite3.connect("file:"+str(DATA/"orders.sqlite3")+"?mode=ro",uri=True) as c:
            outbox=c.execute("SELECT state,message_id FROM shopping_order_notification_outbox WHERE operation_key=? AND event_type='ORDER_CREATED'",(state["operation_key"],)).fetchone()
        if outbox and outbox[0] in ("SENT","UNKNOWN","FAILED"):break
        time.sleep(1)
    print(json.dumps({"dev_order_http":response.status_code,"provider_order_id":state["result"]["provider_order_id"],
        "total":state["result"]["total"],"replay_http":replay.status_code,"telegram_state":outbox[0] if outbox else None,
        "telegram_message_id":outbox[1] if outbox else None,"operator_reference":reference,"actual_phone_session_used":True,
        "delivery":"synthetic DEV test only","prod_mutation":False},ensure_ascii=False))
if __name__=="__main__":main()

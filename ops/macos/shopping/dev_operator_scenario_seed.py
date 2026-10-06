"""Create idempotent synthetic DEV operations for operator UI/Telegram acceptance.

Creates no real SMS, payment, carrier request, refund, or PROD mutation.
"""
from pathlib import Path
import hashlib,json,os,secrets,sqlite3,subprocess,sys,uuid
from datetime import datetime,timedelta,timezone
from pydantic import SecretStr

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))

from core.shopping.customer_identity import Customer,VerifiedContactBinding
from core.shopping.customer_persistence import SQLiteCustomerSessionStore
from core.shopping.order_core import SQLiteOrderCreateLedger
from core.shopping.order_core.catalog import ShoppingServiceOrderCatalogResolver
from core.shopping.order_core.create import OrderCreateAuthority,OrderCreateCommand,OrderCreateLine,OrderCreateService
from core.shopping.order_core.guest_chat import GuestCart
from core.shopping.order_core.guest_checkout import Delivery,PrivateCheckoutStore,fingerprint
from core.shopping.order_core.ledger import _decode_result,_utc
from core.shopping.order_core.telegram import OrderTelegramTransport
from core.shopping.order_core.woocommerce_writer import WooCommerceOrderWriter,ProviderOrderWritePermit
from ops.macos.shopping.dev_aftersales import DevAftersalesStore
from ops.macos.shopping.dev_guest_checkout import GuestCheckoutWooSession,authoritative_quote
from ops.macos.shopping.dev_inquiry_queue import DevInquiryQueue
from ops.macos.shopping.dev_order_operator import DevStockConfirmation
from ops.macos.shopping.dev_order_provision import PRIVATE,RUNTIME,private_write
from ops.macos.shopping.dev_order_runtime import DATA,DevCatalog,assert_isolation,private_config

STATE=PRIVATE/"operator-scenario.private.json"
PHONE="+821000000000"
PHONE_LOCAL="01000000000"
DOCKER=["docker","--context","colima-aicontrolcenter-commerce"]
CONTAINER="aicc-order-dev-wordpress-1"

def utcnow():return datetime.now(timezone.utc)
def ref(prefix):return prefix+"-"+uuid.uuid4().hex
def load_state():
    if STATE.exists():return json.loads(STATE.read_text())
    return {"schema_version":1,"environment":"DEV","synthetic_phone":PHONE_LOCAL,"orders":{},"inquiries":{}}

def provider_customer(state):
    existing=state.get("provider_customer_id")
    if isinstance(existing,int) and existing>0:return existing
    payload=json.dumps({"username":"aicc-dev-synthetic-operator-scenario","password":secrets.token_urlsafe(40)})
    import base64
    encoded=base64.b64encode(payload.encode()).decode()
    php=f"""<?php
if(getenv('WORDPRESS_DB_NAME')!=='aicc_order_dev'){{exit(2);}}
require '/var/www/html/wp-load.php'; add_filter('pre_wp_mail',fn()=>false);
$c=json_decode(base64_decode('{encoded}'),true);$u=get_user_by('login',$c['username']);
if(!$u){{$id=wp_create_user($c['username'],$c['password'],$c['username'].'@example.invalid');if(is_wp_error($id)){{exit(3);}}$u=get_user_by('id',$id);$u->set_role('customer');}}
if(!in_array('customer',$u->roles,true)){{exit(4);}} echo json_encode(['customer_id'=>$u->ID]);
?>"""
    r=subprocess.run(DOCKER+["exec","-i",CONTAINER,"php"],input=php,capture_output=True,text=True,timeout=30)
    if r.returncode:raise RuntimeError("DEV_SCENARIO_PROVIDER_CUSTOMER_FAILED")
    try:value=json.loads(r.stdout)
    except Exception:raise RuntimeError("DEV_SCENARIO_PROVIDER_CUSTOMER_FAILED") from None
    cid=value.get("customer_id")
    if type(cid) is not int or cid<=0:raise RuntimeError("DEV_SCENARIO_PROVIDER_CUSTOMER_FAILED")
    state["provider_customer_id"]=cid
    return cid

def identity(state):
    stamp=utcnow()
    customer_id=state.setdefault("customer_id","AG-CUS-"+uuid.uuid4().hex)
    contact_ref=state.setdefault("contact_ref","AG-CON-"+uuid.uuid4().hex)
    store=SQLiteCustomerSessionStore(DATA/"customers.sqlite3")
    customer=Customer(id=customer_id,state="ACTIVE",created_at=stamp,updated_at=stamp,
        contact_binding=VerifiedContactBinding(customer_id=customer_id,state="VERIFIED",created_at=stamp,
            updated_at=stamp,verified_at=stamp,contact_ref=contact_ref))
    store.save_customer(customer,contact_ref=contact_ref)
    state["verified_fixture"]=True
    state["verified_at"]=stamp.isoformat().replace("+00:00","Z")
    return customer_id

def product_maps(cfg):
    rows=cfg.get("active_products") or []
    if len(rows)<5:raise RuntimeError("DEV_MULTI_PRODUCT_CATALOG_REQUIRED")
    return {v["demo_id"]:v for v in rows}

def line(products,demo,label,qty=1):
    binding=products[demo]
    matches=[v for v in binding["variants"] if v["label"]==label and v["available"]]
    if len(matches)!=1:raise RuntimeError("DEV_SCENARIO_VARIATION_UNAVAILABLE")
    return {"product_id":str(binding["product_id"]),"variation_id":str(matches[0]["id"]),"quantity":qty}

def make_writer(ledger,checkout,catalog,commerce,customer_id,session_id,provider_customer_id):
    def authorize(command,stamp):
        operation=ledger.inspect_operation(command.idempotency_key)
        if operation is None or operation["state"]!="CLAIMED" or operation["customer_id"]!=customer_id or operation["session_id"]!=session_id or operation["command_digest"]!=command.command_digest:
            raise ValueError("SCENARIO_OPERATION_DENIED")
        draft=checkout.operation(command.idempotency_key,customer_id,session_id)
        expected=[(v["product_id"],v["variation_id"],v["quantity"]) for v in draft["body"]["line_items"]]
        actual=[(v.product_id,v.variation_id,v.quantity) for v in command.line_items]
        if actual!=expected:raise ValueError("SCENARIO_LINE_BINDING_DENIED")
        current=authoritative_quote(catalog,GuestCart.model_validate({"line_items":draft["body"]["line_items"]}))
        if fingerprint(current)!=fingerprint(draft["body"]["quote"]):raise ValueError("SCENARIO_QUOTE_CHANGED")
        return ProviderOrderWritePermit(customer_id,session_id,command.idempotency_key,command.command_digest,
            "isolated-dev-scenario",stamp,stamp+timedelta(seconds=30))
    return WooCommerceOrderWriter(base_url="https://localhost",consumer_key=SecretStr(commerce["consumer_key"]),
        consumer_secret=SecretStr(commerce["consumer_secret"]),ledger=ledger,clock=utcnow,authorize_once=authorize,
        resolve_customer=lambda value:provider_customer_id if value==customer_id else (_ for _ in ()).throw(ValueError()),
        session=GuestCheckoutWooSession(PRIVATE/"dev-woo-cert.pem",store=checkout,provider_customer_id=provider_customer_id))

def create_order(name,spec,*,state,products,catalog,checkout,ledger,service,customer_id,session_id):
    saved=state["orders"].get(name)
    if saved:
        op=ledger.inspect_operation(saved["operation_key"])
        if op and op.get("state")=="COMPLETED":return saved
        raise RuntimeError("DEV_SCENARIO_STATE_DRIFT")
    cart=GuestCart.model_validate({"line_items":[line(products,*item) for item in spec["lines"]]})
    quote=authoritative_quote(catalog,cart)
    delivery=Delivery(recipient="DEV 테스트 고객",postcode="00000",address1="서울특별시 테스트구 테스트로 "+str(spec["address_no"]),address2=str(spec["address_no"])+"01호")
    draft=checkout.prepare(customer_id,session_id,cart,delivery,quote,PHONE)
    checkout.confirm(draft["draft_id"],customer_id,session_id)
    requested=utcnow()
    command=OrderCreateCommand(customer_id=customer_id,
        line_items=tuple(OrderCreateLine(v.product_id,v.variation_id,v.quantity) for v in cart.line_items),
        idempotency_key=draft["operation_key"],correlation_id=ref("scenario-corr"),audit_reference=ref("scenario-audit"),requested_at=requested)
    authority=OrderCreateAuthority(customer_id=customer_id,session_id=session_id,authorization_reference=ref("scenario-auth"),
        authorized_at=requested,expires_at=requested+timedelta(seconds=30))
    result=service.execute(command,authority)
    saved={"operation_key":draft["operation_key"],"provider_order_id":result.snapshot.provider_order_id,
        "scenario":name,"phone":PHONE_LOCAL,"desired_state":spec["state"]}
    state["orders"][name]=saved;private_write(STATE,state)
    return saved

def review_transition(ledger,checkout,saved,target):
    key=saved["operation_key"]
    connection=ledger._connect(read_only=True)
    try:
        ledger._validate(connection)
        row=connection.execute("SELECT r.state,o.result_json FROM shopping_order_operator_review r JOIN shopping_order_create_operations o ON o.operation_key=r.operation_key WHERE r.operation_key=?",(key,)).fetchone()
        if row is None:raise RuntimeError("DEV_SCENARIO_REVIEW_MISSING")
        current=row["state"];result=_decode_result(row["result_json"])
    finally:connection.close()
    if current==target:return
    if current!="PENDING_REVIEW":raise RuntimeError("DEV_SCENARIO_REVIEW_CONFLICT")
    if target=="CONFIRMED" and not DevStockConfirmation(store=checkout)(key,result):
        raise RuntimeError("DEV_SCENARIO_STOCK_CONFIRMATION_FAILED")
    now=ledger._now();connection=ledger._connect()
    try:
        ledger._validate(connection);connection.execute("BEGIN IMMEDIATE")
        changed=connection.execute("UPDATE shopping_order_operator_review SET state=?,actor_reference=?,decision_at=? WHERE operation_key=? AND state='PENDING_REVIEW'",
            (target,"dev-scenario-seed",_utc(now),key)).rowcount
        if changed!=1:raise RuntimeError("DEV_SCENARIO_REVIEW_CONFLICT")
        ledger._audit(connection,key,"OPERATOR_"+target,now,reason_code=target)
        ledger._enqueue_notification(connection,key,"OPERATOR_"+target,now,result,
            connection.execute("SELECT reference FROM shopping_order_operator_review WHERE operation_key=?",(key,)).fetchone()[0],
            review_state=target)
        connection.commit()
    except Exception:
        if connection.in_transaction:connection.rollback()
        raise
    finally:connection.close()

def inquiries(state,transport,products):
    q=DevInquiryQueue(DATA/"inquiries.sqlite3",transport)
    specs={
      "pending_delivery":{"product":str(products["oc-demo-dress-0001"]["product_id"]),"question":"배송 후 주소 변경이나 수령 방법 변경이 가능한가요?","answer":None},
      "approved_care":{"product":str(products["oc-demo-top-0001"]["product_id"]),"question":"세탁은 어떻게 하는 게 좋아요?","answer":"찬물로 단독 손세탁하고 자연 건조를 권장합니다."},
      "pending_return":{"product":str(products["oc-demo-bottom-0001"]["product_id"]),"question":"사이즈가 안 맞으면 교환 배송비와 절차는 어떻게 되나요?","answer":None},
    }
    for index,(name,spec) in enumerate(specs.items(),start=1):
        if name in state["inquiries"]:continue
        ticket=q.submit(spec["product"],spec["question"])
        if spec["answer"]:
            q.command("문의 #"+ticket["inquiry_id"]+" 답변 "+spec["answer"],900000000+index)
        state["inquiries"][name]={"id":ticket["inquiry_id"],"product":spec["product"],"state":"APPROVED" if spec["answer"] else "PENDING"}
        private_write(STATE,state)
    q.export(DATA/"inquiry-learning.jsonl")

def main():
    assert_isolation()
    state=load_state();cfg=private_config("runtime.private.json");commerce=private_config("commerce.private.json")["woocommerce"];tg=private_config("telegram.private.json")
    if cfg.get("environment")!="DEV" or commerce.get("confirmed_isolated_from_prod") is not True:raise RuntimeError("DEV_ONLY_REQUIRED")
    products=product_maps(cfg);customer_id=identity(state);provider_customer_id=provider_customer(state)
    session_id=state.setdefault("session_id","AG-SES-"+uuid.uuid4().hex);private_write(STATE,state)
    checkout=PrivateCheckoutStore(DATA/"guest-checkout.sqlite3");ledger=SQLiteOrderCreateLedger(DATA/"orders.sqlite3",clock=utcnow);ledger.initialize()
    catalog=DevCatalog(commerce,cfg);writer=make_writer(ledger,checkout,catalog,commerce,customer_id,session_id,provider_customer_id)
    service=OrderCreateService(catalog_resolver=ShoppingServiceOrderCatalogResolver(catalog),order_creator=writer,coordinator=ledger)
    scenarios={
      "pending":{"state":"PENDING_REVIEW","lines":[("oc-demo-bottom-0001","S",1)],"address_no":1},
      "ready":{"state":"CONFIRMED","lines":[("oc-demo-outer-0001","M",1)],"address_no":2},
      "shipping":{"state":"SHIPPED","lines":[("oc-demo-dress-0001","S",1),("oc-demo-bag-0001","FREE",1)],"address_no":3},
      "completed":{"state":"DELIVERED","lines":[("oc-demo-top-0001","S",1)],"address_no":4},
      "rejected":{"state":"REJECTED","lines":[("oc-demo-bottom-0001","L",1)],"address_no":5},
    }
    created={}
    for name,spec in scenarios.items():
        saved=create_order(name,spec,state=state,products=products,catalog=catalog,checkout=checkout,ledger=ledger,service=service,customer_id=customer_id,session_id=session_id)
        created[name]=saved
        if spec["state"] in ("CONFIRMED","SHIPPED","DELIVERED"):review_transition(ledger,checkout,saved,"CONFIRMED")
        elif spec["state"]=="REJECTED":review_transition(ledger,checkout,saved,"REJECTED")
    aftersales=DevAftersalesStore(DATA/"aftersales.sqlite3",DATA/"aftersales-files",ledger=ledger,checkout=checkout,catalog=catalog)
    for name in ("shipping","completed"):
        oid=created[name]["provider_order_id"];current=aftersales.admin_fulfillment(oid)
        if current["state"]=="NOT_SHIPPED":aftersales.mark_shipped(oid,"DEV택배","DEV-"+str(oid)+"-TRACK")
        if name=="completed" and aftersales.admin_fulfillment(oid)["state"]!="DELIVERED":aftersales.mark_delivered(oid)
    completed=created["completed"]
    if not state.get("return_case_id"):
        case=aftersales.create_case(customer_id,{"order_id":completed["provider_order_id"],"kind":"RETURN","reason":"DEV 테스트용 단순 변심 환불 요청","target_variation_id":None})
        state["return_case_id"]=case["id"];private_write(STATE,state)
    transport=OrderTelegramTransport(token=SecretStr(tg["bot_token"]),chat_id=tg["operator_chat_id"])
    inquiries(state,transport,products)
    print(json.dumps({"synthetic_verified_phone":PHONE_LOCAL,"customer_id":customer_id,
        "orders":created,"return_case_id":state.get("return_case_id"),"inquiries":state["inquiries"],
        "external_sms":False,"payment":False,"carrier_api":False,"production_mutation":False},ensure_ascii=False))

if __name__=="__main__":main()

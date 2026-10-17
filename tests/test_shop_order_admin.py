from types import SimpleNamespace
import sqlite3
from fastapi import FastAPI
from fastapi.testclient import TestClient
from ops.macos.shopping.dev_order_admin import mount_admin

def test_admin_console_lists_orders_without_address_and_detail_on_demand():
    adapter=SimpleNamespace(
        admin_orders=lambda limit:[{"order_id":15,"phone":"01012345678","state":"CONFIRMED","requested_at":"2026-10-06T00:00:00Z",
            "total":"29000","currency":"KRW","items":[{"name":"블라우스","option":"S","quantity":1}]}],
        admin_detail=lambda order_id:{"order_id":15,"phone":"01012345678","state":"CONFIRMED","requested_at":"2026-10-06T00:00:00Z",
            "total":"29000","currency":"KRW","items":[{"name":"블라우스","option":"S","quantity":1}],
            "delivery":{"recipient":"테스트 고객","postcode":"12345","address1":"서울 테스트로 1","address2":"101호"}} if order_id==15 else None)
    queue=SimpleNamespace(admin_rows=lambda limit:[{"id":"abcdef12","product":"10","question":"교환 기간?","answer":"14일 이내입니다.",
        "state":"APPROVED","delivery":"SENT","created":1.0,"answered":2.0,"approved":2.0}])
    aftersales=SimpleNamespace(admin_fulfillment=lambda order_id:{"state":"DELIVERED"},admin_cases=lambda:[{"id":"deadbeef","order_id":15,"kind":"RETURN","state":"REQUESTED","reason":"변심","target_option":None,"attachments":1}])
    app=FastAPI();mount_admin(app,operator_adapter=adapter,inquiry_queue=queue,aftersales=aftersales)
    with TestClient(app) as client:
        page=client.get("/dev-order/admin")
        assert page.status_code==200 and "DEV 주문 관리자" in page.text and "상세·주소" in page.text
        assert "주문·상품 챗봇" in page.text and "Codex 초안 검토" in page.text
        assert 'lines.join("\\n")' in page.text and '.join("\\n")' in page.text
        orders=client.get("/__order-dev/admin/orders")
        assert orders.status_code==200 and "delivery" not in orders.text and "테스트로" not in orders.text
        assert orders.json()["orders"][0]["fulfillment"]["state"]=="DELIVERED"
        cases=client.get("/__order-dev/admin/aftersales").json()["cases"];assert cases[0]["id"]=="deadbeef" and cases[0]["attachments"]==1
        detail=client.get("/__order-dev/admin/orders/15")
        assert detail.status_code==200 and detail.json()["delivery"]["address1"]=="서울 테스트로 1"
        assert client.get("/__order-dev/admin/orders/999").status_code==404
        inquiries=client.get("/__order-dev/admin/inquiries").json()["inquiries"]
        assert inquiries[0]["state"]=="APPROVED" and inquiries[0]["answer"]=="14일 이내입니다."


def test_admin_chat_is_same_origin_and_routes_to_dev_operator(tmp_path):
    class Conversation:
        path=tmp_path/"dialogue.sqlite3"
        def __init__(self):self.calls=[]
        def handle(self,text,update_id,actor):
            self.calls.append((text,update_id,actor))
            return "주문을 조회했습니다."
    conversation=Conversation()
    adapter=SimpleNamespace(admin_orders=lambda limit:[],admin_detail=lambda order_id:None)
    queue=SimpleNamespace(admin_rows=lambda limit:[])
    app=FastAPI()
    mount_admin(app,operator_adapter=adapter,inquiry_queue=queue,conversation=conversation)
    with TestClient(app) as client:
        denied=client.post("/__order-dev/admin/chat",json={"text":"주문 목록"})
        assert denied.status_code==403
        result=client.post("/__order-dev/admin/chat",json={"text":"주문 목록"},headers={"Origin":"https://dev.bokstory.duckdns.org"})
        assert result.status_code==200 and result.json()["reply"]=="주문을 조회했습니다."
        assert conversation.calls[0][0]=="주문 목록"
        assert conversation.calls[0][2]=="telegram-user-9223372036854775807"


def test_codex_product_intake_is_queued_without_woocommerce_write(tmp_path):
    db=tmp_path/"dialogue.sqlite3"
    with sqlite3.connect(db) as c:
        c.execute("CREATE TABLE website_jobs(id TEXT PRIMARY KEY,actor TEXT NOT NULL,request TEXT NOT NULL,state TEXT NOT NULL,created REAL NOT NULL)")
    conversation=SimpleNamespace(path=db)
    codex=SimpleNamespace(root=tmp_path/"codex")
    adapter=SimpleNamespace(admin_orders=lambda limit:[],admin_detail=lambda order_id:None)
    queue=SimpleNamespace(admin_rows=lambda limit:[])
    app=FastAPI()
    mount_admin(app,operator_adapter=adapter,inquiry_queue=queue,conversation=conversation,codex_drafts=codex)
    with TestClient(app) as client:
        response=client.post("/__order-dev/admin/product-drafts",json={"text":"상품 등록: 린넨 셔츠"},headers={"Origin":"https://dev.bokstory.duckdns.org"})
        assert response.status_code==202
        job=response.json()["job_id"]
        with sqlite3.connect(db) as c:
            row=c.execute("SELECT request,state FROM website_jobs WHERE id=?",(job,)).fetchone()
        assert row==("PRODUCT_INTAKE::상품 등록: 린넨 셔츠","WAITING_CODEX")
        candidate=codex.root/job/"brands/agachichi/catalog/intake-drafts"/(job+".json")
        candidate.parent.mkdir(parents=True)
        candidate.write_text('{"schema_version":1,"environment":"DEV","job_id":"'+job+'","request_summary":"테스트","proposed_copy":{"description":"문안","style_tip":""},"provided_facts":[],"missing_facts":["price"],"questions":["가격은 얼마인가요?"],"review_required":true}',encoding="utf-8")
        with sqlite3.connect(db) as c:c.execute("UPDATE website_jobs SET state='PRODUCT_REVIEW_REQUIRED' WHERE id=?",(job,))
        status=client.get("/__order-dev/admin/product-drafts/"+job)
        assert status.status_code==200 and status.json()["draft"]["job_id"]==job
        assert client.get("/__order-dev/admin/product-drafts/../bad").status_code in {404,422}

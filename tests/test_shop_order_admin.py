from types import SimpleNamespace
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

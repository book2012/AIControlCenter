from core.homepage.preview import create_app
from fastapi.testclient import TestClient


def test_inquiry_contract_resolves_canonical_product_variant_and_kakao():
    with TestClient(create_app()) as client:
        channels = client.get("/shopping/contact-channels")
        assert channels.status_code == 200
        assert channels.json()["items"] == [{"type": "kakao_openchat", "label": "카카오 오픈채팅", "url": "https://open.kakao.com/o/sV26tFNi", "enabled": True}]
        missing = client.post("/shopping/inquiries", json={"product_id": "oc-demo-top-0001"})
        assert missing.status_code == 422 and missing.json()["detail"]["code"] == "shopping_variant_required"
        created = client.post("/shopping/inquiries", json={"product_id": "oc-demo-top-0001", "variant_id": "oc-demo-top-0001-m", "message": "<script>alert(1)</script>"})
        assert created.status_code == 200
        payload = created.json()
        assert payload["id"].startswith("AG-INQ-") and payload["product"] == {"id": "oc-demo-top-0001", "name": "소프트 린넨 블라우스"}
        assert payload["variant"] == {"id": "oc-demo-top-0001-m", "label": "M"}
        assert "<script>" not in payload["formatted_message"] and payload["id"] in payload["formatted_message"] and "선택 사이즈: M" in payload["formatted_message"]
        fetched = client.get(f"/shopping/inquiries/{payload['id']}").json()
        assert fetched == {**payload, "public_access_token": None}
        assert payload["public_access_token"] and client.post(f"/shopping/inquiries/{payload['id']}/messages", headers={"X-Inquiry-Access-Token": payload["public_access_token"]}, json={"body": "추가 문의"}).status_code == 200


def test_inquiry_rejects_fabricated_or_cross_product_variants_and_uses_empty_variant_state():
    with TestClient(create_app()) as client:
        assert client.post("/shopping/inquiries", json={"product_id": "oc-demo-top-0001", "variant_id": "fake", "name": "fake"}).status_code == 422
        assert client.post("/shopping/inquiries", json={"product_id": "oc-demo-top-0001", "variant_id": "oc-demo-top-0002-free"}).status_code == 422
        no_variant = client.post("/shopping/inquiries", json={"product_id": "oc-demo-top-0003"})
        assert no_variant.status_code == 200 and no_variant.json()["variant"] is None and "선택 사이즈:" not in no_variant.json()["formatted_message"]
        assert client.post("/shopping/inquiries", json={"product_id": "no-such-product"}).status_code == 404

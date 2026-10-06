from types import SimpleNamespace
import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from core.homepage.preview import create_app
from core.homepage import storefront_gallery
from ops.macos.shopping.dev_chat_history import DevChatHistory,mount_history,COOKIE

@pytest.mark.parametrize("url",["/homepage/storefront","/homepage/storefront/search","/homepage/storefront/my-orders","/homepage/storefront/product/ag-upload-outer-0001","/homepage/storefront/product/ag-upload-outer-0002"])
def test_one_shared_chat_on_customer_pages(url):
    with TestClient(create_app()) as c:
        r=c.get(url)
        assert r.status_code==200
        assert r.text.count('id="shop-chat"')==1
        assert r.text.count('id="shop-chat-form"')==1
        assert 'id="inquiry-section"' not in r.text
        assert 'storefront-chat.js' in r.text
        assert 'id="shop-chat-stock"' in r.text
        if "/product/" in url:
            pid=url.rsplit("/",1)[1]
            assert f'data-context="{pid}"' in r.text
            assert 'data-shop-chat-product=' not in r.text
            assert "제품 문의는 챗봇으로 해주세요." in r.text
            assert r.text.index('id="description-section"') < r.text.index('id="commerce-panel"')
            assert 'id="detail-image"' in r.text and 'model-hero-caption' in r.text

@pytest.mark.parametrize("pid",["ag-upload-outer-0001","ag-upload-outer-0002"])
def test_gallery_preserves_original_and_labels_model_angles(pid):
    rows=storefront_gallery.for_product(pid)
    assert [r["kind"] for r in rows]==["original","model-angles"]
    assert not rows[0]["ai_generated"] and rows[1]["ai_generated"]
    with TestClient(create_app()) as c:
        r=c.get("/homepage/storefront/product/"+pid)
        assert "고객이 올린 실제 사진" in r.text and "AI 예상 이미지" in r.text
        for row in rows:
            response=c.get(row["url"])
            assert response.status_code==200 and response.content==row["path"].read_bytes()
        assert c.get("/homepage/assets/storefront/gallery/not-listed.jpg").status_code==404

def test_gallery_corrupt_manifest_fails_closed(tmp_path,monkeypatch):
    monkeypatch.setattr(storefront_gallery,"MANIFEST",tmp_path/"gallery.json")
    storefront_gallery.MANIFEST.write_text('{"environment":"PROD","schema_version":1,"assets":[]}')
    assert storefront_gallery.assets()=={}

@pytest.fixture
def history(tmp_path):
    identity={"id":None,"csrf":False}
    def authenticate(request,write=False):
        if identity["id"] is None or write and not identity["csrf"]:raise ValueError("AUTH")
        return SimpleNamespace(customer_id=identity["id"])
    store=DevChatHistory(tmp_path/"history.sqlite3",authenticate,"phone-customer")
    app=FastAPI();mount_history(app,store)
    with TestClient(app,base_url="https://testserver") as c:yield store,c,identity

def test_anonymous_records_require_phone_and_csrf_before_claim(history):
    store,c,identity=history
    assert c.get("/__order-dev/chat/history").status_code==401
    assert c.get("/__order-dev/chat/history/session").status_code==200
    token=c.cookies.get(COOKIE)
    request=SimpleNamespace(cookies={COOKIE:token})
    assert store.record(request,SimpleNamespace(product_id="41",message="M 재고 있나요?"),{"message":"M 1개","action":"ANSWER"})
    assert c.post("/__order-dev/chat/history/link").status_code==403
    identity["id"]="phone-customer"
    assert c.get("/__order-dev/chat/history").json()["items"]==[]
    assert c.post("/__order-dev/chat/history/link").status_code==403
    identity["csrf"]=True
    assert c.post("/__order-dev/chat/history/link").status_code==200
    assert c.post("/__order-dev/chat/history/link").status_code==200
    items=c.get("/__order-dev/chat/history").json()["items"]
    assert len(items)==1 and items[0]["product_id"]=="41"
    identity["id"]=None
    assert c.get("/__order-dev/chat/history").status_code==401
    assert not store.record(request,SimpleNamespace(product_id="41",message="unowned"),{"message":"x","action":"ANSWER"})

def test_owner_isolation_rotation_and_private_file_permissions(history):
    store,c,identity=history
    token=store.open(None)
    store.claim(token,"owner-a")
    with pytest.raises(ValueError):store.claim(token,"owner-b")
    assert store.open(token,None)!=token
    assert store.open(token,"owner-a")==token
    assert store.recent("owner-b")==[]
    assert store.path.stat().st_mode & 0o077==0
    identity["id"]="synthetic-fixture";identity["csrf"]=True
    assert c.get("/__order-dev/chat/history").status_code==401

def test_history_retention_and_bounded_recent(history):
    store,c,identity=history
    token=store.open(None);req=SimpleNamespace(cookies={COOKIE:token})
    for n in range(35):
        assert store.record(req,SimpleNamespace(product_id="41",message=str(n)),{"message":"reply","action":"ANSWER"})
    store.claim(token,"phone-customer")
    rows=store.recent("phone-customer")
    assert len(rows)==30 and rows[0]["question"]=="34" and rows[-1]["question"]=="5"
    with store.db() as connection:connection.execute("UPDATE turns SET created=0")
    assert store.recent("phone-customer")==[]


def test_operator_answer_in_phone_history_is_server_authoritative(history):
    store,c,identity=history
    token=store.open(None);request=SimpleNamespace(cookies={COOKIE:token})
    ticket="a"*48
    assert store.record(request,SimpleNamespace(product_id="41",message="추가 질문"),{"message":"운영자 확인 중","action":"OPERATOR_QUEUED","inquiry_token":ticket})
    store.claim(token,"phone-customer")
    store.answer_lookup=lambda key:"운영자가 확인한 답변" if key==ticket else None
    item=store.recent("phone-customer")[0]
    assert item["answer"]=="운영자가 확인한 답변" and item["action"]=="OPERATOR_ANSWERED"
    assert "ticket" not in item and "token" not in item


def test_gallery_directory_symlink_fails_closed(tmp_path,monkeypatch):
    import hashlib
    outside=tmp_path/"outside";outside.mkdir()
    name="ag-upload-outer-0001-original.jpg";data=b"image"
    (outside/name).write_bytes(data)
    root=tmp_path/"repo";base=root/"brands/agachichi/assets/media/uploads";base.mkdir(parents=True)
    (base/"gallery").symlink_to(outside,target_is_directory=True)
    manifest=base/"gallery.json"
    manifest.write_text(json.dumps({"environment":"DEV","schema_version":1,"assets":[{"product_id":"ag-upload-outer-0001","kind":"original","ai_generated":False,"label":"original","path":"brands/agachichi/assets/media/uploads/gallery/"+name,"sha256":hashlib.sha256(data).hexdigest()}]}))
    monkeypatch.setattr(storefront_gallery,"ROOT",root);monkeypatch.setattr(storefront_gallery,"MANIFEST",manifest)
    assert storefront_gallery.assets()=={}

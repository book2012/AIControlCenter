from types import SimpleNamespace
from html import unescape
import json
import re
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from core.homepage.preview import create_app
from core.homepage import storefront_gallery
from ops.macos.shopping.dev_chat_history import DevChatHistory,mount_history,COOKIE

@pytest.mark.parametrize("url",["/homepage/storefront","/homepage/storefront/search","/homepage/storefront/my-orders","/homepage/storefront/cart","/homepage/storefront/checkout","/homepage/storefront/guest-order","/homepage/storefront/product/ag-upload-outer-0001","/homepage/storefront/product/ag-upload-outer-0002"])
def test_one_shared_chat_on_customer_pages(url):
    with TestClient(create_app()) as c:
        r=c.get(url)
        assert r.status_code==200
        assert r.text.count('id="shop-chat"')==1
        assert r.text.count('id="shop-chat-form"')==1
        assert 'id="inquiry-section"' not in r.text
        assert 'storefront-chat.js' in r.text
        assert 'id="shop-chat-stock"' not in r.text
        assert 'id="shop-chat-product"' not in r.text
        if "/product/" in url:
            pid=url.rsplit("/",1)[1]
            assert f'data-context="{pid}"' in r.text
            assert 'data-shop-chat-product=' not in r.text
            assert "제품 문의는 챗봇으로 해주세요." in r.text
            assert r.text.index('id="variant-section"') < r.text.index('id="commerce-panel"') < r.text.index('id="description-section"')
            assert 'id="detail-image"' in r.text and 'model-hero-caption' in r.text

@pytest.mark.parametrize("url,kind",[
    ("/homepage/storefront","home"),
    ("/homepage/storefront/search?category=women-outer&q=coat","search"),
    ("/homepage/storefront/cart","cart"),
    ("/homepage/storefront/my-orders","orders"),
    ("/homepage/storefront/checkout","checkout"),
])
def test_chat_carries_only_page_guidance_and_relevant_questions(url,kind):
    with TestClient(create_app()) as c:
        response=c.get(url)
    assert response.status_code==200
    match=re.search(r'<dialog[^>]+data-page-context="([^"]+)"',response.text)
    assert match
    context=json.loads(unescape(match.group(1)))
    assert context["type"]==kind and context["title"]
    assert context["questions"]
    assert all(set(item)=={"label","text","action"} for item in context["questions"])
    assert not any(key in json.dumps(context).lower() for key in ("phone","address","postcode","recipient"))


def test_checkout_separates_member_entry_and_guest_order_page():
    with TestClient(create_app()) as c:
        entry=c.get("/homepage/storefront/checkout")
        guest=c.get("/homepage/storefront/guest-order")
    assert entry.status_code==guest.status_code==200
    assert entry.text.index('class="checkout-login-button"') < entry.text.index('class="checkout-guest-button"')
    assert 'href="/homepage/storefront/guest-order"' in entry.text
    assert 'id="phone-form"' not in entry.text
    assert 'data-guest-order-page="true"' in guest.text
    assert 'id="phone-form"' in guest.text and 'id="delivery-form"' in guest.text
    assert '비회원 주문' in guest.text and '회원이신가요?' not in guest.text


def test_product_chat_includes_public_product_summary_before_questions():
    with TestClient(create_app()) as c:
        response=c.get("/homepage/storefront/product/ag-upload-outer-0001")
    assert response.status_code==200
    match=re.search(r'data-page-context="([^"]+)"',response.text)
    assert match
    context=json.loads(unescape(match.group(1)))
    assert context["product"]["name"] and context["product"]["price"]
    assert context["product"]["options"] and context["product"]["questions"]
    assert context["product"]["description"]
    assert "availability" not in context["product"]
    assert all(set(item)=={"label","text","action"} for item in context["product"]["questions"])
    assert not any("재고" in item["label"] or "재고" in item["text"] for item in context["product"]["questions"])
    assert 'id="shop-chat-product"' not in response.text
    assert 'id="shop-chat-stock"' not in response.text

@pytest.mark.parametrize("pid",["ag-upload-outer-0001","ag-upload-outer-0002"])
def test_gallery_preserves_original_and_labels_model_angles(pid):
    rows=storefront_gallery.for_product(pid)
    assert [r["kind"] for r in rows]==["garment-cutout","model-other"]
    assert all(row["ai_generated"] for row in rows)
    with TestClient(create_app()) as c:
        r=c.get("/homepage/storefront/product/"+pid)
        assert "기존 사진 보정본" in r.text and "AI 예상 이미지" in r.text
        assert pid+"-original.jpg" not in r.text
        assert r.text.index("상세설명") < r.text.index(pid+"-garment-cutout.webp") < r.text.index(pid+"-model-other.jpg")
        assert pid+"-model-front.jpg" in r.text
        original=storefront_gallery.assets()[pid+"-original.jpg"]
        assert original["path"].is_file()
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


@pytest.mark.parametrize("pid",["ag-upload-outer-0001","ag-upload-outer-0002"])
def test_home_hot_update_and_search_use_same_front_model_as_detail(pid):
    from html.parser import HTMLParser
    class Cards(HTMLParser):
        def __init__(self,html):super().__init__();self.active=False;self.images=[];self.feed(html)
        def handle_starttag(self,tag,attrs):
            a=dict(attrs)
            if tag=="li":self.active=a.get("data-product-id")==pid
            if tag=="img" and self.active:self.images.append(a.get("src"))
        def handle_endtag(self,tag):
            if tag=="li":self.active=False
    with TestClient(create_app()) as c:
        for url in ["/homepage/storefront","/homepage/storefront?collection=hot","/homepage/storefront/search?category=women-outer"]:
            images=Cards(c.get(url).text).images
            assert images and all(src.endswith(pid+"-model-front.jpg") for src in images)
        row=storefront_gallery.assets()[pid+"-garment-cutout.webp"]
        response=c.get(row["url"])
        assert response.status_code==200 and response.headers["content-type"]=="image/webp"



def test_chat_recommendations_send_directly_and_do_not_open_mobile_keyboard():
    from pathlib import Path
    source = Path("core/homepage/ui/storefront-chat.js").read_text()
    suggestion = source[source.index("function showSuggestions"):source.index("function presentContext")]
    opener = source[source.index("const open = productId"):source.index('by("shop-chat-launcher")')]
    assert "form.requestSubmit();" in suggestion
    assert "question.focus()" not in suggestion
    assert "question.focus()" not in opener
    assert 'question.placeholder = "질문을 입력해 주세요"' in opener


def test_guest_order_page_keeps_phone_verification_and_delivery_form():
    from pathlib import Path
    with TestClient(create_app()) as client:
        response = client.get("/homepage/storefront/guest-order")
    assert response.status_code == 200
    assert 'data-guest-order-page="true"' in response.text
    assert "비회원 휴대폰 인증" in response.text
    assert 'id="phone-form"' in response.text
    assert 'id="delivery-form"' in response.text
    plugin = Path("deploy/shopping/wordpress/plugins/aicc-agachichi-account/aicc-agachichi-account.php").read_text()
    assert "function checkout_profile()" in plugin
    assert "if (!is_user_logged_in())" in plugin


def test_account_navigation_highlight_follows_current_route_only():
    from pathlib import Path
    plugin = Path("deploy/shopping/wordpress/plugins/aicc-agachichi-account/aicc-agachichi-account.php").read_text()
    css = Path("deploy/shopping/wordpress/plugins/aicc-agachichi-account/assets/account.css").read_text()
    assert "$is_registration = is_page('register')" in plugin
    assert "$is_login =" in plugin
    assert "aria-current=\"page\"" in plugin
    assert ".header-actions a.is-active" in css
    assert ".header-actions a.header-signup{" not in css


def test_signup_link_uses_normal_style_until_its_page_is_active():
    from pathlib import Path
    css = Path("core/homepage/ui/storefront.css").read_text()
    assert ".store-header .header-actions a.header-signup{" not in css
    assert ".store-header .header-actions a.is-active{" in css


def test_signup_success_shows_id_home_and_recommended_products():
    from pathlib import Path
    plugin = Path("deploy/shopping/wordpress/plugins/aicc-agachichi-account/aicc-agachichi-account.php").read_text()
    css = Path("deploy/shopping/wordpress/plugins/aicc-agachichi-account/assets/account.css").read_text()
    assert "wp_safe_redirect(self::signup_complete_url())" in plugin
    assert "function signup_complete_page()" in plugin
    assert "가입 아이디 <strong>" in plugin
    assert "회원가입을 축하합니다!" in plugin
    assert 'href="/homepage/storefront/">홈으로 가기' in plugin
    assert '[products limit="4" columns="2" orderby="date" order="DESC"]' in plugin
    assert "['signup-complete', '가입 완료', '[aicc_agachichi_signup_complete]', $parent_id]" in plugin
    assert "is_page('signup-complete')" in plugin
    assert ".aicc-recommendations ul.products" in css


def test_account_navigation_orders_guest_lookup_profile_logout_and_withdrawal():
    from pathlib import Path
    plugin = Path("deploy/shopping/wordpress/plugins/aicc-agachichi-account/aicc-agachichi-account.php").read_text()
    dashboard = Path("deploy/shopping/wordpress/plugins/aicc-agachichi-account/templates/myaccount/dashboard.php").read_text()
    css = Path("deploy/shopping/wordpress/plugins/aicc-agachichi-account/assets/account.css").read_text()
    js = Path("deploy/shopping/wordpress/plugins/aicc-agachichi-account/assets/account.js").read_text()
    assert "data-aicc-confirm" in plugin and "로그아웃하시겠습니까?" in plugin
    assert "header-orders" in plugin and ">주문내역</a>" in plugin
    assert "header-profile" in plugin and "/my-account/" in plugin
    assert "header-orders" in plugin and "/my-account/orders/" in plugin
    assert 'aria-label="비회원 주문 조회">주문내역</a>' in plugin and "header-signup" not in plugin
    login_link = plugin[plugin.index("function login_signup_link"):plugin.index("function login_failed") ]
    assert "회원가입</a>" in login_link
    assert "비회원 주문 조회 · 휴대폰 인증" in plugin
    assert "woocommerce_locate_template" in plugin and "templates/myaccount/dashboard.php" in plugin
    assert "'dashboard' => '내 정보'" in plugin and "'orders' => '주문내역'" in plugin
    assert "'edit-account' => '내 정보 수정'" in plugin
    assert "'customer-logout' => '로그아웃'" not in plugin
    assert "wc_get_orders([" in dashboard and "id=\"aicc-dashboard-orders-title\">주문내역" in dashboard
    assert "주문내역 바로가기" in dashboard and "장바구니 바로가기" in dashboard
    assert "이름·이메일·비밀번호 수정" in dashboard and "주소 수정" in dashboard
    assert "회원 탈퇴" in dashboard and "wp_nonce_field('aicc_delete_account')" in dashboard
    assert "WC_Customer($user_id)" in plugin and "delete_and_reassign(0)" in plugin
    assert "add_action('admin_post_aicc_delete_account'" in plugin
    assert "data-aicc-confirm" in js and "window.confirm" in js
    assert ".aicc-orders-table" in css and ".aicc-withdraw-button" in css
    assert "grid-template-columns:repeat(2,minmax(0,1fr))" in css
    assert ".woocommerce-account.aicc-account-dashboard-view .woocommerce-MyAccount-content" in css and "border:0" in css
    assert "aicc-account-dashboard-view" in plugin
    assert "aicc-account-orders-view" in plugin
    assert "No order has been made yet." in plugin and "상품 둘러보기" in plugin
    assert "aicc-account-store-footer" in plugin and "Everyday Comfort, Playful Touch" in plugin
    assert ".aicc-dashboard-links .aicc-account-button:nth-child(n+3){grid-column:1/-1}" in css
    assert ".woocommerce-account footer.wp-block-template-part{display:none!important}" in css
    assert ".woocommerce-account.aicc-account-orders-view .woocommerce-info:before{display:none}" in css
    assert ".woocommerce-account.aicc-account-orders-view .woocommerce-MyAccount-content{padding:0;border:0" in css


def test_account_recovery_ui_is_gated_and_uses_same_origin_api():
    from pathlib import Path
    plugin = Path("deploy/shopping/wordpress/plugins/aicc-agachichi-account/aicc-agachichi-account.php").read_text()
    js = Path("deploy/shopping/wordpress/plugins/aicc-agachichi-account/assets/account.js").read_text()
    css = Path("deploy/shopping/wordpress/plugins/aicc-agachichi-account/assets/account.css").read_text()
    assert "defined('AICC_ACCOUNT_RECOVERY_ENABLED') && AICC_ACCOUNT_RECOVERY_ENABLED === true" in plugin
    assert "if (!self::recovery_enabled()) { return; }" in plugin
    assert "아이디 찾기" in plugin and "비밀번호 재설정" in plugin
    assert "account-recovery/reset" in plugin
    assert "Referrer-Policy: no-referrer" in plugin and "nocache_headers()" in plugin
    assert "accountRecoveryEnabled" in plugin and "recoveryApi" in plugin
    assert "'/id-challenge'" in js and "'/id-confirm'" in js
    assert "'/password-reset'" in js and "'/password-reset/complete'" in js
    assert "localStorage" not in js and "sessionStorage" not in js
    assert ".aicc-recovery-page" in css

"""Explicit isolated DEV phone checkout and synthetic fixture runtime; no production composition."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from datetime import datetime, timedelta, timezone
from html import escape as html_escape
import asyncio, hashlib, json, secrets, subprocess, threading, time, uuid
import requests
import uvicorn
from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
from pydantic import SecretBytes, SecretStr
from core.api.dependencies.customer_session import CustomerSessionBoundary, TrustedSessionEvidence, SessionAPIDenied
from core.api.schemas.customer_auth import VerificationReceiptConsumeRequest
from core.shopping.customer_auth import TrustedReceiptBinding, TrustedVerificationContext, TrustedVerificationReceipt
from core.shopping.customer_identity import Customer, VerifiedContactBinding
from core.shopping.customer_persistence import initialize_schema, SQLiteCustomerSessionStore
from core.shopping.customer_session_service import CustomerSessionService, ReceiptPolicyDenied
from core.shopping.models import ProductVariant
from core.shopping.order_core import SQLiteOrderCreateLedger
from core.shopping.order_core.dev_app import create_order_dev_app
from core.shopping.order_core.telegram import OrderTelegramTransport, OrderTelegramIntegration
from core.shopping.order_core.woocommerce_writer import WooCommerceOrderWriter, ProviderOrderWritePermit
from ops.macos.shopping.dev_order_transport import PinnedDevWooOrderSession

PRIVATE=Path('/Users/kyouhan/.config/aicontrolcenter-dev-order')
DATA=Path('/Users/kyouhan/AIControlCenterRuntime/dev-order/data')
REPO=Path(__file__).resolve().parents[3]
ORIGIN='https://dev.bokstory.duckdns.org'

def now():return datetime.now(timezone.utc)
def reference(kind):return 'AG-'+kind+'-'+uuid.uuid4().hex
def public_reference(kind):return kind+'-'+uuid.uuid4().hex.upper()

def private_config(name):
    path=PRIVATE/name
    if path.is_symlink() or path.stat().st_mode & 0o077:raise RuntimeError('PRIVATE_CONFIG_PERMISSIONS')
    return json.loads(path.read_text())

def assert_isolation():
    v=json.loads(subprocess.run(['docker','--context','colima-aicontrolcenter-commerce','inspect',
        'aicc-order-dev-wordpress-1','aicc-order-dev-database-1'],capture_output=True,text=True,check=True).stdout)
    for item in v:
        if item['Config']['Labels'].get('com.docker.compose.project')!='aicc-order-dev':raise RuntimeError('DEV_PROJECT_REQUIRED')
        volumes={m.get('Name') for m in item['Mounts'] if m['Type']=='volume'}
        if not volumes or not volumes <= {'aicc-order-dev-wordpress','aicc-order-dev-database'}:raise RuntimeError('DEV_VOLUME_REQUIRED')
        if any(name.startswith('ai-shopping') for name in item['NetworkSettings']['Networks']):raise RuntimeError('PROD_NETWORK_DENIED')

class DevCatalog:
    def __init__(self,commerce,cfg):
        self.commerce=commerce;self.cfg=cfg
        products=cfg.get('active_products')
        if isinstance(products,list) and products:
            self.products={str(v['product_id']):v for v in products if isinstance(v,dict) and isinstance(v.get('product_id'),int)}
        else:
            self.products={str(cfg['provider_product_id']):{'product_id':cfg['provider_product_id'],'demo_id':'oc-demo-top-0001',
                'image_demo_id':'oc-demo-top-0001','sku':'aicc-dev-oc-demo-top-0001','category':'TOP'}}
    def read(self,path):
        response=requests.get('https://localhost:18446/wp-json/wc/v3/'+path,
            auth=(self.commerce['consumer_key'],self.commerce['consumer_secret']),verify=str(PRIVATE/'dev-woo-cert.pem'),
            timeout=15,allow_redirects=False,stream=True)
        if response.status_code!=200:response.close();raise ValueError('DEV_CATALOG_UNAVAILABLE')
        return WooCommerceOrderWriter._document(response)
    def binding(self,product_id):
        value=self.products.get(str(product_id))
        if value is None:raise ValueError('DEV_PRODUCT_NOT_ALLOWED')
        return value
    def stock_summary(self,product_id):
        self.get_product(product_id)
        rows=self.read('products/'+str(product_id)+'/variations?per_page=100')
        return '현재 재고: '+', '.join(str(v['attributes'][0]['option'])+': '+str(v['stock_quantity'])+'개' for v in rows if v.get('manage_stock') is True and type(v.get('stock_quantity')) is int)
    def get_product(self,product_id):
        binding=self.binding(product_id);raw=self.read('products/'+str(product_id))
        if raw['id']!=binding['product_id'] or raw['sku']!=binding['sku']:raise ValueError('DEV_PRODUCT_BINDING')
        variants=self.read('products/'+str(product_id)+'/variations?per_page=100')
        options=tuple(ProductVariant(str(v['id']),str(v['attributes'][0]['option']),'size',
            v['status']=='publish' and v['stock_status']=='instock' and (not v['manage_stock'] or v['stock_quantity']>0)) for v in variants)
        return {'id':str(raw['id']),'name':raw['name'],'slug':raw['slug'],'description':raw['description'],
            'price':raw['price'],'currency':'KRW','category':binding['category'],'in_stock':raw['stock_status']=='instock',
            'source':'woocommerce','image_url':'/__order-dev/product-image/'+binding.get('image_demo_id',binding['demo_id']),'variants':options}

def create_app():
    assert_isolation();cfg=private_config('runtime.private.json');commerce=private_config('commerce.private.json')['woocommerce']
    tg=private_config('telegram.private.json')
    if cfg.get('environment')!='DEV' or commerce.get('base_url')!='https://localhost:18446' or commerce.get('confirmed_isolated_from_prod') is not True:
        raise RuntimeError('ISOLATED_DEV_CONFIGURATION_REQUIRED')
    DATA.mkdir(parents=True,exist_ok=True);__import__('os').chmod(DATA,0o700)
    customer_path=DATA/'customers.sqlite3'
    initialize_schema(customer_path)
    store=SQLiteCustomerSessionStore(customer_path)
    # Explicit isolated test-account fixture; NEVER claim a real phone was verified.
    # This database and synthetic contact/receipt evidence must never migrate to PROD.
    with __import__('sqlite3').connect(customer_path) as connection:
        exists=connection.execute('SELECT 1 FROM shopping_customers WHERE customer_id=?',(cfg['customer_id'],)).fetchone()
    if not exists:
        stamp=now();store.save_customer(Customer(id=cfg['customer_id'],state='ACTIVE',created_at=stamp,updated_at=stamp,
            contact_binding=VerifiedContactBinding(customer_id=cfg['customer_id'],state='VERIFIED',created_at=stamp,
                updated_at=stamp,verified_at=stamp,contact_ref=cfg['contact_ref'])))
    evidence={};lock=threading.RLock()
    def resolve(payload):
        with lock:value=evidence.pop((payload.receipt_id,payload.browser_challenge),None)
        if value is None:raise ReceiptPolicyDenied('DEV_CREDENTIAL_RECEIPT_DENIED')
        return value
    boundary=CustomerSessionBoundary(service=CustomerSessionService(str(customer_path)),trusted_origin=ORIGIN,
        csrf_key=SecretBytes(bytes.fromhex(cfg['csrf_key'])),clock=now,resolve_evidence=resolve,recover_durable_bindings=True)
    phone_cfg=private_config('phone-verification.private.json')
    from core.shopping.order_core.guest_checkout import PrivateCheckoutStore,fingerprint
    from ops.macos.shopping.dev_guest_checkout import GuestCheckoutWooSession,authoritative_quote
    checkout=PrivateCheckoutStore(DATA/'guest-checkout.sqlite3') if phone_cfg.get('provider_customer_id') else None
    ledger=SQLiteOrderCreateLedger(DATA/'orders.sqlite3',clock=now);ledger.initialize()
    for file in [customer_path,DATA/'orders.sqlite3']:__import__('os').chmod(file,0o600)
    def authorize(command,stamp):
        operation=ledger.inspect_operation(command.idempotency_key)
        if checkout is not None and command.customer_id==phone_cfg['guest_customer_id']:
            if operation is None or operation['state']!='CLAIMED' or operation['customer_id']!=command.customer_id or operation['command_digest']!=command.command_digest:
                raise ValueError('GUEST_OPERATION_DENIED')
            draft=checkout.operation(command.idempotency_key,command.customer_id,operation['session_id'])
            expected=[(v['product_id'],v['variation_id'],v['quantity']) for v in draft['body']['line_items']]
            if [(v.product_id,v.variation_id,v.quantity) for v in command.line_items]!=expected:raise ValueError('GUEST_LINE_BINDING_DENIED')
            current=authoritative_quote(catalog,__import__('core.shopping.order_core.guest_chat',fromlist=['GuestCart']).GuestCart.model_validate({'line_items':draft['body']['line_items']}))
            if fingerprint(current)!=fingerprint(draft['body']['quote']):raise ValueError('GUEST_QUOTE_CHANGED')
            expires=datetime.fromisoformat(operation['authority_expires_at'].replace('Z','+00:00'))
            if now()>=expires:raise ValueError('GUEST_AUTHORITY_EXPIRED')
            return ProviderOrderWritePermit(command.customer_id,operation['session_id'],command.idempotency_key,
                command.command_digest,'isolated-dev-phone-checkout',stamp,min(expires,stamp+timedelta(seconds=30)))
        allowed={v['id'] for v in cfg['variants'] if v['available']}
        if (operation is None or operation['state']!='CLAIMED' or operation['customer_id']!=cfg['customer_id']
            or command.customer_id!=cfg['customer_id'] or operation['command_digest']!=command.command_digest
            or len(command.line_items)!=1 or any(v.provider_product_id!=cfg['provider_product_id']
                or v.provider_variation_id not in allowed or v.quantity!=1 for v in command.line_items)):
            raise ValueError('DEV_WRITE_POLICY_DENIED')
        expires=datetime.fromisoformat(operation['authority_expires_at'].replace('Z','+00:00'))
        if stamp>=expires:raise ValueError('DEV_AUTHORITY_EXPIRED')
        return ProviderOrderWritePermit(command.customer_id,operation['session_id'],command.idempotency_key,
            command.command_digest,'isolated-dev-one-item-policy',stamp,min(expires,stamp+timedelta(seconds=30)))
    def customer(value):
        if checkout is not None and value==phone_cfg['guest_customer_id']:return phone_cfg['provider_customer_id']
        if value!=cfg['customer_id']:raise ValueError('DEV_CUSTOMER_MAPPING_DENIED')
        return cfg['provider_customer_id']
    writer=WooCommerceOrderWriter(base_url='https://localhost',consumer_key=SecretStr(commerce['consumer_key']),
        consumer_secret=SecretStr(commerce['consumer_secret']),ledger=ledger,clock=now,authorize_once=authorize,
        resolve_customer=customer,session=(GuestCheckoutWooSession(PRIVATE/'dev-woo-cert.pem',store=checkout,provider_customer_id=phone_cfg['provider_customer_id']) if checkout is not None else PinnedDevWooOrderSession(PRIVATE/'dev-woo-cert.pem')))
    catalog=DevCatalog(commerce,cfg)
    transport=OrderTelegramTransport(token=SecretStr(tg['bot_token']),chat_id=tg['operator_chat_id'])
    from ops.macos.shopping.dev_inquiry_queue import DevInquiryQueue,mount_inquiry_status
    inquiry_queue=DevInquiryQueue(DATA/'inquiries.sqlite3',transport)
    aftersales=None
    if checkout is not None:
        from ops.macos.shopping.dev_aftersales import DevAftersalesStore
        aftersales=DevAftersalesStore(DATA/'aftersales.sqlite3',DATA/'aftersales-files',ledger=ledger,checkout=checkout,catalog=catalog)
    from ops.macos.shopping.dev_order_operator import DevOperatorAdapter,DevStockConfirmation
    operator_adapter=DevOperatorAdapter(ledger=ledger,store=checkout,inquiry_queue=inquiry_queue,aftersales=aftersales) if checkout else None
    telegram=OrderTelegramIntegration(ledger=ledger,transport=transport,operator_chat_id=tg['operator_chat_id'],
                                    operator_user_ids=frozenset(tg['operator_user_ids']),
                                    operator_adapter=operator_adapter,
                                    confirmation_guard=DevStockConfirmation(store=checkout) if checkout else None)
    app=create_order_dev_app(session_boundary=boundary,catalog=catalog,ledger=ledger,writer=writer,telegram_integration=telegram)
    from core.shopping.order_core.guest_chat_app import mount_guest_chat
    phone=None
    phone_cfg=private_config('phone-verification.private.json')
    if phone_cfg.get('enabled') is True:
        from ops.macos.shopping.dev_guest_phone import DevPhoneBridge,mount_phone_routes
        phone=DevPhoneBridge(cfg=phone_cfg,binding_key=bytes.fromhex(phone_cfg['binding_key']),
            customer_path=customer_path,bridge_path=DATA/'guest-phone.sqlite3')
        def register_phone_evidence(value):
            with lock:
                public_receipt=public_reference("VRF");public_challenge=public_reference("CHL")
                evidence[public_receipt,public_challenge]=value
            return {'receipt_id':public_receipt,'browser_challenge':public_challenge}
        mount_phone_routes(app,bridge=phone,boundary=boundary,register_evidence=register_phone_evidence)
    if phone is not None and checkout is not None:
        from ops.macos.shopping.dev_guest_checkout import mount_checkout_routes
        from core.api.routes.order_create import get_order_create_application
        mount_checkout_routes(app,store=checkout,phone_cfg=phone_cfg,boundary=boundary,
            application=app.dependency_overrides[get_order_create_application](),catalog=catalog,ledger=ledger)
        if aftersales is not None:
            from ops.macos.shopping.dev_aftersales import mount_aftersales
            mount_aftersales(app,store=aftersales,boundary=boundary,phone_cfg=phone_cfg)
    history_store=None
    if phone is not None and checkout is not None:
        from ops.macos.shopping.dev_chat_history import DevChatHistory,mount_history
        from core.api.routes.order_create import get_order_create_application
        history_app=app.dependency_overrides[get_order_create_application]()
        history_store=DevChatHistory(DATA/"chat-history.sqlite3",history_app._authenticate,phone_cfg["guest_customer_id"],answer_lookup=inquiry_queue.history_answer)
        mount_history(app,history_store)
    from ops.macos.shopping.dev_local_inquiry import LocalInquiryJudge
    mount_guest_chat(app,catalog=catalog,session_boundary=boundary,intent_classifier=LocalInquiryJudge(),phone_available=phone is not None,
        checkout_available=phone is not None and checkout is not None,inquiry_queue=inquiry_queue,history_store=history_store)
    mount_inquiry_status(app,inquiry_queue)
    if operator_adapter is not None:
        from ops.macos.shopping.dev_order_admin import mount_admin
        mount_admin(app,operator_adapter=operator_adapter,inquiry_queue=inquiry_queue,aftersales=aftersales)
    stop=threading.Event();health={'poller':'STARTING','environment':'DEV','auth_mode':'DEV phone verification and isolated test-account fixture'}
    def worker():
        while not stop.is_set():
            try:
                telegram.poll_once();telegram.dispatch_one();inquiry_queue.dispatch_one();health['poller']='RUNNING'
            except Exception:health['poller']='UNAVAILABLE'
            stop.wait(2)
    from contextlib import asynccontextmanager
    @asynccontextmanager
    async def lifespan(_):
        import fcntl
        lease=(DATA/'telegram-poller.lock').open('a')
        fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
        thread=threading.Thread(target=worker,daemon=True);thread.start()
        yield
        stop.set();await asyncio.to_thread(thread.join,20);lease.close()
    app.router.lifespan_context=lifespan
    @app.exception_handler(SessionAPIDenied)
    async def session_denied(request,error):
        return JSONResponse({'detail':'DEV authentication denied'},status_code=403,headers={'Cache-Control':'no-store'})
    @app.exception_handler(RequestValidationError)
    async def validation_error(request,error):return JSONResponse({'detail':'Invalid DEV request'},status_code=422,headers={'Cache-Control':'no-store'})
    @app.get('/dev-order/health',include_in_schema=False)
    def status():return JSONResponse(health,headers={'Cache-Control':'no-store'})
    @app.get('/dev-order/login',include_in_schema=False)
    def login():
        html="""<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DEV 주문 테스트 로그인</title><body><h1>DEV 주문 테스트</h1><p>테스트 고객 전용입니다. 휴대폰 인증·결제·배송 확정은 포함하지 않습니다.</p><form id="login"><label>아이디<input id="username" value="aicc-dev-test-customer" autocomplete="username"></label><label>비밀번호<input id="password" type="password" autocomplete="current-password"></label><button>로그인</button></form><p id="status" role="status"></p><script>document.querySelector('#login').addEventListener('submit',async event=>{event.preventDefault();const status=document.querySelector('#status');try{const r=await fetch('/dev-order/credentials',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:document.querySelector('#username').value,password:document.querySelector('#password').value})});if(!r.ok)throw new Error();const receipt=await r.json();const s=await fetch('/shopping/auth/session',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'same-origin',body:JSON.stringify(receipt)});if(!s.ok)throw new Error();location.href='/order-preview/PRODUCT';}catch(_){status.textContent='로그인에 실패했습니다.';}});</script></body></html>"""
        return HTMLResponse(html.replace('PRODUCT',str(cfg['provider_product_id'])),headers={'Cache-Control':'no-store','X-Robots-Tag':'noindex, nofollow'})
    attempts=[]
    @app.post('/dev-order/credentials',include_in_schema=False)
    async def credentials(request:Request):
        boundary.check_origin(request,required=True)
        if int(request.headers.get('content-length','0'))>4096:return JSONResponse({},status_code=413)
        raw=bytearray()
        async for chunk in request.stream():
            if len(raw)+len(chunk)>4096:return JSONResponse({},status_code=413)
            raw.extend(chunk)
        try:value=json.loads(raw)
        except Exception:value={}
        stamp=now()
        with lock:
            attempts[:]=[v for v in attempts if time.monotonic()-v<60]
            if len(attempts)>=10:return JSONResponse({},status_code=429,headers={'Cache-Control':'no-store'})
            attempts.append(time.monotonic())
            if (type(value) is not dict or set(value)!={'username','password'} or any(type(v) is not str for v in value.values())
                or not secrets.compare_digest(value['username'],'aicc-dev-test-customer')
                or not secrets.compare_digest(value['password'],cfg['login_password'])):
                return JSONResponse({},status_code=401,headers={'Cache-Control':'no-store'})
            receipt=TrustedVerificationReceipt(receipt_id=reference('VRF'),purpose='SESSION_ISSUANCE',
                browser_challenge=reference('CHL'),issuer_ref=reference('ISS'),customer_id=cfg['customer_id'],
                issued_at=stamp,expires_at=stamp+timedelta(minutes=5))
            evidence_keys=[k for k,v in evidence.items() if stamp>=v.receipt.expires_at]
            for k in evidence_keys:del evidence[k]
            if len(evidence)>=100:return JSONResponse({},status_code=503)
            public_receipt=public_reference("VRF");public_challenge=public_reference("CHL")
            evidence[public_receipt,public_challenge]=TrustedSessionEvidence(receipt,
                TrustedVerificationContext(accepted_bindings=frozenset({TrustedReceiptBinding(receipt.receipt_id,
                    receipt.issuer_ref,receipt.customer_id)})),receipt.browser_challenge)
        return JSONResponse({'receipt_id':public_receipt,'browser_challenge':public_challenge},headers={'Cache-Control':'no-store'})
    asset_root=REPO/'deploy/shopping/wordpress/plugins/ai-shopping-storefront'
    manifest=json.loads((asset_root/'assets/agachichi-v1/deployment-manifest.json').read_text())
    upload_manifest_path=REPO/'brands/agachichi/assets/media/uploads/manifest.json'
    upload_manifest=json.loads(upload_manifest_path.read_text()) if upload_manifest_path.is_file() else {'assets':[]}
    upload_root=(REPO/'brands/agachichi/assets/media/uploads').resolve()
    media_by_demo={}
    for binding in catalog.products.values():
        demo=binding.get('image_demo_id',binding.get('demo_id'))
        if str(demo).startswith('ag-upload-'):
            matches=[v for v in upload_manifest.get('assets',[]) if v.get('product_id')==demo]
            if len(matches)!=1:raise RuntimeError('DEV_UPLOAD_MEDIA_BINDING_INVALID')
            media=matches[0]
            expected=f'brands/agachichi/assets/media/uploads/{demo}.jpg'
            if media.get('status')!='READY' or media.get('target_path')!=expected:raise RuntimeError('DEV_UPLOAD_MEDIA_BINDING_INVALID')
            image=(REPO/expected).resolve()
            if not image.is_relative_to(upload_root) or image.is_symlink():raise RuntimeError('DEV_UPLOAD_MEDIA_PATH_INVALID')
        else:
            matches=[v for v in manifest['assets'] if v.get('product_id')==demo]
            if len(matches)!=1:raise RuntimeError('DEV_MEDIA_BINDING_INVALID')
            media=matches[0];image=asset_root/media['deployed_relative_path']
        if not image.is_file() or hashlib.sha256(image.read_bytes()).hexdigest()!=media['sha256']:
            raise RuntimeError('DEV_MEDIA_HASH_INVALID')
        media_by_demo[demo]=image
    @app.get('/__order-dev/product-image/{demo_id}',include_in_schema=False)
    def product_image(demo_id:str):
        image=media_by_demo.get(demo_id)
        if image is None:return JSONResponse({'detail':'not found'},status_code=404,headers={'Cache-Control':'no-store'})
        return FileResponse(image,media_type='image/jpeg',headers={'Cache-Control':'no-store'})
    @app.get('/__order-dev/product-image',include_in_schema=False)
    def legacy_product_image():
        demo=catalog.binding(cfg['provider_product_id']).get('image_demo_id','oc-demo-top-0001')
        return FileResponse(media_by_demo[demo],media_type='image/jpeg',headers={'Cache-Control':'no-store'})
    @app.get('/__order-dev/chat/embed/{demo_id}',include_in_schema=False)
    def storefront_order_embed(demo_id:str):
        rows=[v for v in catalog.products.values() if v.get('demo_id')==demo_id]
        if len(rows)!=1:return HTMLResponse('상품 주문 기능을 확인할 수 없습니다.',status_code=404,headers={'Cache-Control':'no-store'})
        try:product=catalog.get_product(str(rows[0]['product_id']))
        except Exception:return HTMLResponse('상품 주문 기능을 확인할 수 없습니다.',status_code=503,headers={'Cache-Control':'no-store'})
        options=''.join('<option value="'+html_escape(v.id,quote=True)+'"'+('' if v.available else ' disabled')+'>'+html_escape(v.label)+('' if v.available else ' · 품절')+'</option>' for v in product['variants'])
        panel='''<div class="commerce-panel-content" data-guest-shop-product="PRODUCT">
<h2>주문하기</h2>
<p class="commerce-note">궁금한 내용은 챗봇에게 물어보고, 여기에서 주문을 진행하세요. DEV 테스트 주문이며 실제 결제·배송은 진행하지 않습니다.</p>
<div class="commerce-choice"><label>옵션<select id="variation">OPTIONS</select></label><label>수량<input id="quantity" type="number" min="1" max="10" value="1"></label></div>
<div class="commerce-actions"><button id="add" type="button">장바구니 담기</button><button id="single" type="button">이 상품 주문하기</button></div>

<section class="commerce-subsection"><h3>장바구니</h3><div id="cart"></div><button id="checkout" type="button">장바구니 주문하기</button><button id="clear" type="button">비우기</button></section>
<section id="order" class="commerce-subsection" hidden><h3>주문</h3><div id="summary"></div><p id="auth-note" role="status"></p><div id="phone-form" hidden><label>휴대폰 번호<input id="phone-number" type="tel" autocomplete="tel" maxlength="32" placeholder="01012345678"></label><label class="commerce-consent"><input id="phone-consent" type="checkbox">주문 진행을 위한 인증 문자 수신 동의</label><button id="phone" type="button" disabled>인증 문자 받기</button><label>인증번호<input id="phone-code" inputmode="numeric" autocomplete="one-time-code" maxlength="10"></label><button id="phone-check" type="button" disabled>휴대폰 인증 확인</button></div><p>휴대폰 인증 후 배송정보를 확인하고 마지막에 주문을 확정합니다.</p><div id="delivery-form" hidden><h4>배송정보</h4><label>수령인<input id="recipient" maxlength="64" autocomplete="name"></label><div><label>우편번호<input id="postcode" inputmode="numeric" maxlength="5" autocomplete="postal-code" readonly></label><button id="address-search" type="button">한국 주소 검색</button></div><div id="address-search-layer" hidden><div id="address-search-frame"></div><button id="address-search-close" type="button">주소 검색 닫기</button></div><label>주소<input id="address1" maxlength="200" autocomplete="address-line1" readonly></label><label>상세주소<input id="address2" maxlength="100" autocomplete="address-line2" placeholder="동·호수 등 상세주소"></label><button id="prepare" type="button">배송정보와 주문 내용 확인</button></div><div id="final-review"></div><button id="confirm" type="button" disabled>이 내용으로 주문 확정</button><button id="guest-status" type="button" disabled>주문 상태 확인</button><button id="guest-new" type="button" hidden>새 주문 시작</button></section>
<p id="error" role="alert"></p><p class="commerce-links"><a href="/homepage/storefront/my-orders">내 주문 · 환불 · 사이즈교환 보기</a></p>
</div>'''.replace('PRODUCT',html_escape(product['id'],quote=True)).replace('OPTIONS',options or '<option value="">기본 옵션</option>')
        return HTMLResponse(panel,headers={'Cache-Control':'no-store','X-Robots-Tag':'noindex, nofollow'})
    @app.get('/dev-order/product/{demo_id}',include_in_schema=False)
    def storefront_order_entry(demo_id:str):
        rows=[v for v in catalog.products.values() if v.get('demo_id')==demo_id]
        if len(rows)!=1:return JSONResponse({'detail':'not found'},status_code=404,headers={'Cache-Control':'no-store'})
        return RedirectResponse('/homepage/storefront/product/'+demo_id+'#commerce-panel',status_code=302)
    @app.get('/dev-order',include_in_schema=False)
    def entry():return RedirectResponse('/homepage/storefront',status_code=302)
    return app

if __name__=='__main__':
    uvicorn.run(create_app(),host='127.0.0.1',port=18445,access_log=False,log_level='warning')

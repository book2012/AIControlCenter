"""Explicit DEV test-account order runtime; no production or phone-auth composition."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from datetime import datetime, timedelta, timezone
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
    def __init__(self,commerce,cfg):self.commerce=commerce;self.cfg=cfg
    def read(self,path):
        response=requests.get('https://localhost:18446/wp-json/wc/v3/'+path,
            auth=(self.commerce['consumer_key'],self.commerce['consumer_secret']),verify=str(PRIVATE/'dev-woo-cert.pem'),
            timeout=15,allow_redirects=False,stream=True)
        if response.status_code!=200:response.close();raise ValueError('DEV_CATALOG_UNAVAILABLE')
        return WooCommerceOrderWriter._document(response)
    def get_product(self,product_id):
        if product_id!=str(self.cfg['provider_product_id']):raise ValueError('DEV_PRODUCT_NOT_ALLOWED')
        raw=self.read('products/'+product_id)
        if raw['id']!=self.cfg['provider_product_id'] or raw['sku']!='aicc-dev-oc-demo-top-0001':raise ValueError('DEV_PRODUCT_BINDING')
        variants=self.read('products/'+product_id+'/variations?per_page=100')
        options=tuple(ProductVariant(str(v['id']),str(v['attributes'][0]['option']),'size',
            v['status']=='publish' and v['stock_status']=='instock' and (not v['manage_stock'] or v['stock_quantity']>0)) for v in variants)
        return {'id':str(raw['id']),'name':raw['name'],'slug':raw['slug'],'description':raw['description'],
            'price':raw['price'],'currency':'KRW','category':'TOP','in_stock':raw['stock_status']=='instock',
            'source':'woocommerce','image_url':'/__order-dev/product-image','variants':options}

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
    ledger=SQLiteOrderCreateLedger(DATA/'orders.sqlite3',clock=now);ledger.initialize()
    for file in [customer_path,DATA/'orders.sqlite3']:__import__('os').chmod(file,0o600)
    def authorize(command,stamp):
        operation=ledger.inspect_operation(command.idempotency_key)
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
        if value!=cfg['customer_id']:raise ValueError('DEV_CUSTOMER_MAPPING_DENIED')
        return cfg['provider_customer_id']
    writer=WooCommerceOrderWriter(base_url='https://localhost',consumer_key=SecretStr(commerce['consumer_key']),
        consumer_secret=SecretStr(commerce['consumer_secret']),ledger=ledger,clock=now,authorize_once=authorize,
        resolve_customer=customer,session=PinnedDevWooOrderSession(PRIVATE/'dev-woo-cert.pem'))
    transport=OrderTelegramTransport(token=SecretStr(tg['bot_token']),chat_id=tg['operator_chat_id'])
    telegram=OrderTelegramIntegration(ledger=ledger,transport=transport,operator_chat_id=tg['operator_chat_id'],
                                    operator_user_ids=frozenset(tg['operator_user_ids']))
    catalog=DevCatalog(commerce,cfg)
    app=create_order_dev_app(session_boundary=boundary,catalog=catalog,ledger=ledger,writer=writer,telegram_integration=telegram)
    from core.shopping.order_core.guest_chat_app import mount_guest_chat
    mount_guest_chat(app,catalog=catalog,session_boundary=boundary)
    stop=threading.Event();health={'poller':'STARTING','environment':'DEV','auth_mode':'test-account; not phone verified'}
    def worker():
        while not stop.is_set():
            try:
                telegram.poll_once();telegram.dispatch_one();health['poller']='RUNNING'
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
    media=next(v for v in manifest['assets'] if v.get('product_id')=='oc-demo-top-0001')
    image=asset_root/media['deployed_relative_path']
    if hashlib.sha256(image.read_bytes()).hexdigest()!=media['sha256']:raise RuntimeError('DEV_MEDIA_HASH_INVALID')
    @app.get('/__order-dev/product-image',include_in_schema=False)
    def product_image():return FileResponse(image,media_type='image/jpeg',headers={'Cache-Control':'no-store'})
    @app.get('/dev-order',include_in_schema=False)
    def entry():return RedirectResponse('/__order-dev/chat/product/'+str(cfg['provider_product_id']),status_code=302)
    return app

if __name__=='__main__':
    uvicorn.run(create_app(),host='127.0.0.1',port=18445,access_log=False,log_level='warning')

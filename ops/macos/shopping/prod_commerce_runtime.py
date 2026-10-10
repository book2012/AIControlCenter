"""Explicit production composition and one environment-aware Telegram consumer."""
from pathlib import Path
from datetime import datetime,timezone
from contextlib import asynccontextmanager
import asyncio,hashlib,json,os,re,sqlite3,threading,time,fcntl
from pydantic import SecretStr
from fastapi.responses import JSONResponse
from core.shopping.guest_runtime import create_guest_commerce_app
from core.shopping.guest_aftersales import GuestAftersalesStore
from core.shopping.guest_operator import GuestOperatorAdapter
from core.shopping.guest_inquiry_queue import GuestInquiryQueue
from core.shopping.operator_environment import DurableOperatorEnvironmentRouter
from core.shopping.order_core.telegram import OrderTelegramTransport,OrderTelegramIntegration
from ops.macos.shopping.prod_woo_port import ProductionCatalog,production_quote,writer_factory,assert_production
from ops.macos.shopping.prod_stock_confirmation import ProductionStockConfirmation
from ops.macos.shopping.prod_product_operator import ProductionProductOperator,ProductionProductProvider
ROOT=Path('/Users/kyouhan/AIControlCenterRuntime/prod-commerce/data')
PRIVATE=Path('/Users/kyouhan/.config/aicontrolcenter-prod-commerce')
REPO=Path(__file__).resolve().parents[3]
def now():return datetime.now(timezone.utc)
def private(name):
    p=PRIVATE/name
    if p.is_symlink() or p.stat().st_mode&0o077:raise ValueError('PRIVATE_CONFIGURATION_PERMISSIONS')
    return json.loads(p.read_text())
class TaggedTransport(OrderTelegramTransport):
    def send_message(self,text):
        greeting='안녕하세요 agachichi 입니다'
        if not text.startswith(greeting):text=greeting+'\n[운영]\n'+text
        return super().send_message(text)
def create_app():
    assert_production();cfg=private('runtime.private.json');phone=private('phone.private.json');tg=private('telegram.private.json')
    if cfg['environment']!='PROD' or cfg['shipping_policy']!='PROD_INCLUDED_SHIPPING':raise ValueError('PRODUCTION_CONFIGURATION_REQUIRED')
    ROOT.mkdir(mode=0o700,parents=True,exist_ok=True);catalog=ProductionCatalog(cfg['bindings'])
    transport=TaggedTransport(token=SecretStr(tg['bot_token']),chat_id=tg['operator_chat_id'])
    queue=GuestInquiryQueue(ROOT/'inquiries.sqlite3',transport)
    def lookup(ledger,checkout,catalog):return GuestAftersalesStore(ROOT/'aftersales.sqlite3',ROOT/'aftersales-files',ledger=ledger,checkout=checkout,catalog=catalog)
    from ops.macos.shopping.dev_local_inquiry import LocalInquiryJudge
    app=create_guest_commerce_app(private_root=ROOT,origin='https://bokstory.duckdns.org',phone_cfg=phone,binding_key=bytes.fromhex(cfg['binding_key']),csrf_key=bytes.fromhex(cfg['csrf_key']),catalog=catalog,quote=production_quote,writer_factory=writer_factory(tuple(cfg['port_credentials']),now),lookup_store_factory=lookup,clock=now,intent_classifier=LocalInquiryJudge(),inquiry_queue=queue,storefront_bindings={b['demo_id']:str(b['product_id']) for b in cfg['bindings']},bank_provider=lambda:private('bank.private.json').get('bank'))
    source=REPO/'brands/agachichi/catalog/dev-upload-products.json'
    from core.homepage.dev_test_stock import overlay
    records=overlay(json.loads(source.read_text())['products'],source)
    products=ProductionProductOperator(records=records,provider=ProductionProductProvider(records=records,bindings=cfg['bindings'],assert_isolation=assert_production),path=ROOT/'product-commands.sqlite3',projection_path=ROOT/'product-projection.json',catalog_hash=hashlib.sha256(source.read_bytes()).hexdigest())
    adapter=GuestOperatorAdapter(ledger=app.state.order_ledger,store=app.state.checkout,inquiry_queue=queue,aftersales=app.state.lookup_store)
    integration=OrderTelegramIntegration(ledger=app.state.order_ledger,transport=transport,operator_chat_id=tg['operator_chat_id'],operator_user_ids=frozenset(tg['operator_user_ids']),operator_adapter=adapter,product_operator=products,confirmation_guard=ProductionStockConfirmation(app.state.checkout))
    # DEV handler remains explicitly bound to its isolated DEV containers/storage.
    from ops.macos.shopping.dev_order_runtime import create_app as create_dev_app
    dev=create_dev_app();dev_integration=dev.state.telegram_integration
    actor=[None]
    def handle(integration,adapter,products,text,update_id):
        reference,decision,reply=adapter.resolve(text,update_id=update_id)
        if reference is None and decision is None and reply is None:reply=products.command(text,update_id)
        match=re.fullmatch(r'/order_(status|confirm|reject) ([0-9a-f]{24})',text)
        if match:reference=match[2];decision={'status':'STATUS','confirm':'CONFIRMED','reject':'REJECTED'}[match[1]]
        result=integration._ledger.process_operator_update(update_id,reference=reference,decision=decision,actor_reference=actor[0] if decision else None,confirmation_guard=integration._confirmation_guard)
        return reply or ('주문 상태를 반영했습니다. 주문목록으로 확인해 주세요.' if decision else '상품관리 또는 주문목록으로 사용 가능한 명령을 확인해 주세요.')
    router=DurableOperatorEnvironmentRouter(database_path=ROOT/'telegram-router.sqlite3',dev=lambda text,i:handle(dev_integration,dev.state.operator_adapter,dev.state.product_operator,text,i),prod=lambda text,i:handle(integration,adapter,products,text,i),default='PROD',chat_id=tg['operator_chat_id'],user_ids=frozenset(tg['operator_user_ids']))
    with sqlite3.connect(router.path) as c:
        c.execute('CREATE TABLE IF NOT EXISTS bot_cursor(id INTEGER PRIMARY KEY,offset INTEGER NOT NULL)')
        c.execute('INSERT OR IGNORE INTO bot_cursor VALUES(1,?)',(dev_integration._ledger.telegram_offset(),))
    state={'environment':'PROD','poller':'STARTING','product_management':'STARTING','transaction_sms':False};stop=threading.Event()
    def poll():
        with sqlite3.connect(router.path) as c:offset=c.execute('SELECT offset FROM bot_cursor WHERE id=1').fetchone()[0]
        for item in sorted(transport.get_updates(offset),key=lambda v:v.get('update_id',-1)):
            i=item.get('update_id');msg=item.get('message',{});chat=msg.get('chat',{});sender=msg.get('from',{})
            if type(i) is not int or i<offset:continue
            if chat.get('id')==tg['operator_chat_id'] and sender.get('id') in tg['operator_user_ids'] and sender.get('is_bot') is False and type(msg.get('text')) is str:
                try:
                    actor[0]='telegram-user-'+str(sender['id'])
                    reply=router.dispatch(msg['text'],chat_id=chat['id'],user_id=sender['id'],update_id=i);transport.send_message(reply)
                except Exception:pass # CLAIMED updates are never implicitly redispatched.
            with sqlite3.connect(router.path) as c:c.execute('UPDATE bot_cursor SET offset=? WHERE id=1',(i+1,))
            offset=i+1
    def worker():
        last=0
        while not stop.is_set():
            try:
                if time.monotonic()-last>=30:products.sync();state['product_management']='RUNNING';last=time.monotonic()
                poll();integration.dispatch_one();queue.dispatch_one();state['poller']='RUNNING'
            except Exception:state['poller']='UNAVAILABLE'
            stop.wait(2)
    @asynccontextmanager
    async def lifespan(_):
        # One lock shared with the DEV consumer prevents simultaneous getUpdates.
        lease=Path('/Users/kyouhan/AIControlCenterRuntime/dev-order/data/telegram-poller.lock').open('a');fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
        thread=threading.Thread(target=worker,daemon=True);thread.start()
        yield
        stop.set();await asyncio.to_thread(thread.join,20);lease.close()
    app.state.product_operator=products
    app.router.lifespan_context=lifespan
    @app.get('/shopping/health',include_in_schema=False)
    def health():return JSONResponse(state,headers={'Cache-Control':'no-store'})
    return app

def create_homepage():
    os.environ['AICC_COMMERCE_ENV']='PROD'
    from core.homepage.preview import create_app as homepage
    return homepage(managed_projection=ROOT/'product-projection.json')

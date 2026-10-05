"""Mac-only guest chat E2E: no customer login and no provider writes.

Binds loopback HTTPS only, never Caddy/DEV/PROD runtime. The temporary test
operator endpoint exists only in this harness. No external provider I/O occurs.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

import uvicorn
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import test_shop_ai_001b3_session_api as sessions
from test_shop_order_001c_catalog_resolution import Catalog, Writer, product
from test_shop_guest_checkout import LiveCatalog
from test_shop_order_001d_telegram import Transport, integration, update
from core.shopping.order_core.dev_app import create_order_dev_app
from core.shopping.order_core import SQLiteOrderCreateLedger
from core.shopping.product_drafts.persistence.path_policy import IsolatedTestDatabasePathPolicy


PORT=18443
ORIGIN=f"https://localhost:{PORT}"
CHROME=Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')


def main():
    if not CHROME.is_file():raise RuntimeError('isolated Chrome unavailable')
    for port in (PORT,18444):
        with socket.socket() as probe:probe.bind(('127.0.0.1',port))
    sessions.NOW=datetime.now(timezone.utc)
    sessions.ORIGIN=ORIGIN
    with tempfile.TemporaryDirectory(prefix='order-dev-browser-') as directory:
        root=Path(directory).resolve()
        clients=sessions.clients.__wrapped__();make_client=next(clients)
        api_generator=sessions.api.__wrapped__(root,make_client);api=next(api_generator)
        ledger=SQLiteOrderCreateLedger(root/'orders.sqlite3',clock=lambda:api.time.now,path_policy=IsolatedTestDatabasePathPolicy(root))
        ledger.initialize();writer=Writer();transport=Transport();telegram=integration(ledger,transport)
        app=create_order_dev_app(session_boundary=api.boundary,catalog=LiveCatalog(),ledger=ledger,writer=writer,telegram_integration=telegram)

        from core.shopping.order_core.guest_chat_app import mount_guest_chat
        from test_shop_guest_chat import Catalog as GuestCatalog
        from test_shop_dev_guest_phone import cfg,Port
        from ops.macos.shopping.dev_guest_phone import DevPhoneBridge,mount_phone_routes
        phone_port=Port(lambda:api.time.now)
        bridge=DevPhoneBridge(cfg=cfg(),binding_key=b"test-binding",customer_path=api.path,bridge_path=root/'phone.sqlite3',clock=lambda:api.time.now,port=phone_port)
        def register(value):
            import uuid
            r="VRF-"+uuid.uuid4().hex.upper();c="CHL-"+uuid.uuid4().hex.upper();api.evidence[r,c]=value
            return dict(receipt_id=r,browser_challenge=c)
        mount_phone_routes(app,bridge=bridge,boundary=api.boundary,register_evidence=register)
        from core.shopping.order_core.guest_checkout import PrivateCheckoutStore
        from ops.macos.shopping.dev_guest_checkout import mount_checkout_routes
        from core.api.routes.order_create import get_order_create_application
        from dataclasses import replace
        from decimal import Decimal
        original_writer=writer.create_order
        def priced_writer(command):
            result=original_writer(command)
            line=replace(result.line_items[0],subtotal=Decimal("29000"),total=Decimal("29000"))
            return replace(result,line_items=(line,),total=Decimal("29000"))
        writer.create_order=priced_writer
        store=PrivateCheckoutStore(root/'delivery.sqlite3',clock=lambda:api.time.now.timestamp())
        mount_checkout_routes(app,store=store,phone_cfg=bridge.cfg,boundary=api.boundary,
            application=app.dependency_overrides[get_order_create_application](),catalog=LiveCatalog(),ledger=ledger)
        mount_guest_chat(app,catalog=GuestCatalog(),session_boundary=api.boundary,phone_available=True,checkout_available=True)
        @app.post('/__test/operator')
        def operator():
            telegram.dispatch_one()
            reference=transport.messages[0].split('참조: ',1)[1].split('\n',1)[0]
            value=update();value['message']['text']='/order_confirm '+reference
            transport.updates=[value];telegram.poll_once();telegram.dispatch_one()
            return {'ok':True}


        @app.get('/')
        def boot():
            return HTMLResponse('<script>location.href="/__test/page"</script>')
        @app.get('/__test/page')
        def page():
            with TestClient(app,base_url=ORIGIN) as client:html=client.get('/__order-dev/chat/product/10').text
            script="""<script>window.addEventListener('load',async()=>{
 const pause=ms=>new Promise(r=>setTimeout(r,ms));
 const wait=async predicate=>{for(let i=0;i<150;i++){if(predicate())return;await pause(50);}throw new Error('timeout');};
 try{
 document.querySelector('#stock').click();
 await wait(()=>document.querySelector('#messages').textContent.includes('품절 옵션: L'));
 document.querySelector('#variation').value='11';document.querySelector('#add').click();
 await wait(()=>document.querySelector('#cart').textContent.includes('1개'));
 document.querySelector('#checkout').click();
 await wait(()=>!document.querySelector('#order').hidden);
 if(document.querySelector('#phone').disabled||!document.querySelector('#confirm').disabled)throw new Error('unverified order');
 if(!document.querySelector('#summary').textContent.includes('29000'))throw new Error('price');
 document.querySelector('#phone-number').value='01012345678';document.querySelector('#phone-consent').checked=true;
 document.querySelector('#phone').click();await wait(()=>!document.querySelector('#phone-check').disabled);
 document.querySelector('#phone-code').value='123456';document.querySelector('#phone-check').click();
 await wait(()=>!document.querySelector('#delivery-form').hidden);
 const session=await fetch('/shopping/auth/session');if(!session.ok)throw new Error('session');
 if(document.querySelector('#phone-code').value||!document.querySelector('#confirm').disabled)throw new Error('otp or premature order');
 await wait(()=>!document.querySelector('#delivery-form').hidden);
 document.querySelector('#recipient').value='DEV 수령인';document.querySelector('#postcode').value='12345';
 document.querySelector('#address1').value='DEV 테스트 배송 주소';document.querySelector('#prepare').click();
 await wait(()=>!document.querySelector('#confirm').disabled);
 document.querySelector('#confirm').click();document.querySelector('#confirm').click();
 await wait(()=>document.querySelector('#auth-note').textContent.includes('접수 완료'));
 const operator=await fetch('/__test/operator',{method:'POST'});if(!operator.ok)throw new Error('operator');
 document.querySelector('#guest-status').click();await wait(()=>document.querySelector('#auth-note').textContent.includes('주문을 확인했습니다'));
 if(sessionStorage.getItem('aicc-guest-operation-v1').includes('배송 주소')||document.querySelector('#recipient').value)throw new Error('PII retention');

 if(!sessionStorage.getItem('aicc-guest-cart-v1'))throw new Error('cart');
 document.body.dataset.orderE2e='PASS';
 }catch(error){document.body.dataset.orderE2e='FAIL';document.body.dataset.testError=error.message;}
});</script>"""
            return HTMLResponse(html.replace('</html>',script+'</html>'))

        cert=root/'cert.pem';key=root/'key.pem'
        subprocess.run(['/usr/bin/openssl','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),
                        '-out',str(cert),'-days','1','-subj','/CN=localhost'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
        server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=PORT,ssl_keyfile=str(key),ssl_certfile=str(cert),
                                            log_level='error',access_log=False))
        thread=threading.Thread(target=server.run,daemon=True);thread.start()
        try:
            for _ in range(100):
                if server.started:break
                time.sleep(.05)
            if not server.started:raise RuntimeError('isolated server did not start')
            # Certificate bypass is confined to this disposable loopback-only test profile.
            chrome=subprocess.Popen([str(CHROME),'--headless','--disable-gpu','--no-first-run',
                '--no-default-browser-check','--disable-background-networking','--ignore-certificate-errors',
                '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE localhost',
                '--remote-debugging-address=127.0.0.1','--remote-debugging-port=18444',
                '--user-data-dir='+str(root/'chrome-profile'),'about:blank'],
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            try:
                for _ in range(100):
                    try:
                        with urllib.request.urlopen('http://127.0.0.1:18444/json/list',timeout=.3) as response:
                            targets=json.load(response)
                        target=next(v for v in targets if v['type']=='page')
                        break
                    except Exception:time.sleep(.1)
                else:raise RuntimeError('isolated Chrome CDP unavailable')
                driver=r"""
const socket = new WebSocket(process.argv[1]);
await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject;});
let sequence=0;const pending=new Map();
socket.onmessage=event=>{const value=JSON.parse(event.data);const entry=pending.get(value.id);if(entry){pending.delete(value.id);value.error?entry.reject(new Error(value.error.message)):entry.resolve(value.result);}};
const call=(method,params={})=>new Promise((resolve,reject)=>{const id=++sequence;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));});
try {
 await call('Page.enable');await call('Page.navigate',{url:process.argv[2]});
 let state;
 for(let i=0;i<200;i++){
  const result=await call('Runtime.evaluate',{expression:'JSON.stringify({state:document.body?.dataset.orderE2e,status:document.querySelector("#auth-note")?.textContent,error:document.querySelector("#error")?.textContent,testError:document.body?.dataset.testError})',returnByValue:true});
  state=JSON.parse(result.result.value||'{}');if(['PASS','FAIL'].includes(state.state))break;
  await new Promise(resolve=>setTimeout(resolve,100));
 }
 console.log(JSON.stringify(state));
} finally {socket.close();}
"""
                result=subprocess.run(['/opt/homebrew/bin/node','--input-type=module','-e',driver,
                    target['webSocketDebuggerUrl'],ORIGIN+'/'],capture_output=True,text=True,timeout=30)
                browser_state=json.loads(result.stdout)
                passed=browser_state.get('state')=='PASS'
                if not passed:print('BROWSER_STATE',json.dumps(browser_state,ensure_ascii=False))
            finally:
                chrome.terminate()
                try:chrome.wait(timeout=5)
                except subprocess.TimeoutExpired:chrome.kill();chrome.wait()
            report={'browser':'isolated real Chrome','guest_phone_shipping_confirm_telegram_operator_status':passed,
                    'writer_calls':len(writer.calls),'telegram_fake_messages':len(transport.messages),'test_target':'loopback HTTPS',
                    'external_provider_requests':0,'phone_fake_calls':phone_port.calls,'prod_mutation':False}
            print(json.dumps(report,ensure_ascii=False))
            if not passed or len(writer.calls)!=1 or len(transport.messages)!=2:raise RuntimeError('isolated browser E2E failed')
        finally:
            server.should_exit=True;thread.join(timeout=5)
            api_generator.close();clients.close()


if __name__=='__main__':main()

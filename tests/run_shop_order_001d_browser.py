"""Mac-only isolated real-Chrome E2E: synthetic auth + fake Woo/Telegram.

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
        app=create_order_dev_app(session_boundary=api.boundary,catalog=Catalog(product()),ledger=ledger,writer=writer,telegram_integration=telegram)

        @app.get('/')
        def boot():
            return HTMLResponse('<!doctype html><html lang="ko"><title>Isolated DEV test</title><script>'
                +'fetch("/shopping/auth/session",{method:"POST",credentials:"same-origin",headers:{"Content-Type":"application/json"},body:JSON.stringify('
                +json.dumps(sessions.PAYLOAD)+')}).then(r=>{if(r.status!==201)throw new Error("issue");location.href="/__test/page";}).catch(()=>document.body.dataset.orderE2e="FAIL");'
                +'</script><body>Isolated synthetic DEV test</body></html>')

        @app.get('/__test/page')
        def page():
            with TestClient(app,base_url=ORIGIN) as client: html=client.get('/order-preview/123').text
            script='<script>\nwindow.addEventListener("load",async()=>{\n const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));\n const wait=async text=>{for(let i=0;i<160;i++){if(document.querySelector("#order-status").textContent.includes(text))return;await sleep(50);}throw new Error("state timeout");};\n try{\n  document.querySelector("#order-submit").click();\n  await wait("접수되었습니다");\n  document.querySelector("#order-submit").click();\n  const response=await fetch("/__test/operator",{method:"POST"});\n  if(!response.ok)throw new Error("operator");\n  document.querySelector("#order-check").click();\n  await wait("주문을 확인했습니다");\n  document.body.dataset.orderE2e="PASS";\n }catch(_){document.body.dataset.orderE2e="FAIL";}\n});\n</script>'
            return HTMLResponse(html.replace('</html>',script+'</html>'))

        @app.post('/__test/operator')
        def operator():
            keys=ledger.notification_statuses()
            if len(keys)!=1:raise RuntimeError('one order expected')
            sent=telegram.dispatch_one()
            text=transport.messages[0]
            reference=text.split('참조: ',1)[1].split('\n',1)[0]
            value=update()
            value['message']['text']='/order_confirm '+reference
            transport.updates=[value]
            result=telegram.poll_once()
            telegram.dispatch_one()
            return {'sent':sent['outcome'],'review':result['results'][0]['outcome']}

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
  const result=await call('Runtime.evaluate',{expression:'JSON.stringify({state:document.body?.dataset.orderE2e,status:document.querySelector("#order-status")?.textContent})',returnByValue:true});
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
            report={'browser':'isolated real Chrome','ui_to_http_to_telegram_to_operator_to_customer':passed,
                    'writer_calls':len(writer.calls),'telegram_fake_messages':len(transport.messages),'test_target':'loopback HTTPS',
                    'external_provider_requests':0,'prod_mutation':False}
            print(json.dumps(report,ensure_ascii=False))
            if not passed or len(writer.calls)!=1 or len(transport.messages)!=2:raise RuntimeError('isolated browser E2E failed')
        finally:
            server.should_exit=True;thread.join(timeout=5)
            api_generator.close();clients.close()


if __name__=='__main__':main()

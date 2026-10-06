"""Disposable real Chrome: fake trusted Telegram updates, zero external providers."""
import sys,json,subprocess,tempfile,threading,time,urllib.request
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import uvicorn
from fastapi import FastAPI,Request
from fastapi.responses import Response,JSONResponse
from fastapi.testclient import TestClient
from core.homepage.preview import create_app
from core.shopping.order_core import SQLiteOrderCreateLedger
from core.shopping.order_core.telegram import OrderTelegramIntegration
from core.shopping.product_drafts.persistence.path_policy import IsolatedTestDatabasePathPolicy
from test_shop_dev_product_operator import operator,Provider

def main():
    with tempfile.TemporaryDirectory(prefix="aicc-product-operator-browser-") as d:
        root=Path(d);op=operator(root);op.sync()
        class Transport:
            chat_id=123456
            def __init__(self):self.updates=[];self.messages=[]
            def get_updates(self,offset):return [u for u in self.updates if u["update_id"]>=offset]
            def send_message(self,text):self.messages.append(text);return len(self.messages)
        t=Transport();ledger=SQLiteOrderCreateLedger(root/"orders.sqlite3",clock=lambda:datetime.now(timezone.utc),path_policy=IsolatedTestDatabasePathPolicy(root));ledger.initialize()
        tg=OrderTelegramIntegration(ledger=ledger,transport=t,operator_chat_id=t.chat_id,operator_user_ids=frozenset({777}),product_operator=op)
        preview=TestClient(create_app(managed_projection=op.projection_path));app=FastAPI()
        @app.post("/__fake_telegram_command")
        async def command(request:Request):
            v=await request.json()
            t.updates=[{"update_id":v["id"],"message":{"chat":{"id":t.chat_id,"type":"private"},"from":{"id":777,"is_bot":False},"text":v["text"]}}]
            tg.poll_once();return JSONResponse({"reply":t.messages[-1]})
        @app.get("/{path:path}")
        def page(path:str,request:Request):
            r=preview.get("/"+path+("?"+request.url.query if request.url.query else ""));
            return Response(r.content,status_code=r.status_code,media_type=r.headers.get("content-type","text/plain"),headers={"Cache-Control":"no-store"})
        cert=root/"cert.pem";key=root/"key.pem"
        subprocess.run(["/usr/bin/openssl","req","-x509","-newkey","rsa:2048","-nodes","-keyout",str(key),"-out",str(cert),"-days","1","-subj","/CN=localhost"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
        server=uvicorn.Server(uvicorn.Config(app,host="127.0.0.1",port=18443,ssl_keyfile=str(key),ssl_certfile=str(cert),log_level="error",access_log=False))
        thread=threading.Thread(target=server.run,daemon=True);thread.start();chrome=None
        try:
            for _ in range(100):
                if server.started:break
                time.sleep(.05)
            chrome=subprocess.Popen(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome","--headless","--disable-gpu","--no-first-run","--no-default-browser-check","--disable-background-networking","--ignore-certificate-errors","--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE localhost","--remote-debugging-address=127.0.0.1","--remote-debugging-port=18444","--user-data-dir="+str(root/"profile"),"about:blank"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            for _ in range(100):
                try:
                    with urllib.request.urlopen("http://127.0.0.1:18444/json/list",timeout=.3) as r:target=next(v for v in json.load(r) if v["type"]=="page")
                    break
                except Exception:time.sleep(.1)
            else:raise RuntimeError("CDP unavailable")
            driver=r"""
const s=new WebSocket(process.argv[1]);await new Promise((r,j)=>{s.onopen=r;s.onerror=j;});let n=0;const p=new Map();s.onmessage=e=>{const v=JSON.parse(e.data),x=p.get(v.id);if(x){p.delete(v.id);v.error?x.reject(Error(v.error.message)):x.resolve(v.result);}};
const call=(method,params={})=>new Promise((resolve,reject)=>{const id=++n;p.set(id,{resolve,reject});s.send(JSON.stringify({id,method,params}));});
const js=async expression=>{const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(r.exceptionDetails.exception?.description);return r.result.value;};
const wait=async expression=>{for(let i=0;i<100;i++){if(await js(expression))return;await new Promise(r=>setTimeout(r,70));}throw Error('timeout '+expression);};
const nav=async path=>{await call('Page.navigate',{url:'https://localhost:18443'+path});await wait('document.readyState==="complete"&&!!document.getElementById("shop-chat-launcher")');await new Promise(r=>setTimeout(r,300));};
const command=async (id,text)=>js('fetch("/__fake_telegram_command",{method:"POST",headers:{"Content-Type":"application/json"},body:'+JSON.stringify(JSON.stringify({id,text}))+'}).then(r=>r.json())');
try{
 await call('Page.enable');await nav('/homepage/storefront');
 await command(1,'베이직 하이넥 니트 50000으로 할인');
 await nav('/homepage/storefront?collection=sale');
 if(!await js('!!document.querySelector(".product-card[data-product-id=ag-upload-top-0006]")&&document.getElementById("home-feed").textContent.includes("#SALE")'))throw Error('SALE feed');
 await nav('/homepage/storefront/product/ag-upload-top-0006');
 if(!await js('document.body.textContent.includes("50,000원")&&document.body.textContent.includes("정상가 69,000원")'))throw Error('SALE price');
 await command(2,'브라운 싱글 롱 코트 가격 200000원으로 변경');
 await nav('/homepage/storefront/product/ag-upload-outer-0004');
 if(!await js('document.body.textContent.includes("200,000원")'))throw Error('regular price');
 await command(3,'카멜 벨티드 롱 코트 L 재고 없음');
 await nav('/homepage/storefront/product/ag-upload-outer-0001');
 if(!await js('Array.from(document.querySelectorAll(".variant-option")).find(x=>x.textContent==="L").disabled'))throw Error('out of stock size');
 await command(4,'브라운 싱글 롱 코트 제거');await nav('/homepage/storefront?collection=hot');
 if(await js('!!document.querySelector(".product-card[data-product-id=ag-upload-outer-0004]")'))throw Error('hidden still visible');
 if(await js('fetch("/homepage/storefront/product/ag-upload-outer-0004").then(r=>r.status)')!==404)throw Error('hidden PDP');
 await command(5,'브라운 싱글 롱 코트 다시 공개');await nav('/homepage/storefront/product/ag-upload-outer-0004');
 if(!await js('document.body.textContent.includes("200,000원")&&document.getElementById("detail-image").naturalWidth>0'))throw Error('restore content');
 await command(6,'베이직 하이넥 니트 할인 취소');await nav('/homepage/storefront?collection=sale');
 if(await js('!!document.querySelector(".product-card[data-product-id=ag-upload-top-0006]")'))throw Error('sale removal');
 await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
 await nav('/homepage/storefront/product/ag-upload-top-0006');
 if(!await js('document.documentElement.scrollWidth<=innerWidth&&document.body.textContent.includes("69,000원")'))throw Error('mobile price');
 console.log(JSON.stringify({passed:true,checks:['SALE feed and original price','regular price','exact size stock','hide and restore images','discount removal','mobile'],external_provider_requests:0,prod_mutation:false}));
}finally{s.close();}
"""
            r=subprocess.run(["/opt/homebrew/bin/node","--input-type=module","-e",driver,target["webSocketDebuggerUrl"]],capture_output=True,text=True,timeout=65)
            if r.returncode:raise RuntimeError(r.stderr[-1500:])
            assert len(op.provider.calls)==6 and len(t.messages)==6
            print(r.stdout.strip())
        finally:
            if chrome:
                chrome.terminate()
                try:chrome.wait(timeout=5)
                except subprocess.TimeoutExpired:chrome.kill();chrome.wait()
            server.should_exit=True;thread.join(timeout=5);preview.close()
if __name__=="__main__":main()

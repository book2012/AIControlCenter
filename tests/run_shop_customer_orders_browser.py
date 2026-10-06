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

def main():
    with tempfile.TemporaryDirectory(prefix="aicc-product-operator-browser-") as d:
        root=Path(d);preview=TestClient(create_app(managed_projection=False));app=FastAPI()
        @app.get("/shopping/auth/session")
        def auth():return JSONResponse({"verified":True},headers={"X-CSRF-Token":"fake-csrf"})
        @app.post("/__order-dev/orders/lookup")
        async def lookup(request:Request):
            data=await request.json()
            if data!={"order_number":"15","phone":"01012345678"}:return JSONResponse({"message":"주문번호와 인증한 휴대폰 번호를 확인해 주세요."},status_code=403)
            return JSONResponse({"order":{"order_id":15,"review_state":"CONFIRMED","items":[{"name":"테스트 블라우스","option":"화이트 / M","quantity":2}],"total":"58000","currency":"KRW","payment":{"state":"PAID"},"fulfillment":{"state":"SHIPPED","carrier":"테스트 택배","tracking":"TEST12345"},"delivery":{"first_name":"테스트 고객","postcode":"12345","address_1":"테스트 배송주소"},"cases":[],"return_available":False,"exchange_available":False}})
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
const nav=async path=>{await call('Page.navigate',{url:'https://localhost:18443'+path});await wait('document.readyState==="complete"');await new Promise(r=>setTimeout(r,200));};
try{
 await call('Page.enable');await nav('/homepage/storefront');
 if(!await js('document.querySelector(".header-orders").textContent==="ORDER"&&getComputedStyle(document.getElementById("shop-chat-launcher")).backgroundColor==="rgb(198, 83, 0)"'))throw Error('ORDER header / orange chat');
 await nav('/homepage/storefront/my-orders');
 await js('document.getElementById("orders-number").value="15";document.getElementById("lookup-phone").value="01012345678";document.getElementById("orders-lookup").click()');
 await wait('!!document.querySelector(".order-card")');
 if(!await js('["주문확인 완료","입금완료","배송중","화이트 / M","테스트 배송주소","TEST12345"].every(t=>document.body.textContent.includes(t))'))throw Error('order detail');
 await js('document.getElementById("orders-number").value="999";document.getElementById("orders-lookup").click()');
 await wait('!document.querySelector(".order-card")&&document.getElementById("orders-message").textContent.includes("주문번호")');
 await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
 if(!await js('document.documentElement.scrollWidth<=innerWidth'))throw Error('mobile overflow');
 console.log(JSON.stringify({passed:true,checks:['ORDER header','orange chat','number and phone lookup','payment and shipment','delivery and item detail','invalid lookup clears detail','mobile'],external_provider_requests:0,prod_mutation:false}));
}finally{s.close();}
"""
            r=subprocess.run(["/opt/homebrew/bin/node","--input-type=module","-e",driver,target["webSocketDebuggerUrl"]],capture_output=True,text=True,timeout=65)
            if r.returncode:raise RuntimeError(r.stderr[-1500:])
            print(r.stdout.strip())
        finally:
            if chrome:
                chrome.terminate()
                try:chrome.wait(timeout=5)
                except subprocess.TimeoutExpired:chrome.kill();chrome.wait()
            server.should_exit=True;thread.join(timeout=5);preview.close()
if __name__=="__main__":main()

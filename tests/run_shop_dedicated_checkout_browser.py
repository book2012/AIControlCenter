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
    production="--production-transport" in sys.argv
    api_prefix="/shopping" if production else "/__order-dev"
    browser_host="bokstory.duckdns.org" if production else "localhost"
    with tempfile.TemporaryDirectory(prefix="aicc-product-operator-browser-") as d:
        root=Path(d);preview=TestClient(create_app(managed_projection=False));app=FastAPI()
        from core.shopping.order_core.guest_chat_app import mount_guest_chat
        from test_shop_guest_chat import Catalog
        guest=FastAPI();mount_guest_chat(guest,catalog=Catalog(),session_boundary=None)
        guest_client=TestClient(guest)
        fixture={"verified":False,"writes":0,"sms":0,"start_failure":True}
        quote={"line_items":[{"product_id":"10","variation_id":"11","name":"테스트 블라우스","option":"화이트 / M","quantity":2,"subtotal":"58000"}],"items_total":"58000","final_total":"58000","shipping_fee":"0","currency":"KRW"}
        @app.get("/__fake_product")
        def fake_product():
            html=guest_client.get("/__order-dev/chat/product/10").text
            html=html.replace("/__order-dev/guest-chat.js",api_prefix+"/guest-chat.js")
            html=html.replace('data-product="10"','data-guest-shop-product="10"')
            return Response(html,media_type="text/html")
        @app.get(api_prefix+"/guest-chat.js")
        def guest_script():return Response((Path(__file__).resolve().parents[1]/"deploy/shopping/wordpress/plugins/ai-shopping-storefront/assets/storefront-guest-chat.js").read_text(),media_type="application/javascript")
        @app.get("/shopping/auth/session")
        def auth():return JSONResponse({"verified":fixture["verified"]},status_code=200 if fixture["verified"] else 401,headers={"X-CSRF-Token":"fake-csrf"})
        @app.get(api_prefix+"/checkout/session")
        def verified():return JSONResponse({"verified":fixture["verified"]},status_code=200 if fixture["verified"] else 401)
        @app.get(api_prefix+"/chat/capabilities")
        def capabilities():return {"phone_verification":True,"order_confirmation":True,"message":"휴대폰 인증을 진행해 주세요."}
        @app.post(api_prefix+"/chat/quote")
        async def price(request:Request):
            data=await request.json();assert data["line_items"]==[{"product_id":"10","variation_id":"11","quantity":2}]
            return quote
        @app.get(api_prefix+"/chat/cart/product/10")
        def metadata():return {"id":"10","name":"테스트 블라우스","price":"29000","product_url":"/__fake_product","variants":[{"id":"11","label":"화이트 / M","available":True}]}
        @app.post(api_prefix+"/phone/start")
        async def phone(request:Request):
            data=await request.json();assert data=={"phone":"01012345678","consent":True}
            if fixture["start_failure"]:
                fixture["start_failure"]=False;return JSONResponse({"message":"잠시 후 다시 요청해 주세요."},status_code=503)
            fixture["sms"]+=1
            return {"message":"인증번호를 입력해 주세요."}
        @app.post(api_prefix+"/phone/check")
        async def check(request:Request):
            data=await request.json();assert data["code"]=="123456";fixture["verified"]=True
            return JSONResponse({"verified":True},status_code=201)
        @app.post(api_prefix+"/checkout/prepare")
        async def prepare(request:Request):
            data=await request.json();assert fixture["verified"] and data["cart"]["line_items"]==[{"product_id":"10","variation_id":"11","quantity":2}]
            return {"draft_id":"a"*48,"operation_key":"guest-order-"+"b"*48,"delivery":data["delivery"],"quote":quote}
        @app.post(api_prefix+"/checkout/confirm")
        async def confirm(request:Request):
            assert fixture["verified"] and (await request.json())=={"draft_id":"a"*48};fixture["writes"]+=1
            return JSONResponse({"provider_order_id":42,"state":"COMPLETED"},status_code=201)
        @app.get("/shopping/orders/operations/{key}")
        def status(key:str):return {"state":"COMPLETED","provider_order_id":42,"review_state":"CONFIRMED"}
        @app.get(api_prefix+"/chat/history/session")
        def history_ready():return {"ready":True}
        @app.post(api_prefix+"/chat/orders/notices")
        async def notices(request:Request):
            assert fixture["verified"] and request.headers.get("X-CSRF-Token")=="fake-csrf"
            assert (await request.json())=={"order_number":"42"}
            return {"messages":[{"id":"42:SHIPPED","message":"안녕하세요 agachichi 입니다\n주문 #42 배송을 시작했습니다.\n운송장번호: TEST-TRACKING"}],"transaction_sms":False}
        @app.get("/__fake_stats")
        def stats():return fixture
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
            chrome=subprocess.Popen(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome","--headless","--disable-gpu","--no-first-run","--no-default-browser-check","--disable-background-networking","--ignore-certificate-errors","--host-resolver-rules=MAP bokstory.duckdns.org 127.0.0.1, MAP * ~NOTFOUND, EXCLUDE localhost","--remote-debugging-address=127.0.0.1","--remote-debugging-port=18444","--user-data-dir="+str(root/"profile"),"about:blank"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
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
 await call('Page.enable');await call('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false});await nav('/__fake_product');
 await js('document.getElementById("variation").value="11";document.getElementById("quantity").value="2";document.getElementById("single").click()');
 await wait('location.pathname==="/homepage/storefront/checkout"&&document.getElementById("phone-form")?.hidden===false');
 if(!await js('document.body.textContent.includes("테스트 블라우스")&&document.body.textContent.includes("화이트 / M")&&document.body.textContent.includes("2개")&&getComputedStyle(document.querySelector(".checkout-layout")).gridTemplateColumns.split(" ").length===2'))throw Error("selection/desktop layout "+JSON.stringify(await js('({summary:document.getElementById("summary").textContent,grid:getComputedStyle(document.querySelector(".checkout-layout")).gridTemplateColumns,width:innerWidth})')));
 await js('document.getElementById("phone-number").value="01012345678";document.getElementById("phone-consent").checked=true;document.getElementById("phone").click()');
 await wait('document.getElementById("error").textContent.includes("잠시 후")&&document.getElementById("phone").disabled===false');
 await js('document.getElementById("phone").click()');
 await wait('document.getElementById("phone-check").disabled===false');
 await js('document.getElementById("phone-code").value="123456";document.getElementById("phone-check").click()');
 await wait('document.getElementById("delivery-form").hidden===false');
 await js('document.getElementById("recipient").value="테스트 고객";document.getElementById("postcode").value="12345";document.getElementById("address1").value="테스트 도로 1";document.getElementById("address2").value="101호";document.getElementById("prepare").click()');
 await wait('document.getElementById("confirm").disabled===false');
 if(!await js('!JSON.stringify(sessionStorage).includes("테스트 고객")&&!JSON.stringify(sessionStorage).includes("01012345678")&&!JSON.stringify(sessionStorage).includes("테스트 도로")'))throw Error('PII persisted');
 await js('document.getElementById("confirm").click()');
 await wait('document.getElementById("auth-note").textContent.includes("주문 #42 접수 완료")');
 await nav('/homepage/storefront/checkout');
 await wait('document.getElementById("guest-status").disabled===false');
 await js('document.getElementById("guest-status").click()');
 await wait('document.getElementById("auth-note").textContent.includes("주문 #42")');
 if((await js('fetch("/__fake_stats").then(r=>r.json())')).writes!==1)throw Error('duplicate confirm');
 await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
 if(!await js('document.documentElement.scrollWidth<=innerWidth&&getComputedStyle(document.querySelector(".checkout-layout")).gridTemplateColumns.split(" ").length===1'))throw Error('mobile layout');
 await js('sessionStorage.removeItem("aicc-guest-operation-v1");sessionStorage.setItem("aicc-guest-cart-v1",JSON.stringify([{product_id:"10",variation_id:"11",quantity:2}]))');
 await nav('/__fake_product');await js('document.getElementById("checkout").click()');
 await wait('location.pathname==="/homepage/storefront/checkout"&&document.getElementById("delivery-form")?.hidden===false');
 if(!await js('document.getElementById("summary").textContent.includes("테스트 블라우스")'))throw Error('cart transfer');
 await js('sessionStorage.removeItem("aicc-guest-checkout-v1")');await nav('/homepage/storefront/checkout');
 await wait('document.getElementById("error").textContent.includes("상품을 선택")');
 if((await js('fetch("/__fake_stats").then(r=>r.json())')).writes!==1)throw Error('automatic mutation');
 await nav('/homepage/storefront');
 await js('document.getElementById("shop-chat-launcher").click();document.getElementById("shop-chat-question").value="배송 42";document.getElementById("shop-chat-form").requestSubmit()');
 await wait('document.getElementById("shop-chat-messages").textContent.includes("TEST-TRACKING")');
 if(!await js('!JSON.stringify(sessionStorage).includes("TEST-TRACKING")'))throw Error('private order notice persisted');
 if((await js('fetch("/__fake_stats").then(r=>r.json())')).writes!==1)throw Error('notice caused order write');
 console.log(JSON.stringify({passed:true,checks:['single product transfer','cart transfer','full page desktop/mobile','phone and delivery','explicit confirm once','reload recovery','no PII persisted','empty selection safe','authenticated chat shipping notice','notice not persisted'],external_provider_requests:0,prod_mutation:false}));
}finally{s.close();}
"""
            driver=driver.replace("https://localhost:18443", "https://"+browser_host+":18443")
            r=subprocess.run(["/opt/homebrew/bin/node","--input-type=module","-e",driver,target["webSocketDebuggerUrl"]],capture_output=True,text=True,timeout=65)
            if r.returncode:raise RuntimeError(r.stderr[-1500:])
            print(r.stdout.strip())
        finally:
            guest_client.close()
            if chrome:
                chrome.terminate()
                try:chrome.wait(timeout=5)
                except subprocess.TimeoutExpired:chrome.kill();chrome.wait()
            server.should_exit=True;thread.join(timeout=5);preview.close()
if __name__=="__main__":main()

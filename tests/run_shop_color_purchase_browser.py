"""Real Chrome on disposable loopback HTTPS; fake inquiry/auth only, zero providers."""
import json,subprocess,tempfile,threading,time,urllib.request,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import uvicorn
from fastapi import FastAPI,Request
from fastapi.responses import Response,HTMLResponse,JSONResponse
from fastapi.testclient import TestClient
from core.homepage.preview import create_app

def main():
    state={'verified':False,'inquiries':[],'sms':0,'quotes':[]}
    import ast
    constants=[v.value for v in ast.walk(ast.parse((Path(__file__).resolve().parents[1]/'ops/macos/shopping/dev_order_runtime.py').read_text())) if isinstance(v,ast.Constant) and isinstance(v.value,str)]
    panel=next(v for v in constants if '<div class="commerce-panel-content" data-guest-shop-product="PRODUCT">' in v)
    def html(pid,cart=False):
        body=panel.replace('PRODUCT',pid).replace('OPTIONS','<option value="'+('37' if pid=='36' else '42')+'">M</option>')
        if cart:body=body.replace('data-guest-shop-product=', 'data-cart-page="true" data-guest-shop-product=',1)
        return HTMLResponse(body)
    preview=TestClient(create_app());app=FastAPI()
    @app.get('/shopping/auth/session')
    def auth():return JSONResponse({},status_code=200 if state['verified'] else 401,headers={'X-CSRF-Token':'isolated-fake-csrf'} if state['verified'] else {})
    @app.get('/__order-dev/chat/history/session')
    def session():return JSONResponse({'ready':True})
    @app.post('/__order-dev/chat/history/link')
    def link():return JSONResponse({'linked':True},status_code=200 if state['verified'] else 403)
    @app.get('/__order-dev/chat/history')
    def history():return JSONResponse({'items':[{**v,'question':v['message'],'answer':'재고 확인 답변','action':'ANSWER','created_at':time.time()} for v in state['inquiries']]})
    @app.post('/__order-dev/phone/start')
    def sms():state['sms']+=1;return JSONResponse({'message':'테스트 인증번호 입력'})
    @app.post('/__order-dev/phone/check')
    def verify():state['verified']=True;return JSONResponse({'verified':True})
    @app.post('/__order-dev/chat/inquiry')
    async def inquiry(request:Request):
        data=await request.json();state['inquiries'].append(data)
        return JSONResponse({'action':'ANSWER','message':'재고 확인 답변','history_saved':True})
    @app.get('/__order-dev/chat/embed/{pid}')
    def embed(pid:str):
        if pid in ('ag-upload-top-0005','ag-upload-top-0006'):
            knit=pid.endswith('0006')
            labels=['그레이','아이보리','브라운','네이비','블랙'] if knit else ['스카이블루','네이비']
            options=''.join('<option value="'+str((110 if knit else 107)+i)+'"'+(' disabled' if knit else '')+'>'+label+(' · 재고 확인 중' if knit else '')+'</option>' for i,label in enumerate(labels))
            body=panel.replace('PRODUCT','106' if knit else '105').replace('OPTIONS',options)
            if knit:body=body.replace('id="add" type="button"','id="add" type="button" disabled').replace('id="single" type="button"','id="single" type="button" disabled')
            return HTMLResponse(body)
        return html('36' if pid.endswith('0001') else '41')
    @app.get('/__order-dev/chat/cart')
    def cart():return html('36',True)
    @app.get('/__order-dev/chat/cart/product/{pid}')
    def meta(pid:str):
        if pid=='105':return JSONResponse({'id':pid,'name':'스트라이프 셔츠','price':'79000','currency':'KRW','product_url':'/homepage/storefront/product/ag-upload-top-0005','variants':[{'id':'108','label':'네이비','available':True}]})
        if pid not in ('36','41'):return JSONResponse({},status_code=404)
        return JSONResponse({'id':pid,'name':'카멜 코트' if pid=='36' else '오트밀 코트','price':'300000' if pid=='36' else '450000','currency':'KRW','product_url':'/homepage/storefront/product/ag-upload-outer-'+('0001' if pid=='36' else '0002'),'variants':[{'id':'37' if pid=='36' else '42','label':'M','available':True}]})
    @app.post('/__order-dev/chat/quote')
    async def quote(request:Request):
        body=await request.json();state['quotes'].append(body);items=[]
        for line in body['line_items']:
            pid=line['product_id'];price=300000 if pid=='36' else 450000
            if pid=='105':price=79000
            if pid not in ('36','41','105'):return JSONResponse({'message':'상품 확인 필요'},status_code=400)
            items.append({'name':'카멜 코트' if pid=='36' else '오트밀 코트','option':'M','quantity':line['quantity'],'subtotal':str(price*line['quantity'])})
        return JSONResponse({'line_items':items,'items_total':str(sum(int(v['subtotal']) for v in items)),'currency':'KRW'})
    @app.get('/__order-dev/chat/capabilities')
    def capabilities():return JSONResponse({'order_confirmation':True,'phone_verification':True,'message':'휴대폰 인증 후 주문'})
    @app.get('/__order-dev/guest-chat.js')
    def guest():return Response((Path(__file__).resolve().parents[1]/'deploy/shopping/wordpress/plugins/ai-shopping-storefront/assets/storefront-guest-chat.js').read_text(),media_type='text/javascript')
    @app.get('/{path:path}')
    def page(path:str):
        r=preview.get('/'+path)
        return Response(r.content,status_code=r.status_code,media_type=r.headers.get('content-type','text/plain'))
    with tempfile.TemporaryDirectory(prefix='aicc-shared-chat-browser-') as d:
        root=Path(d);cert=root/'cert.pem';key=root/'key.pem'
        subprocess.run(['/usr/bin/openssl','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-days','1','-subj','/CN=localhost'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
        server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=18443,ssl_keyfile=str(key),ssl_certfile=str(cert),log_level='error',access_log=False))
        thread=threading.Thread(target=server.run,daemon=True);thread.start()
        chrome=None
        try:
            for _ in range(100):
                if server.started:break
                time.sleep(.05)
            chrome=subprocess.Popen(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','--headless','--disable-gpu','--no-first-run','--no-default-browser-check','--disable-background-networking','--ignore-certificate-errors','--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE localhost','--remote-debugging-address=127.0.0.1','--remote-debugging-port=18444','--user-data-dir='+str(root/'profile'),'about:blank'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            for _ in range(100):
                try:
                    with urllib.request.urlopen('http://127.0.0.1:18444/json/list',timeout=.3) as r:targets=json.load(r)
                    target=next(v for v in targets if v['type']=='page');break
                except Exception:time.sleep(.1)
            else:raise RuntimeError('Chrome CDP unavailable')
            driver=r"""
const socket=new WebSocket(process.argv[1]);await new Promise((r,j)=>{socket.onopen=r;socket.onerror=j;});
let n=0;const pending=new Map();socket.onmessage=e=>{const v=JSON.parse(e.data),p=pending.get(v.id);if(p){pending.delete(v.id);v.error?p.reject(Error(v.error.message)):p.resolve(v.result);}};
const call=(method,params={})=>new Promise((resolve,reject)=>{const id=++n;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));});
const evalJS=async expression=>{const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(r.exceptionDetails.text+' '+r.exceptionDetails.exception?.description);return r.result.value;};
const wait=async expression=>{for(let i=0;i<100;i++){if(await evalJS(expression))return;await new Promise(r=>setTimeout(r,70));}throw Error('timeout '+expression+' '+JSON.stringify(await evalJS('({src:document.getElementById("detail-image")?.src,hidden:document.getElementById("detail-image")?.hidden,status:document.getElementById("color-preview-status")?.textContent,focus:document.activeElement?.outerHTML})')));};
const nav=async path=>{await call('Page.navigate',{url:'https://localhost:18443'+path});await wait('!!document.getElementById("shop-chat-launcher")');await new Promise(r=>setTimeout(r,250));};
const checks=[];
try{

 await call('Page.enable');await nav('/homepage/storefront/product/ag-upload-top-0005');
 await wait('typeof document.getElementById("add")?.onclick==="function"');
 if(!await evalJS('!!document.querySelector("#purchase-color") && !!document.querySelector("#purchase-size") && !!document.querySelector("#purchase-quantity #quantity") && !!document.querySelector("#purchase-actions #add") && !!document.querySelector("#purchase-actions #single") && document.querySelector(".commerce-choice").hidden'))throw Error('unified controls');
 if(!await evalJS('document.getElementById("purchase-actions").getBoundingClientRect().top>=document.getElementById("purchase-controls").getBoundingClientRect().bottom'))throw Error('action placement');
 checks.push('color size quantity and compact actions together');
 await evalJS('document.querySelector("[data-color-id=navy]").click()');
 await wait('document.getElementById("detail-image").src.endsWith("ag-upload-top-0005-color-navy.jpg") && !document.getElementById("detail-image").hidden && document.getElementById("detail-image").naturalWidth>0');
 if(!await evalJS('document.getElementById("variation").value==="108"'))throw Error('color checkout mapping');
 await evalJS('document.getElementById("quantity").value="2";document.getElementById("add").click()');
 await wait('JSON.parse(sessionStorage.getItem("aicc-guest-cart-v1")||"[]").some(v=>v.product_id==="105"&&v.variation_id==="108"&&v.quantity===2)');
 await wait('document.getElementById("cart-added-dialog")?.open');
 await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
 if(!await evalJS('document.getElementById("cart-added-dialog").getBoundingClientRect().width<=innerWidth && document.getElementById("cart-added-go").textContent==="장바구니 가기"'))throw Error('cart popup mobile');
 await evalJS('document.getElementById("cart-added-continue").click()');
 await wait('!document.getElementById("cart-added-dialog").open && document.activeElement.id==="add"');
 await call('Emulation.clearDeviceMetricsOverride');
 await evalJS('document.getElementById("quantity").value="11";document.getElementById("add").click()');
 await wait('document.getElementById("error").textContent.length>0');
 if(!await evalJS('!document.getElementById("cart-added-dialog").open && JSON.parse(sessionStorage.getItem("aicc-guest-cart-v1"))[0].quantity===2'))throw Error('failed add opens popup');
 await evalJS('document.getElementById("quantity").value="2"');
 checks.push('chosen color and quantity quoted into cart');
 await evalJS('document.getElementById("variation").value="107";document.getElementById("variation").dispatchEvent(new Event("change",{bubbles:true}))');
 await wait('document.getElementById("detail-image").src.endsWith("ag-upload-top-0005-model-front.jpg") && !document.getElementById("detail-image").hidden');
 checks.push('provider selection synchronizes photo and canonical options');
 await nav('/homepage/storefront/product/ag-upload-top-0006');
 await wait('typeof document.getElementById("add")?.onclick==="function"');
 for(const color of ['gray','ivory','brown','navy','black']){
   await evalJS('document.querySelector("[data-color-id='+color+']").click()');
   const file=color==='gray'?'ag-upload-top-0006-model-front.jpg':'ag-upload-top-0006-color-'+color+'.jpg';
   await wait('document.getElementById("detail-image").src.endsWith("'+file+'") && !document.getElementById("detail-image").hidden && document.getElementById("detail-image").naturalWidth>0');
   if(!await evalJS('document.querySelectorAll("#detail-variants [aria-pressed=true]").length===1 && document.querySelector("[data-color-id='+color+']").getAttribute("aria-pressed")==="true"'))throw Error('color selected state');
 }
 if(!await evalJS('document.getElementById("add").disabled && document.getElementById("single").disabled && document.getElementById("purchase-size").textContent.includes("사이즈 확인 중")'))throw Error('pending stock bypassed');
 await evalJS('document.querySelector("[data-preview-size=M]").click()');
 if(!await evalJS('document.querySelector("[data-preview-size=M]").getAttribute("aria-pressed")==="true" && document.querySelectorAll(".size-preview-option[aria-pressed=true]").length===1 && document.querySelector("[data-color-id=black]").getAttribute("aria-pressed")==="true" && document.getElementById("single").disabled && document.getElementById("add").disabled'))throw Error('temporary size bypasses stock or color');
 checks.push('all five knit colors preview while stock-gated');
 await evalJS('window.realImage=window.Image;window.pendingImages=[];window.Image=class {set src(value){this.path=value;window.pendingImages.push(this)}};for(const c of ["gray","navy","black"])document.querySelector("[data-color-id="+c+"]").click();pendingImages[2].onload();pendingImages[0].onload();pendingImages[1].onload()');
 if(!await evalJS('document.getElementById("detail-image").src.endsWith("color-black.jpg") && !document.getElementById("detail-image").hidden'))throw Error('stale image overwrote selection');
 await evalJS('document.querySelector("[data-color-id=brown]").click();pendingImages[3].onerror()');
 if(!await evalJS('document.getElementById("detail-image").hidden && document.getElementById("color-preview-status").textContent.includes("불러오지 못")'))throw Error('failure shows wrong color');
 await evalJS('window.Image=window.realImage;document.querySelector("[data-color-id=navy]").focus()');
 await call('Page.bringToFront');
 await call('Emulation.setFocusEmulationEnabled',{enabled:true});
 await call('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',text:'\r',unmodifiedText:'\r',windowsVirtualKeyCode:13,nativeVirtualKeyCode:13});
 await call('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13});
 await wait('document.getElementById("detail-image").src.endsWith("color-navy.jpg") && !document.getElementById("detail-image").hidden');
 checks.push('rapid selection failure recovery and keyboard activation');
 await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
 if(!await evalJS('document.documentElement.scrollWidth<=innerWidth && document.getElementById("quantity").getBoundingClientRect().left>=document.getElementById("purchase-size").getBoundingClientRect().right && document.getElementById("single").getBoundingClientRect().height<=44'))throw Error('mobile unified layout');
 checks.push('mobile color size quantity layout');
 await evalJS('sessionStorage.removeItem("aicc-guest-cart-v1")');
 await call('Emulation.clearDeviceMetricsOverride');
 await nav('/homepage/storefront/product/ag-upload-outer-0001');

 await wait('typeof document.getElementById("add")?.onclick==="function"');
 if(!await evalJS('document.getElementById("variant-section").compareDocumentPosition(document.getElementById("commerce-panel"))&Node.DOCUMENT_POSITION_FOLLOWING'))throw Error('order placement');
 await evalJS('document.getElementById("add").click()');
 await wait('JSON.parse(sessionStorage.getItem("aicc-guest-cart-v1")||"[]").length===1');checks.push('PDP add and order under options');
 await wait('document.getElementById("cart-added-dialog")?.open');
 await evalJS('document.getElementById("cart-added-go").click()');
 await wait('location.pathname==="/homepage/storefront/cart" && document.querySelector("#cart a")?.textContent.includes("카멜")');

 await nav('/homepage/storefront/product/ag-upload-outer-0002');
 await wait('typeof document.getElementById("add")?.onclick==="function"');
 await evalJS('document.getElementById("add").click()');await wait('JSON.parse(sessionStorage.getItem("aicc-guest-cart-v1")||"[]").length===2');
 await evalJS('document.querySelector(".header-cart").click()');await wait('document.querySelector("[data-cart-page=true] #cart")?.textContent.includes("오트밀 코트")');checks.push('cart navigation and product names');
 await evalJS('document.querySelector("#cart select").value="3";document.querySelector("#cart select").dispatchEvent(new Event("change"))');await wait('JSON.parse(sessionStorage.getItem("aicc-guest-cart-v1"))[0].quantity===3');checks.push('quantity update');
 await nav('/homepage/storefront/cart');await wait('document.querySelector("#cart select")?.value==="3"');checks.push('reload cart persistence');
 await evalJS('document.getElementById("checkout").click()');await wait('!document.getElementById("order").hidden && document.getElementById("summary").textContent.includes("1350000")');checks.push('server quote checkout');
 await evalJS('document.querySelector("#cart button").click()');await wait('document.getElementById("order").hidden && document.getElementById("confirm").disabled');checks.push('cart edit invalidates review');
 await evalJS('document.getElementById("clear").click()');await wait('document.getElementById("cart").textContent.includes("비어") && document.getElementById("checkout").disabled');checks.push('empty cart');
 await evalJS('sessionStorage.setItem("aicc-guest-cart-v1",JSON.stringify([{product_id:"36",variation_id:"37",quantity:1}]));sessionStorage.setItem("aicc-guest-operation-v1",JSON.stringify({draft_id:"a".repeat(48),operation_key:"guest-order-"+"b".repeat(48)}))');
 await nav('/homepage/storefront/cart');await wait('document.getElementById("cart").textContent.includes("카멜 코트")');
 await evalJS('document.getElementById("clear").click()');if(!await evalJS('JSON.parse(sessionStorage.getItem("aicc-guest-cart-v1")||"[]").length===1 && !!sessionStorage.getItem("aicc-guest-operation-v1") && document.getElementById("checkout").disabled'))throw Error('pending operation lost');checks.push('pending order preserved');
 await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
 if(!await evalJS('document.documentElement.scrollWidth<=innerWidth && document.getElementById("checkout").getBoundingClientRect().height<=44'))throw Error('mobile compact layout');checks.push('mobile compact cart');
 console.log(JSON.stringify({passed:true,checks}));
}finally{socket.close();}
"""
            r=subprocess.run(['/opt/homebrew/bin/node','--input-type=module','-e',driver,target['webSocketDebuggerUrl']],capture_output=True,text=True,timeout=40)
            if r.returncode:raise RuntimeError(r.stderr[-2000:])
            result=json.loads(r.stdout)
            assert len(state['quotes'])==4 and state['quotes'][0]['line_items']==[{'product_id':'105','variation_id':'108','quantity':2}] and state['quotes'][-1]['line_items'][0]['quantity']==3
            assert state['inquiries']==[]
            assert state['sms']==0
            result.update(external_provider_requests=0,prod_mutation=False,quoted_cart_items=2,mock_sms_requests=state['sms'])
            print(json.dumps(result,ensure_ascii=False))
        finally:
            if chrome:
                chrome.terminate()
                try:chrome.wait(timeout=5)
                except subprocess.TimeoutExpired:chrome.kill();chrome.wait()
            server.should_exit=True;thread.join(timeout=5);preview.close()
if __name__=='__main__':main()

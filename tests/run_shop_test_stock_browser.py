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
    products=preview.get('/shopping/products?page_size=100').json()['items']
    lookup={r['id']:{**r,'provider_id':str(1000+i),'provider_variants':[{'id':str(2000+i*100+j),'label':v['label'],'available':v['available']} for j,v in enumerate(r['variants'])]} for i,r in enumerate(products)}
    providers={r['provider_id']:r for r in lookup.values()}
    @app.get('/__order-dev/chat/embed/{pid}')
    def embed(pid:str):
        import html as escape
        row=lookup[pid]
        options=''.join('<option value="'+v['id']+'">'+escape.escape(v['label'])+'</option>' for v in row['provider_variants'])
        return HTMLResponse(panel.replace('PRODUCT',row['provider_id']).replace('OPTIONS',options))
    @app.get('/__order-dev/chat/cart')
    def cart():return html('36',True)
    @app.get('/__order-dev/chat/cart/product/{pid}')
    def meta(pid:str):
        row=providers[pid]
        return JSONResponse({'id':pid,'name':row['name'],'price':row['price'],'currency':'KRW','product_url':'/homepage/storefront/product/'+row['id'],'variants':row['provider_variants']})
    @app.post('/__order-dev/chat/quote')
    async def quote(request:Request):
        body=await request.json();state['quotes'].append(body);items=[]
        for line in body['line_items']:
            row=providers[line['product_id']]
            variant=next(v for v in row['provider_variants'] if v['id']==line['variation_id'])
            if line['quantity']>3:return JSONResponse({'message':'재고 수량을 초과했습니다.'},status_code=400)
            items.append({'name':row['name'],'option':variant['label'],'quantity':line['quantity'],'subtotal':str(int(row['price'])*line['quantity'])})
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
const wait=async expression=>{for(let i=0;i<100;i++){if(await evalJS(expression))return;await new Promise(r=>setTimeout(r,70));}throw Error('timeout '+expression);};
const nav=async path=>{await call('Page.navigate',{url:'https://localhost:18443'+path});await wait('!!document.getElementById("shop-chat-launcher")');await new Promise(r=>setTimeout(r,250));};
const checks=[];
try{
 await call('Page.enable');await nav('/homepage/storefront/product/ag-upload-top-0006');
 await wait('typeof document.getElementById("add")?.onclick==="function" && !document.getElementById("add").disabled');
 await evalJS('document.querySelector("[data-preview-size=M]").click();document.querySelector("[data-color-id=navy]").click()');
 await wait('document.getElementById("variation").selectedOptions[0]?.textContent==="네이비 / M" && document.getElementById("detail-image").src.endsWith("color-navy.jpg") && !document.getElementById("detail-image").hidden');
 const variant=await evalJS('document.getElementById("variation").value');
 await evalJS('document.getElementById("quantity").value="2";document.getElementById("add").click()');
 await wait('document.getElementById("cart-added-dialog")?.open');
 if(!await evalJS('JSON.parse(sessionStorage.getItem("aicc-guest-cart-v1"))[0].variation_id==='+JSON.stringify(variant)+' && JSON.parse(sessionStorage.getItem("aicc-guest-cart-v1"))[0].quantity===2'))throw Error('color size quantity mismatch');
 checks.push('combined color size quantity and anonymous add');
 await evalJS('document.getElementById("cart-added-continue").click()');await wait('!document.getElementById("cart-added-dialog").open');
 await evalJS('document.getElementById("quantity").value="4";document.getElementById("add").click()');
 await wait('document.getElementById("error").textContent.includes("재고")');
 if(!await evalJS('!document.getElementById("cart-added-dialog").open && JSON.parse(sessionStorage.getItem("aicc-guest-cart-v1"))[0].quantity===2'))throw Error('overstock cart mutated');
 checks.push('insufficient stock cannot add or show success');
 await evalJS('document.getElementById("variation").selectedOptions[0].disabled=true;document.querySelector("[data-preview-size=M]").click()');
 if(!await evalJS('document.getElementById("add").disabled && document.getElementById("single").disabled && document.getElementById("variation").value===""'))throw Error('unavailable combination fallback');
 await evalJS('document.querySelector("[data-preview-size=L]").click()');
 if(!await evalJS('!document.getElementById("add").disabled && document.getElementById("variation").selectedOptions[0].textContent==="네이비 / L"'))throw Error('size recovery');
 checks.push('unavailable combination blocks checkout and recovers');
 await nav('/homepage/storefront/cart');await wait('document.querySelector("#cart a")?.textContent.includes("하이넥")');
 if(!await evalJS('document.getElementById("cart").textContent.includes("네이비 / M")'))throw Error('cart option lost');
 checks.push('cart displays preserved color and size');
 await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
 await nav('/homepage/storefront/product/ag-upload-top-0006');await wait('typeof document.getElementById("add")?.onclick==="function"');
 if(!await evalJS('document.documentElement.scrollWidth<=innerWidth && !!document.querySelector("#purchase-quantity #quantity")'))throw Error('mobile combined layout');
 checks.push('mobile combined layout');
 console.log(JSON.stringify({passed:true,checks}));
}finally{socket.close();}

"""
            r=subprocess.run(['/opt/homebrew/bin/node','--input-type=module','-e',driver,target['webSocketDebuggerUrl']],capture_output=True,text=True,timeout=40)
            if r.returncode:raise RuntimeError(r.stderr[-2000:])
            result=json.loads(r.stdout)
            assert len(state['quotes'])==2 and state['quotes'][0]['line_items'][0]['quantity']==2 and state['quotes'][1]['line_items'][0]['quantity']==4
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

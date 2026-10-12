"""Real headless Chrome over disposable loopback HTTP, zero provider/SMS traffic."""
import json,subprocess,tempfile,threading,time,sys,urllib.request
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import uvicorn
from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse,Response
from fastapi.testclient import TestClient
from core.homepage.preview import create_app
from core.shopping.customer_order_notices import order_notices

def main():
    preview=TestClient(create_app());app=FastAPI();calls=[]
    order={'order_id':15,'review_state':'CONFIRMED','payment':{'state':'PAID'},'fulfillment':{'state':'DELIVERED'},'return_status':{'state':'RETURN_RESTOCKED'},'refund':{'state':'RECORDED','amount':'58000','currency':'KRW','recorded_at':1000},'items':[{'name':'테스트 블라우스','option':'M','quantity':2}],'total':'58000','currency':'KRW','delivery':{'first_name':'테스트고객'},'cases':[{'id':'a1b2c3d4','kind':'RETURN','state':'RETURN_RESTOCKED','attachments':0}],'return_available':False,'exchange_available':False}
    order['customer_messages']=order_notices(order)
    @app.get('/shopping/auth/session')
    def auth():return JSONResponse({},headers={'X-CSRF-Token':'isolated-csrf'})
    @app.post('/__order-dev/orders/lookup')
    async def lookup(request:Request):
        data=await request.json();calls.append(data)
        assert request.headers.get('x-csrf-token')=='isolated-csrf' and data=={'order_number':'15','phone':'01000000000'}
        return JSONResponse({'order':order})
    @app.get('/{path:path}')
    def page(path:str):
        response=preview.get('/'+path);body=response.content
        if path=='homepage/storefront/my-orders':
            body+="<script>window.addEventListener('load',async()=>{document.getElementById('orders-number').value='15';document.getElementById('lookup-phone').value='01000000000';await document.getElementById('orders-lookup').onclick();const mark=document.createElement('p');mark.id='isolated-browser-result';mark.textContent=document.querySelector('.order-state')?.textContent==='환불완료'&&document.querySelector('.order-card')?.textContent.includes('58000 KRW')?'REFUND_BROWSER_PASS':'REFUND_BROWSER_FAIL';document.body.appendChild(mark);});</script>".encode()
        return Response(body,status_code=response.status_code,media_type=response.headers.get('content-type','text/plain'))
    with tempfile.TemporaryDirectory(prefix='aicc-refund-browser-') as tmp:
        server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=18447,access_log=False,log_level='error'));thread=threading.Thread(target=server.run,daemon=True);thread.start()
        chrome=None
        try:
            for _ in range(100):
                if server.started:break
                time.sleep(.05)
            chrome=subprocess.Popen(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','--headless','--disable-gpu','--no-first-run','--no-default-browser-check','--disable-background-networking','--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE localhost','--user-data-dir='+tmp+'/profile','--remote-debugging-address=127.0.0.1','--remote-debugging-port=18448','about:blank'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            for _ in range(100):
                try:
                    with urllib.request.urlopen('http://127.0.0.1:18448/json/list',timeout=.3) as response:targets=json.load(response)
                    target=next(x for x in targets if x['type']=='page');break
                except Exception:time.sleep(.1)
            else:raise RuntimeError('REFUND_BROWSER_CDP_UNAVAILABLE')
            driver=r"""
const socket=new WebSocket(process.argv[1]);await new Promise((r,j)=>{socket.onopen=r;socket.onerror=j});let n=0;const pending=new Map();socket.onmessage=e=>{const v=JSON.parse(e.data),p=pending.get(v.id);if(p){pending.delete(v.id);v.error?p.reject(Error(v.error.message)):p.resolve(v.result)}};
const call=(method,params={})=>new Promise((resolve,reject)=>{const id=++n;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}))});
const evalJS=async expression=>{const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(r.exceptionDetails.text);return r.result.value};
try{await call('Page.enable');await call('Page.navigate',{url:'http://localhost:18447/homepage/storefront/my-orders'});let text='';for(let i=0;i<100;i++){text=await evalJS('document.getElementById("isolated-browser-result")?.textContent||""');if(text)break;await new Promise(r=>setTimeout(r,70))}if(text!=='REFUND_BROWSER_PASS')throw Error('REFUND_RENDER_FAILED '+text);const page=await evalJS('document.querySelector(".order-card").textContent');if(!page.includes('환불완료')||!page.includes('58000 KRW')||page.includes('환불검토'))throw Error('REFUND_DETAILS_INCONSISTENT');process.stdout.write('REFUND_BROWSER_PASS')}finally{socket.close()}
"""
            result=subprocess.run(['/opt/homebrew/bin/node','--input-type=module','-e',driver,target['webSocketDebuggerUrl']],capture_output=True,text=True,timeout=20)
            if result.returncode:raise RuntimeError(result.stderr[-1000:])
            assert 'REFUND_BROWSER_PASS' in result.stdout
            assert len(calls)==1
            print(json.dumps({'passed':True,'checks':['real order page refund status','refund amount displayed','case row completed','verified lookup CSRF'],'external_messages':0,'prod_mutation':False}))
        finally:
            if chrome is not None:
                chrome.terminate()
                try:chrome.wait(timeout=5)
                except subprocess.TimeoutExpired:chrome.kill();chrome.wait(timeout=5)
            server.should_exit=True;thread.join(5);preview.close()
if __name__=='__main__':main()

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
    state={'verified':False,'inquiries':[],'sms':0}
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
    def embed(pid:str):return HTMLResponse('<div data-guest-shop-product="'+('36' if pid.endswith('0001') else '41')+'"></div>')
    @app.get('/__order-dev/guest-chat.js')
    def guest():return Response('/* isolated order script stub; checkout regression is separate */',media_type='text/javascript')
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
 await call('Page.enable');await nav('/homepage/storefront');
 await evalJS('document.getElementById("shop-chat-launcher").click()');
 await wait('document.getElementById("shop-chat-messages").textContent.includes("어떤 상품")');checks.push('bot asks first');
 await evalJS('document.getElementById("shop-chat-product").value="ag-upload-outer-0001";document.getElementById("shop-chat-product").dispatchEvent(new Event("change"));document.getElementById("shop-chat-question").value="M 재고 있나요?";document.getElementById("shop-chat-form").requestSubmit()');
 await wait('document.getElementById("shop-chat-messages").textContent.includes("재고 확인 답변")');checks.push('tagged first inquiry');
 await nav('/homepage/storefront/product/ag-upload-outer-0002');
 await evalJS('document.getElementById("shop-chat-launcher").click()');
 await wait('document.getElementById("shop-chat-product").value==="ag-upload-outer-0002"');
 if(!await evalJS('document.getElementById("shop-chat-messages").textContent.includes("M 재고 있나요?")'))throw Error('lost navigation history');
 await evalJS('document.getElementById("shop-chat-question").value="L 재고 있나요?";document.getElementById("shop-chat-form").requestSubmit()');
 await wait('document.getElementById("shop-chat-messages").textContent.includes("L 재고 있나요?") && !document.getElementById("shop-chat-send").disabled');checks.push('navigation history and second product binding');
 await evalJS('document.getElementById("shop-chat-stock").click()');await wait('document.getElementById("shop-chat-messages").textContent.includes("재고와 사이즈 옵션 알려주세요") && !document.getElementById("shop-chat-send").disabled');checks.push('stock inquiry in shared chatbot');
 await nav('/homepage/storefront');
 await evalJS('document.getElementById("shop-chat-launcher").click()');
 if(!await evalJS('document.getElementById("shop-chat-messages").textContent.includes("M 재고 있나요?") && document.getElementById("shop-chat-messages").textContent.includes("L 재고 있나요?")'))throw Error('lost reload history');
 checks.push('reload persistence');
 await evalJS('document.getElementById("shop-chat-history").click()');
 await wait('!document.getElementById("shop-chat-phone").hidden');
 await evalJS('document.getElementById("shop-chat-code").value="000000";document.getElementById("shop-chat-verify").click()');
 await wait('!document.getElementById("shop-chat-recent").hidden && document.getElementById("shop-chat-recent").textContent.includes("M 재고 있나요?")');checks.push('verified history');
 await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
 if(!await evalJS('document.documentElement.scrollWidth<=innerWidth'))throw Error('mobile overflow');checks.push('mobile dialog');
 console.log(JSON.stringify({passed:true,checks}));
}finally{socket.close();}
"""
            r=subprocess.run(['/opt/homebrew/bin/node','--input-type=module','-e',driver,target['webSocketDebuggerUrl']],capture_output=True,text=True,timeout=40)
            if r.returncode:raise RuntimeError(r.stderr[-2000:])
            result=json.loads(r.stdout)
            assert [x['product_id'] for x in state['inquiries']]==['36','41','41']
            assert state['sms']==0
            result.update(external_provider_requests=0,prod_mutation=False,inquiry_product_ids=['36','41','41'],mock_sms_requests=state['sms'])
            print(json.dumps(result,ensure_ascii=False))
        finally:
            if chrome:
                chrome.terminate()
                try:chrome.wait(timeout=5)
                except subprocess.TimeoutExpired:chrome.kill();chrome.wait()
            server.should_exit=True;thread.join(timeout=5);preview.close()
if __name__=='__main__':main()

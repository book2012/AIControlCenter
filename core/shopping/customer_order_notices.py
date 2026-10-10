"""Customer transaction/shipping messages. Read-only; no SMS dispatch."""
import json,re
from fastapi import Request
from fastapi.responses import JSONResponse
GREETING="안녕하세요 agachichi 입니다"

def order_notices(order,bank=None):
    number=str(order['order_id'])
    lines=[str(v['name'])+' / '+str(v.get('option') or '기본')+' · '+str(v['quantity'])+'개' for v in order['items']]
    summary='주문번호: '+number+'\n'+'\n'.join(lines)+'\n총 금액: '+str(order['total'])+' '+order['currency']
    review=order.get('review_state');payment=order.get('payment',{}).get('state');shipping=order.get('fulfillment',{})
    result=[]
    def add(kind,text):result.append({'id':number+':'+kind,'kind':kind,'message':GREETING+'\n'+text})
    if review=='REJECTED':add('REJECTED',summary+'\n주문이 거절되었습니다. 챗봇으로 문의해 주세요.');return result
    if review!='CONFIRMED':add('RECEIVED',summary+'\n주문을 접수했습니다. 운영자가 상품과 재고를 확인하고 있습니다.');return result
    text=summary+'\n주문이 확인되었습니다.'
    if payment!='PAID':
        text+='\n입금 확인을 기다리고 있습니다.'
        if isinstance(bank,dict) and all(isinstance(bank.get(k),str) and bank[k].strip() and len(bank[k])<=200 for k in ('name','account','holder')):
            text+='\n입금 계좌: '+bank['name']+' '+bank['account']+'\n예금주: '+bank['holder']
        else:text+='\n계좌 안내는 운영자에게 문의해 주세요.'
    add('CONFIRMED',text)
    if payment=='PAID':add('PAID','주문 #'+number+' 입금이 확인되었습니다. 배송을 준비하고 있습니다.')
    if shipping.get('state') in ('SHIPPED','DELIVERED'):
        add('SHIPPED','주문 #'+number+' 배송을 시작했습니다.\n택배사: '+str(shipping.get('carrier') or '확인 중')+'\n운송장번호: '+str(shipping.get('tracking') or '확인 중'))
    if shipping.get('state')=='DELIVERED':add('DELIVERED','주문 #'+number+' 배송이 완료되었습니다. 환불·교환은 주문조회 페이지에서 요청해 주세요.')
    return result

def mount_order_notices(app,*,path,store,authenticate,verified_phone,bank_provider=None):
    @app.post(path,include_in_schema=False)
    async def notices(request:Request):
        try:
            auth=authenticate(request);phone=verified_phone(auth.customer_id)
            raw=bytearray()
            async for chunk in request.stream():
                if len(raw)+len(chunk)>1024:raise ValueError('BODY_TOO_LARGE')
                raw.extend(chunk)
            data=json.loads(raw)
            if type(data) is not dict or set(data)!={'order_number'} or type(data['order_number']) is not str or not re.fullmatch(r'[1-9][0-9]{0,18}',data['order_number']):raise ValueError('INVALID_ORDER')
            order=store.lookup(auth.customer_id,data['order_number'],phone,phone)
            bank=bank_provider() if bank_provider else None
            return JSONResponse({'order_number':data['order_number'],'messages':order_notices(order,bank),'transaction_sms':False},headers={'Cache-Control':'no-store','X-Robots-Tag':'noindex, nofollow'})
        except Exception:return JSONResponse({'message':'휴대폰 인증 후 본인의 주문번호를 확인해 주세요.'},status_code=403,headers={'Cache-Control':'no-store'})

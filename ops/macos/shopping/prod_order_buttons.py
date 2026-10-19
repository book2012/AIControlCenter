"""Production-only Telegram order cards and callback validation."""
import re
_FILTER_STATES={"PENDING_REVIEW":"확인 대기","AWAITING_DEPOSIT":"입금 대기","READY_TO_SHIP":"배송 준비","SHIPPED":"배송 중","COMPLETED":"배송 완료","RETURN_APPROVED":"환불 승인","RETURN_RECEIVED":"환불 회수","RETURN_RESTOCKED":"환불 검수","REFUND_RECORDED":"환불 완료","CANCELLED":"취소 완료","REJECTED":"주문 거절","STOCK_BLOCKED":"재고 확인"}

_ORDER = re.compile(r"(?m)^([0-9]{10}) · (010[0-9]{8}) · ([^·\n]+)$")
_PAGE = re.compile(r"(?m)^AICC_ORDER_PAGE:(ALL|STATUS):([A-Z_]+):([0-9]{1,6}):([0-9]{1,6}):([0-9]{1,9})$")
_CANCEL_STATES = {"확인대기", "확인완료", "입금대기", "배송준비"}

def menu_markup():
    return {"inline_keyboard":[
        [{"text":"📦 주문 목록","callback_data":"aiccp:menu:orders"}],
        [{"text":"🔎 주문 조회 안내","callback_data":"aiccp:menu:help"}],
        [{"text":"🛍 상품 목록","callback_data":"aiccp:menu:products"}],
    ]}

def reply_markup(text):
    if not isinstance(text,str): return None
    body=text.split("[운영]\n",1)[-1].strip()
    if body in ("주문 목록 보기를 선택해 주세요.","조회할 주문 상태를 선택해 주세요."):
        states=list(_FILTER_STATES.items())
        rows=[[{"text":"📋 전체 보기","callback_data":"aiccp:orders:all:0"}]]
        for i in range(0,len(states),2):
            rows.append([{"text":"🏷 "+label,"callback_data":"aiccp:orders:status:"+code+":0"} for code,label in states[i:i+2]])
        return {"inline_keyboard":rows}
    nav=re.fullmatch(r"주문 더 보기 · (ALL|STATUS):([A-Z_]+):([0-9]{1,6})",body)
    if nav:return {"inline_keyboard":[[{"text":"다음 주문 보기 ➡️","callback_data":"aiccp:orders:next:"+nav[2]+":"+str(int(nav[3])+1)}]]}
    match=_ORDER.search(body)
    if not match:return menu_markup() if "관리자 메뉴" in body else None
    number,phone,state=(v.strip() for v in match.groups())
    buttons=[{"text":"📋 상세 보기","callback_data":"aiccp:item:detail:"+number}]
    actions={"확인대기":("✅ 주문 확인","confirm"),"입금대기":("💳 입금 확인","payment"),
             "배송준비":("🚚 배송 등록","ship"),"배송중":("📦 배송 완료","delivered")}
    if state in actions:
        label,action=actions[state];buttons.append({"text":label,"callback_data":"aiccp:item:"+action+":"+number})
    if state in _CANCEL_STATES:buttons.append({"text":"❌ 주문 취소","callback_data":"aiccp:item:cancel:"+number})
    return {"inline_keyboard":[buttons]}

def callback_command(update,cfg):
    q=update.get("callback_query")
    if not isinstance(q,dict):return None
    actor=q.get("from",{});msg=q.get("message",{});chat=msg.get("chat",{});bot=msg.get("from",{})
    if (not isinstance(actor,dict) or not isinstance(msg,dict) or chat.get("type")!="private"
        or chat.get("id")!=cfg["operator_chat_id"] or actor.get("id") not in cfg["operator_user_ids"]
        or actor.get("is_bot") is not False or bot.get("is_bot") is not True
        or bot.get("username")!="mommychichi_bot" or type(msg.get("text")) is not str
        or type(q.get("id")) is not str or type(q.get("data")) is not str):return None
    data=q["data"];body=msg["text"].split("[운영]\n",1)[-1].strip()
    menus={"orders":"주문목록 메뉴","help":"주문조회 도움말","products":"/products"}
    m=re.fullmatch(r"aiccp:menu:([a-z]+)",data)
    if m and body=="[운영] 관리자 메뉴" and m[1] in menus:return q["id"],actor["id"],menus[m[1]],"📦 주문 목록" if m[1]=="orders" else "선택 메뉴"
    if data=="aiccp:orders:all:0" and body=="주문 목록 보기를 선택해 주세요.":
        return q["id"],actor["id"],"주문목록 전체 ALL 0","📋 전체 보기"
    state=re.fullmatch(r"aiccp:orders:status:([A-Z_]+):([0-9]{1,6})",data)
    if state and body in ("주문 목록 보기를 선택해 주세요.","조회할 주문 상태를 선택해 주세요.") and state[1] in _FILTER_STATES:
        return q["id"],actor["id"],"주문목록 상태 "+state[1]+" "+state[2],"🏷 "+_FILTER_STATES[state[1]]
    page=re.fullmatch(r"aiccp:orders:next:([A-Z_]+):([1-9][0-9]{0,5})",data);nav=re.fullmatch(r"주문 더 보기 · (ALL|STATUS):([A-Z_]+):([0-9]{1,6})",body)
    if page and nav and int(page[2])==int(nav[3])+1 and ((page[1]=="ALL" and nav[1]=="ALL") or (page[1]==nav[2] and nav[1]=="STATUS")):
        mode="전체 ALL" if page[1]=="ALL" else "상태 "+page[1]
        return q["id"],actor["id"],"주문목록 "+mode+" "+page[2],"➡️ 다음 주문 보기"
    item=re.fullmatch(r"aiccp:item:(detail|confirm|cancel|payment|ship|delivered):([0-9]{10})",data)
    if not item:return None
    source=next((m for m in _ORDER.finditer(msg["text"]) if m[1]==item[2]),None)
    if not source:return None
    number,phone,state=(v.strip() for v in source.groups())
    valid={"detail":True,"confirm":state=="확인대기","cancel":state in _CANCEL_STATES,"payment":state=="입금대기","ship":state=="배송준비","delivered":state=="배송중"}
    if not valid[item[1]]:return None
    action={"detail":"주문상세","confirm":"주문확인","cancel":"주문 취소","payment":"입금 확인","ship":"배송","delivered":"배송 완료"}[item[1]]
    return q["id"],actor["id"],phone+" 고객 "+action+" #"+number,{"detail":"📋 상세 보기","confirm":"✅ 주문 확인","cancel":"❌ 주문 취소","payment":"💳 입금 확인","ship":"🚚 배송 등록","delivered":"📦 배송 완료"}[item[1]]+" · 주문 #"+number

def send_reply(transport,text,context=None):
    if not isinstance(text,str):return
    page=_PAGE.search(text);body=_PAGE.sub("",text,count=1).strip() if page else text.strip()
    matches=list(_ORDER.finditer(body))
    if matches:
        for i,m in enumerate(matches):
            end=matches[i+1].start() if i+1<len(matches) else len(body)
            card=body[m.start():end].strip()
            if i==0:
                heading=body[:m.start()].strip()
                card="\n".join(value for value in (context,heading,card) if value)
            transport.send_message(card,reply_markup=reply_markup(card))
        if page and int(page[3])+1<int(page[4]):
            nav="주문 더 보기 · "+page[1]+":"+page[2]+":"+page[3]
            transport.send_message(nav,reply_markup=reply_markup(nav))
        return
    if context:body=context+"\n\n"+body
    markup=reply_markup(body)
    if markup:transport.send_message(body,reply_markup=markup)
    else:transport.send_message(body)

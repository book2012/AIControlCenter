"""DEV-only bot consumer; private bridge, independent cursor, no PROD handler."""
import fcntl,json,logging,re,sqlite3,time
from pathlib import Path
from pydantic import SecretStr
from core.shopping.order_core.telegram import OrderTelegramTransport
from ops.macos.shopping.dev_operator_bridge_client import compose_dev_command_client

PRIVATE=Path('/Users/kyouhan/.config/aicontrolcenter-dev-order')
DATA=Path('/Users/kyouhan/AIControlCenterRuntime/dev-order/data')
LOGGER=logging.getLogger("aicc.dev.telegram")
_ORDER_LINE=re.compile(r"(?m)^([0-9]{11}) 고객님 주문\n주문 ([0-9]{10}) ·")
_ORDER_LIST_LINE=re.compile(r"(?m)^([0-9]{10}) · (010[0-9]{8}) · ([^·\n]+) ·")
_ORDER_PAGE=re.compile(r"(?m)^AICC_ORDER_PAGE:(ALL|STATUS):([A-Z_]+):([0-9]{1,6}):([0-9]{1,6}):([0-9]{1,9})$")
_ORDER_NAV=re.compile(r"^주문 더 보기 · (ALL|STATUS):([A-Z_]+):([0-9]{1,6})$")
_OPERATOR_PREFIX="안녕하세요 agachichi 입니다\n[개발]\n"

def _operator_body(text):
    return text.strip().removeprefix(_OPERATOR_PREFIX).strip() if type(text) is str else ""
_LIST_CANCEL_STATES={"확인대기","확인완료","입금대기","배송준비"}
_FILTER_STATES={"PENDING_REVIEW":"확인 대기","AWAITING_DEPOSIT":"입금 대기","READY_TO_SHIP":"배송 준비","SHIPPED":"배송 중","COMPLETED":"배송 완료","RETURN_APPROVED":"환불 승인","RETURN_RECEIVED":"환불 회수","RETURN_RESTOCKED":"환불 검수","REFUND_RECORDED":"환불 완료","CANCELLED":"취소 완료","REJECTED":"주문 거절","STOCK_BLOCKED":"재고 확인"}


def menu_markup():
    return {"inline_keyboard":[
        [{"text":"📦 주문 목록","callback_data":"aicc:menu:orders"},
         {"text":"🔎 주문 조회 안내","callback_data":"aicc:menu:order_help"}],
        [{"text":"🛍 상품 목록","callback_data":"aicc:menu:products"},
         {"text":"📊 재고 확인","callback_data":"aicc:menu:stock"}],
        [{"text":"➕ 상품 등록 안내","callback_data":"aicc:menu:product_help"}],
    ]}


def reply_markup(text):
    """Offer a button-first order browser and actions bound to one order card."""
    if type(text) is str and "[DEV] 관리자 메뉴" in text:
        return menu_markup()
    if type(text) is not str:
        return None
    text=_operator_body(text)
    if text.strip() in ("주문 목록 보기를 선택해 주세요.","조회할 주문 상태를 선택해 주세요."):
        states=list(_FILTER_STATES.items());rows=[[{"text":"📋 전체 보기","callback_data":"aicc:orders:all:0"}]]
        for i in range(0,len(states),2):
            rows.append([{"text":"🏷 "+label,"callback_data":"aicc:orders:status:"+code+":0"} for code,label in states[i:i+2]])
        return {"inline_keyboard":rows}
    nav=_ORDER_NAV.fullmatch(text.strip())
    if nav:
        scope,state,page=nav.groups()
        token="ALL" if scope=="ALL" else state
        return {"inline_keyboard":[[{"text":"다음 주문 보기 ➡️","callback_data":"aicc:orders:next:"+token+":"+str(int(page)+1)}]]}
    page_match=_ORDER_PAGE.search(text)
    if page_match:
        _,state,page,pages,_=page_match.groups(); page=int(page);pages=int(pages)
        if page+1<pages:
            scope="ALL" if page_match[1]=="ALL" else state
            return {"inline_keyboard":[[{"text":"다음 주문 보기 ➡️","callback_data":"aicc:orders:next:"+scope+":"+str(page+1)}]]}
        return None
    list_rows=list(_ORDER_LIST_LINE.finditer(text))
    if list_rows:
        number,phone,state=(v.strip() for v in list_rows[0].groups())
        row=[{"text":"📋 상세 보기","callback_data":"aicc:item:detail:"+number}]
        if state=="확인대기":row.append({"text":"✅ 주문 확인","callback_data":"aicc:item:confirm:"+number})
        if state=="입금대기":row.append({"text":"💳 입금 확인","callback_data":"aicc:item:payment:"+number})
        if state=="배송준비":row.append({"text":"🚚 배송 등록","callback_data":"aicc:item:ship:"+number})
        if state=="배송중":row.append({"text":"📦 배송 완료","callback_data":"aicc:item:delivered:"+number})
        if state in _LIST_CANCEL_STATES:row.append({"text":"❌ 주문 취소","callback_data":"aicc:item:cancel:"+number})
        return {"inline_keyboard":[row]}
    match=_ORDER_LINE.search(text)
    if match is None:
        return None
    phone,number=match.groups()
    confirm=f"aicc:confirm:{number}"
    detail=f"aicc:detail:{number}"
    if max(len(v.encode()) for v in (confirm,detail))>64:
        return None
    cancel=f"aicc:cancel:{number}"
    if len(cancel.encode())>64:return None
    return {"inline_keyboard":[[
        {"text":"✅ 주문 확인","callback_data":confirm},
        {"text":"📋 주문 상세","callback_data":detail},
    ],[{"text":"❌ 주문 취소","callback_data":cancel}]]}


def callback_command(update,cfg):
    """Bind a compact callback token to the exact pending-order bot message."""
    query=update.get("callback_query")
    if type(query) is not dict:
        return None
    actor=query.get("from",{})
    message=query.get("message",{})
    if type(actor) is not dict or type(message) is not dict:
        return None
    chat=message.get("chat",{})
    bot=message.get("from",{})
    if (type(actor) is not dict or type(message) is not dict or type(chat) is not dict
        or type(bot) is not dict or chat.get("type")!="private"
        or chat.get("id")!=cfg["operator_chat_id"]
        or actor.get("id") not in cfg["operator_user_ids"] or actor.get("is_bot") is not False
        or bot.get("is_bot") is not True or bot.get("username")!=cfg["bot_username"]):
        return None
    if type(query.get("id")) is not str or type(query.get("data")) is not str:
        return None
    menu_commands={"orders":"주문목록 메뉴","order_help":"주문조회 도움말",
                   "products":"/products","stock":"재고관리",
                   "product_help":"상품 등록"}
    menu=re.fullmatch(r"aicc:menu:([a-z_]+)",query["data"])
    if menu is not None:
        if menu[1] not in menu_commands or type(message.get("text")) is not str or "[DEV] 관리자 메뉴" not in message["text"]:
            return None
        return query["id"],actor["id"],menu_commands[menu[1]]
    if type(message.get("text")) is not str:return None
    data=query["data"]
    message_text=_operator_body(message.get("text",""))
    if data=="aicc:orders:filters" and message_text=="주문 목록 보기를 선택해 주세요.":
        return query["id"],actor["id"],"주문목록 상태 메뉴"
    if data=="aicc:orders:back" and message_text=="조회할 주문 상태를 선택해 주세요.":
        return query["id"],actor["id"],"주문목록 메뉴"
    if data=="aicc:orders:all:0" and message_text=="주문 목록 보기를 선택해 주세요.":
        return query["id"],actor["id"],"주문목록 전체 ALL 0"
    status=re.fullmatch(r"aicc:orders:status:([A-Z_]+):([0-9]{1,6})",data)
    if status and message_text in ("주문 목록 보기를 선택해 주세요.","조회할 주문 상태를 선택해 주세요.") and status[1] in _FILTER_STATES:
        return query["id"],actor["id"],"주문목록 상태 "+status[1]+" "+status[2]
    next_page=re.fullmatch(r"aicc:orders:next:(ALL|[A-Z_]+):([1-9][0-9]{0,5})",data)
    nav=_ORDER_NAV.fullmatch(message_text)
    if next_page and nav and int(next_page[2])==int(nav[3])+1:
        scope=next_page[1]
        if scope=="ALL" and nav[1]=="ALL":return query["id"],actor["id"],"주문목록 전체 ALL "+next_page[2]
        if scope==nav[2] and nav[1]=="STATUS":return query["id"],actor["id"],"주문목록 상태 "+scope+" "+next_page[2]
        return None
    item=re.fullmatch(r"aicc:item:(detail|confirm|cancel|payment|ship|delivered):([0-9]{10})",data)
    if item is not None:
        source=next((m for m in _ORDER_LIST_LINE.finditer(message["text"]) if m[1]==item[2]),None)
        if source is None:return None
        number,phone,state=(v.strip() for v in source.groups())
        if item[1]=="confirm" and state!="확인대기":return None
        if item[1]=="cancel" and state not in _LIST_CANCEL_STATES:return None
        if item[1]=="payment" and state!="입금대기":return None
        if item[1]=="ship" and state!="배송준비":return None
        if item[1]=="delivered" and state!="배송중":return None
        action={"detail":"주문상세","confirm":"주문확인","cancel":"주문 취소","payment":"입금 확인","ship":"배송","delivered":"배송 완료"}[item[1]]
        return query["id"],actor["id"],phone+" 고객 "+action+" #"+number
    match=re.fullmatch(r"aicc:(confirm|detail|cancel):([0-9]{10})",query["data"])
    if match is None:
        return None
    source=_ORDER_LINE.search(message["text"])
    if source is None:
        return None
    phone,number=source.groups()
    if number!=match[2]:
        return None
    action={"confirm":"주문확인","detail":"주문상세","cancel":"주문 취소"}[match[1]]
    return query.get("id"),actor["id"],phone+" 고객 "+action+" #"+number


def _callback_label(data):
    menu_labels={"orders":"📦 주문 목록","order_help":"🔎 주문 조회 안내","products":"🛍 상품 목록",
                 "stock":"📊 재고 확인","product_help":"➕ 상품 등록 안내"}
    menu=re.fullmatch(r"aicc:menu:([a-z_]+)",data or "")
    if menu:return menu_labels.get(menu[1],"메뉴")
    if data=="aicc:orders:filters":return "🏷 상태별 보기"
    if data=="aicc:orders:back":return "⬅️ 상태 선택으로 돌아가기"
    if re.fullmatch(r"aicc:orders:all:[0-9]{1,6}",data or ""):return "📋 전체 보기"
    status=re.fullmatch(r"aicc:orders:status:([A-Z_]+):[0-9]{1,6}",data or "")
    if status:return "🏷 "+_FILTER_STATES.get(status[1],status[1])
    if re.fullmatch(r"aicc:orders:next:(?:ALL|[A-Z_]+):[0-9]{1,6}",data or ""):return "➡️ 다음 주문 보기"
    item=re.fullmatch(r"aicc:item:(detail|confirm|cancel|payment|ship|delivered):([0-9]{10})",data or "")
    legacy=re.fullmatch(r"aicc:(confirm|detail|cancel):([0-9]{10})",data or "")
    match=item or legacy
    if match:
        action=match[1];number=match[2]
        labels={"detail":"📋 상세 보기","confirm":"✅ 주문 확인","cancel":"❌ 주문 취소",
                "payment":"💳 입금 확인","ship":"🚚 배송 등록","delivered":"📦 배송 완료"}
        return labels[action]+" · 주문 #"+number
    return "선택한 작업"


def _send_reply(transport,text,*,context=None):
    if type(text) is str:
        page=_ORDER_PAGE.search(text)
        body=_ORDER_PAGE.sub("",text,count=1).strip() if page else text.strip()
        matches=list(_ORDER_LIST_LINE.finditer(body))
        if matches:
            last_sent=None
            def send_card(value,markup=None):
                nonlocal last_sent
                if last_sent is not None:
                    delay=1.05-(time.monotonic()-last_sent)
                    if delay>0:time.sleep(delay)
                result=transport.send_message(value,reply_markup=markup) if markup else transport.send_message(value)
                last_sent=time.monotonic()
                return result
            for index,match in enumerate(matches):
                end=matches[index+1].start() if index+1<len(matches) else len(body)
                card=body[match.start():end].strip()
                card=re.sub(r"\n{2,}","\n",card)
                if index==0 and context:card=context+"\n"+card
                send_card(card,reply_markup(card))
            if page and int(page[3])+1<int(page[4]):
                nav="주문 더 보기 · "+page[1]+":"+page[2]+":"+page[3]
                send_card(nav,reply_markup(nav))
            return True
    if context:text=context+"\n\n"+text
    markup=reply_markup(text)
    if markup is None:
        return transport.send_message(text)
    return transport.send_message(text,reply_markup=markup)


def poll_once(transport,client,cfg,path):
    with sqlite3.connect(path) as c:
        offset=c.execute('SELECT offset FROM cursor WHERE id=1').fetchone()[0]
    for item in sorted(transport.get_updates(offset),key=lambda x:x.get('update_id',-1)):
        i=item.get('update_id')
        if type(i) is not int or not 0<=i<2**50 or i<offset:
            continue
        query=item.get("callback_query")
        callback=callback_command(item,cfg)
        if type(query) is dict:
            if callback is not None:
                callback_id,user_id,text=callback
                try:
                    callback_data=query.get("data","")
                    status_text=_callback_label(callback_data)+" 선택 · 처리 중"
                    transport.answer_callback_query(callback_id,text=status_text)
                except Exception as error:
                    # Callback acknowledgement is cosmetic; a transport failure must not skip the command.
                    LOGGER.warning("callback_ack_failed error_type=%s",type(error).__name__)
                try:
                    reply=client(text,i+(1<<60),'telegram-user-'+str(user_id))
                except Exception as error:
                    # Do not retry a possibly ambiguous order mutation. Log type only, never message/PII.
                    LOGGER.warning("callback_command_failed error_type=%s",type(error).__name__)
                    try:
                        _send_reply(transport,'처리 결과 확인이 필요합니다. 같은 버튼을 다시 누르지 말고 주문상세로 현재 상태를 확인해 주세요.',context="🔘 선택한 버튼: "+_callback_label(query.get("data","")))
                    except Exception as send_error:
                        LOGGER.warning("callback_error_reply_failed error_type=%s",type(send_error).__name__)
                else:
                    try:
                        _send_reply(transport,reply,context="🔘 선택한 버튼: "+_callback_label(query.get("data","")))
                    except Exception as error:
                        # The command may have completed; never call it again after delivery fails.
                        LOGGER.warning("callback_result_delivery_failed error_type=%s",type(error).__name__)
            else:
                # Stop the spinner only for a trusted operator in this private chat.
                actor=query.get("from",{})
                if (type(actor) is dict and actor.get("id") in cfg["operator_user_ids"]
                    and actor.get("is_bot") is False and type(query.get("id")) is str):
                    try:transport.answer_callback_query(query["id"],text="이 주문에 사용할 수 없는 버튼입니다.")
                    except Exception:pass
        else:
            msg=item.get('message',{});chat=msg.get('chat',{});user=msg.get('from',{})
            if (chat.get('id')==cfg['operator_chat_id'] and chat.get('type')=='private'
                and user.get('id') in cfg['operator_user_ids'] and user.get('is_bot') is False
                and type(msg.get('text')) is str):
                text=msg['text']
                try:
                    if text.strip().lower() in ('/start','/help','/menu','메뉴','menu'):
                        reply='안녕하세요 agachichi 입니다\n[DEV] 관리자 메뉴\n주문·상품 관리 작업을 선택하세요.'
                    else:
                        # Separate bot IDs must never collide with historical shared-bot updates.
                        reply=client(text,i+(1<<60),'telegram-user-'+str(user['id']))
                    _send_reply(transport,reply)
                except Exception:
                    # Never replay an ambiguous mutation; tell the operator to inspect status.
                    reply=('안녕하세요 agachichi 입니다\n[개발]\n'
                           '처리 결과 확인이 필요합니다. 같은 변경을 재전송하지 말고 '
                           '주문상세 또는 주문상태로 현재 상태를 확인해 주세요.')
                    try:
                        _send_reply(transport,reply)
                    except Exception:
                        pass
        with sqlite3.connect(path) as c:
            c.execute('UPDATE cursor SET offset=? WHERE id=1',(i+1,))
        offset=i+1


def main():
    cfg=json.loads((PRIVATE/'telegram-papachichi.private.json').read_text())
    if cfg.get('enabled') is not True or cfg.get('environment')!='DEV' or cfg.get('bot_username')!='papachichi_bot':
        raise ValueError('DEV_BOT_CONFIGURATION')
    transport=OrderTelegramTransport(token=SecretStr(cfg['bot_token']),chat_id=cfg['operator_chat_id'])
    bridge=json.loads((PRIVATE/'operator-bridge.private.json').read_text())
    client=compose_dev_command_client(bridge,chat_id=cfg['operator_chat_id'],user_ids=frozenset(cfg['operator_user_ids']))
    path=DATA/'papachichi-cursor.sqlite3'
    with sqlite3.connect(path) as c:
        c.execute('CREATE TABLE IF NOT EXISTS cursor(id INTEGER PRIMARY KEY,offset INTEGER NOT NULL)')
        c.execute('INSERT OR IGNORE INTO cursor VALUES(1,0)')
    path.chmod(0o600)
    with (DATA/'papachichi-poller.lock').open('a') as lease:
        fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
        while True:
            try:poll_once(transport,client,cfg,path)
            except Exception as error:
                LOGGER.warning("poller_cycle_failed error_type=%s",type(error).__name__)
            time.sleep(2)

if __name__=='__main__':
    main()

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
_LIST_CANCEL_STATES={"확인대기","확인완료","입금대기"}


def menu_markup():
    return {"inline_keyboard":[
        [{"text":"📦 주문 목록","callback_data":"aicc:menu:orders"},
         {"text":"🔎 주문 조회 안내","callback_data":"aicc:menu:order_help"}],
        [{"text":"🛍 상품 목록","callback_data":"aicc:menu:products"},
         {"text":"📊 재고 확인","callback_data":"aicc:menu:stock"}],
        [{"text":"➕ 상품 등록 안내","callback_data":"aicc:menu:product_help"}],
    ]}


def reply_markup(text):
    """Offer order-scoped admin actions, including buttons on each order-list row."""
    if type(text) is str and "[DEV] 관리자 메뉴" in text:
        return menu_markup()
    if type(text) is not str:
        return None
    list_rows=list(_ORDER_LIST_LINE.finditer(text))
    if list_rows:
        keyboard=[]
        for index,match in enumerate(list_rows):
            if index>=30:
                break
            number,phone,state=(v.strip() for v in match.groups())
            row=[{"text":"📋 "+number+" 상세","callback_data":"aicc:item:detail:"+number}]
            if state=="확인대기":
                row.append({"text":"✅ 주문 확인","callback_data":"aicc:item:confirm:"+number})
            if state in _LIST_CANCEL_STATES:
                row.append({"text":"❌ 주문 취소","callback_data":"aicc:item:cancel:"+number})
            keyboard.append(row)
        return {"inline_keyboard":keyboard} if keyboard else None
    match=_ORDER_LINE.search(text)
    if match is None:
        return None
    phone,number=match.groups()
    confirm=f"aicc:confirm:{number}"
    detail=f"aicc:detail:{number}"
    cancel=f"aicc:cancel:{number}"
    if max(len(v.encode()) for v in (confirm,detail,cancel))>64:
        return None
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
    menu_commands={"orders":"주문목록","order_help":"주문조회 도움말",
                   "products":"/products","stock":"재고관리",
                   "product_help":"상품관리 도움말"}
    menu=re.fullmatch(r"aicc:menu:([a-z_]+)",query["data"])
    if menu is not None:
        if menu[1] not in menu_commands or type(message.get("text")) is not str or "[DEV] 관리자 메뉴" not in message["text"]:
            return None
        return query["id"],actor["id"],menu_commands[menu[1]]
    if type(message.get("text")) is not str:
        return None
    item=re.fullmatch(r"aicc:item:(detail|confirm|cancel):([0-9]{10})",query["data"])
    if item is not None:
        source=next((m for m in _ORDER_LIST_LINE.finditer(message["text"]) if m[1]==item[2]),None)
        if source is None:return None
        number,phone,state=(v.strip() for v in source.groups())
        if item[1]=="confirm" and state!="확인대기":return None
        if item[1]=="cancel" and state not in _LIST_CANCEL_STATES:return None
        action={"detail":"주문상세","confirm":"주문확인","cancel":"주문 취소"}[item[1]]
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


def _send_reply(transport,text):
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
                    status_text="요청을 처리하고 있습니다." if callback_data.startswith("aicc:menu:") else ("주문을 취소하고 있습니다." if ":cancel:" in callback_data else "주문을 확인하고 있습니다.")
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
                        _send_reply(transport,'처리 결과 확인이 필요합니다. 같은 버튼을 다시 누르지 말고 주문상세로 현재 상태를 확인해 주세요.')
                    except Exception as send_error:
                        LOGGER.warning("callback_error_reply_failed error_type=%s",type(send_error).__name__)
                else:
                    try:
                        _send_reply(transport,reply)
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

"""DEV-only bot consumer; private bridge, independent cursor, no PROD handler."""
import fcntl,json,re,sqlite3,time
from pathlib import Path
from pydantic import SecretStr
from core.shopping.order_core.telegram import OrderTelegramTransport
from ops.macos.shopping.dev_operator_bridge_client import compose_dev_command_client

PRIVATE=Path('/Users/kyouhan/.config/aicontrolcenter-dev-order')
DATA=Path('/Users/kyouhan/AIControlCenterRuntime/dev-order/data')
_ORDER_LINE=re.compile(r"(?m)^([0-9]{11}) 고객님 주문\n주문 ([0-9]{10}) ·")


def reply_markup(text):
    """Offer order actions only on an explicit, single pending-order result."""
    match=_ORDER_LINE.search(text) if type(text) is str else None
    if match is None:
        return None
    phone,number=match.groups()
    confirm=f"aicc:confirm:{number}"
    detail=f"aicc:detail:{number}"
    if max(len(confirm.encode()),len(detail.encode()))>64:
        return None
    return {"inline_keyboard":[[
        {"text":"✅ 주문 확인","callback_data":confirm},
        {"text":"📋 주문 상세","callback_data":detail},
    ]]}


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
    match=re.fullmatch(r"aicc:(confirm|detail):([0-9]{10})",query["data"])
    if match is None or type(message.get("text")) is not str:
        return None
    source=_ORDER_LINE.search(message["text"])
    if source is None:
        return None
    phone,number=source.groups()
    if number!=match[2]:
        return None
    action="주문확인" if match[1]=="confirm" else "주문상세"
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
                    transport.answer_callback_query(callback_id,text="주문을 확인하고 있습니다.")
                    reply=client(text,i+(1<<60),'telegram-user-'+str(user_id))
                    _send_reply(transport,reply)
                except Exception:
                    try:
                        _send_reply(transport,'처리 결과 확인이 필요합니다. 같은 버튼을 다시 누르지 말고 주문상세로 현재 상태를 확인해 주세요.')
                    except Exception:
                        pass
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
                    if text in ('/start','/help'):
                        reply='안녕하세요 agachichi 입니다\n[개발]\n개발 전용 봇입니다. 주문목록, 상품목록, 할일을 물어보세요.'
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
            except Exception:pass
            time.sleep(2)

if __name__=='__main__':
    main()

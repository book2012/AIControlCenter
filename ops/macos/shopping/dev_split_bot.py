"""DEV-only bot consumer; private bridge, independent cursor, no PROD handler."""
import fcntl,json,sqlite3,time
from pathlib import Path
from pydantic import SecretStr
from core.shopping.order_core.telegram import OrderTelegramTransport
from ops.macos.shopping.dev_operator_bridge_client import compose_dev_command_client
PRIVATE=Path('/Users/kyouhan/.config/aicontrolcenter-dev-order')
DATA=Path('/Users/kyouhan/AIControlCenterRuntime/dev-order/data')
def poll_once(transport,client,cfg,path):
    with sqlite3.connect(path) as c:offset=c.execute('SELECT offset FROM cursor WHERE id=1').fetchone()[0]
    for item in sorted(transport.get_updates(offset),key=lambda x:x.get('update_id',-1)):
        i=item.get('update_id');msg=item.get('message',{});chat=msg.get('chat',{});user=msg.get('from',{})
        if type(i) is not int or not 0<=i<2**50 or i<offset:continue
        if (chat.get('id')==cfg['operator_chat_id'] and chat.get('type')=='private'
            and user.get('id') in cfg['operator_user_ids'] and user.get('is_bot') is False and type(msg.get('text')) is str):
            text=msg['text']
            try:
                if text in ('/start','/help'):
                    reply='안녕하세요 agachichi 입니다\n[개발]\n개발 전용 봇입니다. 주문목록, 상품목록, 할일을 물어보세요.'
                else:
                    # Separate bot IDs must never collide with historical shared-bot updates.
                    reply=client(text,i+(1<<60),'telegram-user-'+str(user['id']))
                transport.send_message(reply)
            except Exception:pass # No replay of an ambiguous mutation or delivery.
        with sqlite3.connect(path) as c:c.execute('UPDATE cursor SET offset=? WHERE id=1',(i+1,))
        offset=i+1

def main():
    cfg=json.loads((PRIVATE/'telegram-papachichi.private.json').read_text())
    if cfg.get('enabled') is not True or cfg.get('environment')!='DEV' or cfg.get('bot_username')!='papachichi_bot':raise ValueError('DEV_BOT_CONFIGURATION')
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
if __name__=='__main__':main()

"""Independent bot IDs cannot be suppressed by the historical shared-bot cursor."""
import os,time,socket
_ORIGINAL_CONNECT=socket.socket.connect
from types import SimpleNamespace
from test_shop_order_001d_telegram import api,clients,composed,deny_network,complete,REFERENCE,CHAT,OPERATOR
from core.shopping.operator_bridge import BridgeCodec,call_dev_bridge
from ops.macos.shopping.dev_operator_bridge import compose_dev_bridge

def test_bridge_read_does_not_advance_shared_cursor_and_decision_is_once(api,composed,tmp_path,monkeypatch):
    def unix_only(sock,address):
        assert sock.family==socket.AF_UNIX and address==str(tmp_path/"operator-dev.sock")
        return _ORIGINAL_CONNECT(sock,address)
    monkeypatch.setattr(socket.socket,"connect",unix_only)
    complete(api,composed);app,ledger,_=composed;guards=[]
    ledger.process_operator_update((1<<60)+10**12)
    before=ledger.telegram_offset();os.chmod(tmp_path,0o700)
    adapter=SimpleNamespace(resolve=lambda text,update_id,actor=None:(None,None,'조회완료' if text=='주문목록' else None))
    tg=SimpleNamespace(_ledger=ledger,_chat=CHAT,_users=frozenset({OPERATOR}),_confirmation_guard=lambda *a:guards.append(1) or True)
    cfg={'enabled':True,'environment':'DEV','hmac_key_hex':'11'*32};products=SimpleNamespace(command=lambda *_:None)
    codec=BridgeCodec(bytes.fromhex(cfg['hmac_key_hex']))
    def request(text,i):return codec.sign({'environment':'DEV','update_id':i,'chat_id':CHAT,'user_id':OPERATOR,'is_bot':False,'text':text,'timestamp':int(time.time()),'nonce':format(i%(1<<128),'032x')})
    server=compose_dev_bridge(cfg=cfg,data=tmp_path,telegram=tg,adapter=adapter,products=products);server.start()
    command=request('/order_confirm '+REFERENCE,(1<<60)+2)
    try:
        assert '조회완료' in call_dev_bridge(server.path,request('주문목록',(1<<60)+1),codec)
        assert ledger.telegram_offset()==before
        first=call_dev_bridge(server.path,command,codec)
        assert '확인완료' in first and guards==[1]
        assert ledger.telegram_offset()==before+1
        assert call_dev_bridge(server.path,command,codec)==first and guards==[1]
    finally:server.close()
    server=compose_dev_bridge(cfg=cfg,data=tmp_path,telegram=tg,adapter=adapter,products=products);server.start()
    try:
        assert call_dev_bridge(server.path,command,codec)==first
        assert guards==[1] and ledger.telegram_offset()==before+1
    finally:server.close()

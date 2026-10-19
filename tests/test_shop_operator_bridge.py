"""Private ingress checks with fake handlers and disposable Unix sockets; no Telegram network."""
from concurrent.futures import ThreadPoolExecutor
import io
import os
from types import SimpleNamespace
import pytest
from core.shopping.operator_bridge import (
    BridgeCodec, BridgeDenied, DevOperatorBridge, PrivateBridgeServer, call_dev_bridge, read_frame)
from ops.macos.shopping.dev_operator_bridge import compose_dev_bridge

KEY = b"k"*32
CHAT = 123
USER = 456

def envelope(codec, **changes):
    body = dict(environment="DEV", update_id=10, chat_id=CHAT, user_id=USER,
        is_bot=False, text="주문목록", timestamp=1000, nonce="a"*32)
    body.update(changes)
    return codec.sign(body)

def bridge(tmp_path, handler):
    return DevOperatorBridge(database_path=tmp_path/"bridge.sqlite3", key=KEY,
        chat_id=CHAT, user_ids=frozenset({USER}), handler=handler, clock=lambda:1000)

def test_restart_replay_and_concurrency_preserve_one_bound_execution(tmp_path):
    calls = []
    def handle(*args):
        calls.append(args)
        return "주문 확인"
    service = bridge(tmp_path, handle)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(service.process, [envelope(service.codec)]*2))
    assert len(calls) == 1 and calls[0] == ("주문목록", 10, "telegram-user-456")
    assert service.codec.verify(results[0])["reply"].startswith("안녕하세요 agachichi 입니다\n[개발]")
    resumed = bridge(tmp_path, handle)
    resumed.process(envelope(resumed.codec, nonce="b"*32))
    assert len(calls) == 1
    with pytest.raises(ValueError, match="UPDATE_CONFLICT"):
        resumed.process(envelope(resumed.codec, text="주문취소 #15"))
    assert len(calls) == 1

@pytest.mark.parametrize("changes", [
    {"environment":"PROD"}, {"text":"운영 주문목록"}, {"text":"PROD: 주문목록"},
    {"chat_id":999}, {"user_id":999}, {"user_id":True}, {"is_bot":True},
    {"timestamp":939}, {"timestamp":1061}, {"update_id":True}, {"update_id":-1},
    {"update_id":2**63-1}, {"nonce":"bad"}, {"text":""}, {"text":"x"*4097}])
def test_invalid_requests_never_reach_handler(tmp_path, changes):
    calls = []
    service = bridge(tmp_path, lambda *a: calls.append(a))
    with pytest.raises(ValueError):
        service.process(envelope(service.codec, **changes))
    assert calls == []

def test_bad_signature_and_frame_rejected(tmp_path):
    service = bridge(tmp_path, lambda *_: pytest.fail("not authorized"))
    message = envelope(service.codec)
    message["body"]["user_id"] = 999
    with pytest.raises(BridgeDenied, match="AUTH"):
        service.process(message)
    for data in [b"{}", b"x"*20000+b"\n"]:
        with pytest.raises(BridgeDenied):
            read_frame(io.BytesIO(data))

def test_unknown_handler_outcome_is_never_redispatched(tmp_path):
    calls = []
    def unknown(*args):
        calls.append(args)
        raise TimeoutError("provider receipt unknown")
    service = bridge(tmp_path, unknown)
    with pytest.raises(TimeoutError):
        service.process(envelope(service.codec))
    restarted = bridge(tmp_path, unknown)
    with pytest.raises(ValueError, match="INSPECTION"):
        restarted.process(envelope(restarted.codec))
    assert len(calls) == 1

def test_socket_roundtrip_permissions_and_private_directory(tmp_path):
    os.chmod(tmp_path, 0o700)
    service = bridge(tmp_path, lambda *_: "완료")
    server = PrivateBridgeServer(tmp_path/"dev.sock", service)
    server.start()
    try:
        assert server.path.stat().st_mode & 0o777 == 0o600
        assert "완료" in call_dev_bridge(server.path, envelope(service.codec), service.codec)
        with pytest.raises(BridgeDenied, match="EXISTS"):
            PrivateBridgeServer(server.path, service)
    finally:
        server.close()
    assert not server.path.exists()
    os.chmod(tmp_path, 0o755)
    with pytest.raises(BridgeDenied, match="DIRECTORY"):
        PrivateBridgeServer(tmp_path/"dev.sock", service)

def test_disabled_composition_does_not_create_socket_or_database(tmp_path):
    assert compose_dev_bridge(cfg={"enabled":False}, data=tmp_path,
        telegram=None, adapter=None, products=None) is None
    assert list(tmp_path.iterdir()) == []

def test_adapter_actor_confirmation_guard_and_no_transport_calls(tmp_path):
    os.chmod(tmp_path, 0o700)
    calls = []
    ledger = SimpleNamespace(process_operator_update=lambda *a, **kw: calls.append((a,kw)))
    telegram = SimpleNamespace(_ledger=ledger, _chat=CHAT, _users=frozenset({USER}),
        _confirmation_guard="guard")
    adapter = SimpleNamespace(resolve=lambda text, update_id,actor=None:("f"*24,"CONFIRMED",None))
    products = SimpleNamespace(command=lambda *_:pytest.fail("should not route product"))
    server = compose_dev_bridge(cfg={"enabled":True, "environment":"DEV", "hmac_key_hex":KEY.hex()},
        data=tmp_path, telegram=telegram, adapter=adapter, products=products)
    server.start()
    try:
        codec = BridgeCodec(KEY)
        import time
        reply = call_dev_bridge(server.path, envelope(codec, timestamp=int(time.time())), codec)
        assert "주문 상태" in reply
        assert calls == [((10,), dict(reference="f"*24, decision="CONFIRMED",
            actor_reference="telegram-user-456", confirmation_guard="guard"))]
    finally:
        server.close()

def test_forwarding_client_binds_actor_and_never_retries_on_timeout():
    from ops.macos.shopping.dev_operator_bridge_client import compose_dev_command_client, DEV_SOCKET
    calls = []
    def timed_out(path, message, codec):
        calls.append((path, codec.request(message)))
        raise TimeoutError("unknown")
    client = compose_dev_command_client({"enabled":True,"environment":"DEV","hmac_key_hex":KEY.hex()},
        chat_id=CHAT, user_ids=frozenset({USER}), call=timed_out, clock=__import__("time").time)
    with pytest.raises(ValueError, match="AUTHORIZED"):
        client("주문목록", 10, "telegram-user-999")
    assert calls == []
    with pytest.raises(TimeoutError):
        client("주문목록", 10, "telegram-user-456")
    assert len(calls) == 1 and calls[0][0] == DEV_SOCKET
    assert calls[0][1]["environment"] == "DEV" and calls[0][1]["user_id"] == USER

def test_mismatched_authenticated_reply_does_not_pass_client(tmp_path):
    from core.shopping.operator_bridge import canonical
    import socketserver, threading
    codec = BridgeCodec(KEY)
    calls = []
    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            calls.append(read_frame(self.rfile))
            self.wfile.write(canonical(codec.sign(dict(environment="DEV",nonce="b"*32,
                update_id=10,reply="wrong binding")))+b"\n")
    server = socketserver.UnixStreamServer(str(tmp_path/"wrong.sock"),Handler)
    thread = threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with pytest.raises(BridgeDenied,match="RECEIPT"):
            call_dev_bridge(tmp_path/"wrong.sock",envelope(codec),codec)
        assert len(calls) == 1
    finally:
        server.shutdown();thread.join();server.server_close()


def test_shared_router_does_not_repeat_authenticated_dev_header(tmp_path):
    from core.shopping.operator_environment import DurableOperatorEnvironmentRouter,OperatorEnvironmentRouter
    service=bridge(tmp_path,lambda *_:"전체 주문 8건")
    outer=DurableOperatorEnvironmentRouter(database_path=tmp_path/"outer.sqlite3",
        dev=lambda text,i:service.codec.verify(service.process(envelope(service.codec,text=text,update_id=i)))["reply"],
        prod=lambda *_:"운영 목록",default="PROD",chat_id=CHAT,user_ids=frozenset({USER}))
    reply=outer.dispatch("개발 주문목록",chat_id=CHAT,user_id=USER,update_id=10)
    assert reply=="안녕하세요 agachichi 입니다\n[개발]\n전체 주문 8건"
    assert outer.dispatch("개발 주문목록",chat_id=CHAT,user_id=USER,update_id=10)==reply
    plain=OperatorEnvironmentRouter(dev=lambda _:reply,prod=lambda _:"운영 목록",
        default="PROD",chat_id=CHAT,user_ids=frozenset({USER}))
    assert plain.dispatch("개발 주문목록",chat_id=CHAT,user_id=USER)==reply
    assert plain.dispatch("운영 주문목록",chat_id=CHAT,user_id=USER)=="안녕하세요 agachichi 입니다\n[운영]\n운영 목록"

def test_environment_conversation_scopes_plain_followups_and_expiry(tmp_path,monkeypatch):
    from core.shopping.operator_environment import DurableOperatorEnvironmentRouter
    import time
    now=[1000]
    monkeypatch.setattr(time,"time",lambda:now[0])
    calls=[]
    router=DurableOperatorEnvironmentRouter(database_path=tmp_path/"scope.sqlite3",
        dev=lambda t,i:(calls.append(("DEV",t,i)) or "개발 결과"),
        prod=lambda t,i:(calls.append(("PROD",t,i)) or "운영 결과"),
        default="PROD",chat_id=CHAT,user_ids=frozenset({USER,999}),conversation_seconds=1800)
    router.dispatch("개발 입금 확인",chat_id=CHAT,user_id=USER,update_id=1)
    assert "[개발]" in router.dispatch("응",chat_id=CHAT,user_id=USER,update_id=2)
    assert calls[-1]==("DEV","응",2)
    assert "[운영]" in router.dispatch("주문목록",chat_id=CHAT,user_id=999,update_id=3)
    now[0]+=1801
    assert "대화 시간이 지났" in router.dispatch("입금확인 #15",chat_id=CHAT,user_id=USER,update_id=4)
    assert len(calls)==3
    router.dispatch("운영 주문목록",chat_id=CHAT,user_id=USER,update_id=5)
    assert "[운영]" in router.dispatch("주문목록",chat_id=CHAT,user_id=USER,update_id=6)

def test_authenticated_bridge_dialogue_asks_before_payment_and_scopes_actor(tmp_path,monkeypatch):
    import time
    from types import SimpleNamespace
    import core.shopping.operator_intent as intent_module
    os.chmod(tmp_path,0o700)
    monkeypatch.setattr(intent_module,"LocalOperatorJudge",lambda:lambda text,ctx:{"action":"DEPOSIT_CONFIRM","order_id":15})
    payments=[]
    adapter=SimpleNamespace(admin_orders=lambda limit:[dict(order_id=15,phone="01012345678",display_state="AWAITING_DEPOSIT")],
        resolve=lambda text,update_id,actor=None:(payments.append(text) or (None,None,"입금완료")),aftersales=None)
    products=SimpleNamespace(records=[],command=lambda *_:None)
    telegram=SimpleNamespace(_ledger=SimpleNamespace(process_operator_update=lambda *a,**kw:dict(outcome="IGNORED")),
        _chat=CHAT,_users=frozenset({USER}),_confirmation_guard=None)
    server=compose_dev_bridge(cfg={"enabled":True,"environment":"DEV","hmac_key_hex":KEY.hex()},
        data=tmp_path,telegram=telegram,adapter=adapter,products=products,
        conversation_cfg={"enabled":True,"environment":"DEV","model":"qwen3:4b"})
    server.start()
    try:
        codec=BridgeCodec(KEY)
        request=envelope(codec,text="15번 입금했어",update_id=1,timestamp=int(time.time()))
        assert "처리할까요" in call_dev_bridge(server.path,request,codec)
        assert payments==[]
        request=envelope(codec,text="응",update_id=2,timestamp=int(time.time()))
        assert "입금완료" in call_dev_bridge(server.path,request,codec)
        assert payments==["입금확인 #15"]
        call_dev_bridge(server.path,request,codec)
        assert payments==["입금확인 #15"]
    finally:server.close()



def test_phone_bound_order_button_commands_bypass_conversation(tmp_path, monkeypatch):
    os.chmod(tmp_path, 0o700)
    from core.shopping import operator_conversation, operator_intent
    monkeypatch.setattr(operator_intent, "LocalOperatorJudge", lambda **_: object())
    conversation_calls = []
    class FakeConversation:
        def __init__(self, **_): pass
        def handle(self, text, update_id, actor):
            conversation_calls.append((text, update_id, actor))
            return "대화 처리"
    monkeypatch.setattr(operator_conversation, "OperatorConversation", FakeConversation)

    adapter_calls = []
    adapter = SimpleNamespace(
        resolve=lambda text, update_id, actor=None: (
            adapter_calls.append((text, update_id, actor)) or ("f" * 24, "CONFIRMED", None)
        ),
        admin_orders=lambda _limit: [],
    )
    ledger_calls = []
    telegram = SimpleNamespace(
        _ledger=SimpleNamespace(process_operator_update=lambda *a, **kw: (
            ledger_calls.append((a, kw)) or {"outcome": "CONFIRMED"}
        )),
        _chat=CHAT, _users=frozenset({USER}), _confirmation_guard="guard",
    )
    products = SimpleNamespace(records=[], command=lambda *_: None)
    server = compose_dev_bridge(
        cfg={"enabled": True, "environment": "DEV", "hmac_key_hex": KEY.hex()},
        data=tmp_path, telegram=telegram, adapter=adapter, products=products,
        conversation_cfg={"enabled": True, "environment": "DEV", "model": "qwen3:4b"},
    )
    server.start()
    try:
        import time
        codec = BridgeCodec(KEY)
        button_command = "01092838321 고객 주문확인 #2610192105"
        reply = call_dev_bridge(server.path, envelope(codec, text=button_command,
            timestamp=int(time.time())), codec)
        assert "주문 상태: 확인완료" in reply
        assert adapter_calls == [(button_command, 10, "telegram-user-456")]
        assert ledger_calls and ledger_calls[0][1]["decision"] == "CONFIRMED"
        assert conversation_calls == []

        natural = "15번 입금했어"
        reply = call_dev_bridge(server.path, envelope(codec, text=natural, update_id=11,
            timestamp=int(time.time()), nonce="b" * 32), codec)
        assert reply.endswith("대화 처리")
        assert conversation_calls == [(natural, 11, "telegram-user-456")]
    finally:
        server.close()

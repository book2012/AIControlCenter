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
    adapter = SimpleNamespace(resolve=lambda text, update_id:("f"*24,"CONFIRMED",None))
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

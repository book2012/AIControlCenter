import json
import sqlite3
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from core.shopping.customer_persistence import initialize_schema
from ops.macos.shopping.dev_guest_phone import DevPhoneBridge, PhoneDenied, ref
from ops.macos.shopping.dev_sens_sms import SensSMS, SensUnknown
from ops.macos.shopping.dev_sens_phone import FixedDevSensPort, SOURCE


def sens_config():
    return {
        "environment": "DEV", "provider": "NCP_SENS", "enabled": True,
        "service_id": "ncp:sms:kr:123456789:sens", "sender_number": "0212345678",
        "credentials": {"access_key": "TEST_ACCESS", "secret_key": "TEST_SECRET"},
    }


class Response:
    def __init__(self, status, document):
        self.status_code = status
        self.content = json.dumps(document).encode()
        self.document = document

    def json(self):
        return self.document


class Session:
    trust_env = True

    def __init__(self):
        self.calls = []
        self.response = Response(202, {"statusCode": "202", "statusName": "success",
                                       "requestId": "RSLA-1234567890123456-TEST"})

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.response


def test_sens_pins_endpoint_sender_recipient_and_hmac():
    session = Session()
    client = SensSMS(sens_config(), session=session, clock=lambda: 1000)
    receipt = client.send("+821012345678", "[agachichi] 인증번호 123456")
    method, url, kwargs = session.calls[0]
    assert method == "POST" and url == "https://sens.apigw.ntruss.com/sms/v2/services/ncp:sms:kr:123456789:sens/messages"
    assert session.trust_env is False and kwargs["allow_redirects"] is False and kwargs["timeout"] == 15
    assert kwargs["json"]["from"] == "0212345678" and kwargs["json"]["messages"] == [{"to": "01012345678"}]
    assert kwargs["json"]["type"] == "SMS" and receipt["state"] == "ACCEPTED"
    import base64, hashlib, hmac
    path = url.removeprefix("https://sens.apigw.ntruss.com")
    expected = base64.b64encode(hmac.new(
        b"TEST_SECRET", f"POST {path}\n1000000\nTEST_ACCESS".encode(), hashlib.sha256
    ).digest()).decode()
    assert kwargs["headers"]["x-ncp-apigw-signature-v2"] == expected


def test_sens_delivery_status_is_distinct_from_acceptance():
    session = Session()
    client = SensSMS(sens_config(), session=session, clock=lambda: 1000)
    text = "안녕하세요 agachichi 입니다"
    receipt = client.send("01012345678", text)
    session.response = Response(200, {"statusCode": "200", "statusName": "success",
        "messages": [{"requestId": receipt["request_id"], "to": receipt["to"],
                      "from": receipt["sender"], "content": text,
                      "status": "COMPLETED", "statusName": "fail", "statusCode": "3018"}]})
    assert client.status(receipt) == {"state": "FAILED", "status_code": "3018"}
    assert "requestId=" in session.calls[1][1]
    session.response.document["messages"][0]["to"] = "01099999999"
    with pytest.raises(SensUnknown):
        client.status(receipt)


def test_sens_otp_uses_existing_receipt_boundary_and_never_stores_plaintext(tmp_path, monkeypatch):
    from ops.macos.shopping import dev_sens_phone
    monkeypatch.setattr(dev_sens_phone.secrets, "randbelow", lambda _: 123456)
    sent = []
    monkeypatch.setattr(SensSMS, "send", lambda self, phone, text: sent.append((phone, text)) or
                        {"provider": "NCP_SENS", "state": "ACCEPTED"})
    phone_cfg = {"environment": "DEV", "provider": "sens_sms", "enabled": True,
                 "test_phone": "+821012345678", "guest_customer_id": ref("CUS"),
                 "guest_contact_ref": ref("CON")}
    path = tmp_path / "sens.private.json"
    path.write_text(json.dumps(sens_config()))
    path.chmod(0o600)
    customer = tmp_path / "customer.sqlite3"
    initialize_schema(customer)
    bridge = DevPhoneBridge(cfg=phone_cfg, binding_key=b"private-binding-key",
                            customer_path=customer, bridge_path=tmp_path / "bridge.sqlite3",
                            sens_config_path=path)
    assert isinstance(bridge.port, FixedDevSensPort)
    assert bridge.service._provider_source.value == SOURCE
    token, requested = bridge.start("01012345678")
    assert requested and sent == [("+821012345678", "[agachichi] 인증번호 123456 (5분 유효)")]
    db = (tmp_path / "sens-phone.sqlite3").read_bytes()
    assert b"123456" not in db and b"+821012345678" not in db
    receipt = bridge.verify(token, "123456")
    assert receipt.receipt.customer_id == phone_cfg["guest_customer_id"]
    with pytest.raises(PhoneDenied):
        bridge.verify(token, "123456")


def test_sens_unknown_send_is_not_retried(tmp_path, monkeypatch):
    calls = []
    def ambiguous(self, phone, text):
        calls.append(phone)
        raise TimeoutError()
    monkeypatch.setattr(SensSMS, "send", ambiguous)
    phone_cfg = {"environment": "DEV", "provider": "sens_sms", "enabled": True,
                 "test_phone": "+821012345678", "guest_customer_id": ref("CUS"),
                 "guest_contact_ref": ref("CON")}
    path = tmp_path / "sens.private.json"
    path.write_text(json.dumps(sens_config()))
    path.chmod(0o600)
    customer = tmp_path / "customer.sqlite3"
    initialize_schema(customer)
    bridge = DevPhoneBridge(cfg=phone_cfg, binding_key=b"private-binding-key",
                            customer_path=customer, bridge_path=tmp_path / "bridge.sqlite3",
                            sens_config_path=path)
    with pytest.raises(PhoneDenied):
        bridge.start("01012345678")
    with pytest.raises(PhoneDenied):
        bridge.start("01012345678")
    assert calls == ["+821012345678"]
    with sqlite3.connect(tmp_path / "sens-phone.sqlite3") as db:
        assert db.execute("SELECT state FROM sens_otp").fetchone()[0] == "UNKNOWN"


def test_order_notice_uses_same_sens_sender_and_reconciles(tmp_path, monkeypatch):
    from test_shop_customer_order_lookup import sms_fixture
    from test_shop_aftersales_dev import ORDER
    sms, store, rows = sms_fixture(tmp_path, lambda *_: None)
    private = tmp_path / "sens.private.json"
    private.write_text(json.dumps(sens_config()))
    private.chmod(0o600)
    sms.sens_config_path = private
    order_cfg = json.loads(sms.config_path.read_text())
    order_cfg["provider"] = "NCP_SENS"
    sms.config_path.write_text(json.dumps(order_cfg))
    sms.transport = lambda cfg, to, text: {
        "provider": "NCP_SENS", "request_id": "RSLA-1234567890123456-TEST",
        "to": "01012345678", "sender": sens_config()["sender_number"], "text_hash": "test",
        "state": "ACCEPTED",
    }
    with sqlite3.connect(sms.path) as db:
        db.execute("DELETE FROM notices WHERE order_id=?", (ORDER,))
    assert sms.config()["provider"] == "NCP_SENS"
    assert sms.dispatch_one() == "ACCEPTED"
    with sqlite3.connect(sms.path) as db:
        db.execute("UPDATE provider_receipts SET next_check=0")
    monkeypatch.setattr(SensSMS, "status", lambda self, receipt: {
        "state": "DELIVERED", "status_code": "0"})
    assert sms.dispatch_one() == "DELIVERED"
    assert sms.state(ORDER) == "DELIVERED"


def test_sens_order_cannot_send_with_fake_bank_or_implicit_activation(tmp_path):
    from test_shop_customer_order_lookup import sms_fixture
    sms, _, _ = sms_fixture(tmp_path, lambda *_: pytest.fail("must remain preview"))
    private = tmp_path / "sens.private.json"
    private.write_text(json.dumps(sens_config()))
    private.chmod(0o600)
    sms.sens_config_path = private
    assert sms.config().get("provider") != "NCP_SENS"
    config = json.loads(sms.config_path.read_text())
    config["provider"] = "NCP_SENS"
    config["bank"] = {"name": "가상 테스트은행", "account": "DEV-0000-0000",
                      "holder": "아가치치 DEV"}
    sms.config_path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match="REAL_BANK_REQUIRED"):
        sms.config()


def test_sens_wrong_otp_is_terminal(tmp_path, monkeypatch):
    from ops.macos.shopping import dev_sens_phone
    monkeypatch.setattr(dev_sens_phone.secrets, "randbelow", lambda _: 123456)
    monkeypatch.setattr(SensSMS, "send", lambda self, phone, text: {
        "provider": "NCP_SENS", "state": "ACCEPTED"})
    phone_cfg = {"environment": "DEV", "provider": "sens_sms", "enabled": True,
                 "test_phone": "+821012345678", "guest_customer_id": ref("CUS"),
                 "guest_contact_ref": ref("CON")}
    path = tmp_path / "sens.private.json"
    path.write_text(json.dumps(sens_config()))
    path.chmod(0o600)
    customer = tmp_path / "customer.sqlite3"
    initialize_schema(customer)
    bridge = DevPhoneBridge(cfg=phone_cfg, binding_key=b"private-binding-key",
                            customer_path=customer, bridge_path=tmp_path / "bridge.sqlite3",
                            sens_config_path=path)
    token, _ = bridge.start("01012345678")
    with pytest.raises(PhoneDenied):
        bridge.verify(token, "000000")
    with pytest.raises(PhoneDenied):
        bridge.verify(token, "123456")
    with sqlite3.connect(tmp_path / "sens-phone.sqlite3") as db:
        assert db.execute("SELECT state,attempts FROM sens_otp").fetchone() == ("FAILED", 1)

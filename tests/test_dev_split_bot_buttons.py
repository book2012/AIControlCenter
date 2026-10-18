import sqlite3
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from pydantic import SecretStr
from core.shopping.order_core.telegram import OrderTelegramTransport, TelegramDeliveryRejected
from ops.macos.shopping.dev_split_bot import callback_command, poll_once, reply_markup

CHAT = 771122
USER = 884433
PHONE = "01092838321"
NUMBER = "2610192105"
BOT = "papachichi_bot"
PENDING = (
    f"{PHONE} 고객님 주문\n"
    f"주문 {NUMBER} · 한경복\n"
    "주문일: 2026-10-19 08:45\n"
    "카멜 숄카라 벨티드 코트 / 카멜 / S / 1개\n"
    "229000.00 KRW"
)
CFG = {
    "operator_chat_id": CHAT,
    "operator_user_ids": [USER],
    "bot_username": BOT,
}


class FakeTransport:
    chat_id = CHAT

    def __init__(self, updates=()):
        self.updates = list(updates)
        self.messages = []
        self.answered = []

    def get_updates(self, offset):
        return self.updates

    def send_message(self, text, *, reply_markup=None):
        self.messages.append((text, reply_markup))

    def answer_callback_query(self, callback_id, *, text=None):
        self.answered.append((callback_id, text))


def cursor_db(path):
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE cursor(id INTEGER PRIMARY KEY, offset INTEGER NOT NULL)")
        connection.execute("INSERT INTO cursor VALUES(1, 0)")


def callback_update(update_id=10, *, number=NUMBER, user=USER, chat=CHAT, bot=BOT, data_action="confirm"):
    return {
        "update_id": update_id,
        "callback_query": {
            "id": "callback-10",
            "from": {"id": user, "is_bot": False},
            "data": f"aicc:{data_action}:{number}",
            "message": {
                "chat": {"id": chat, "type": "private"},
                "from": {"is_bot": True, "username": bot},
                "text": PENDING,
            },
        },
    }


def test_pending_order_reply_has_order_bound_inline_buttons():
    markup = reply_markup(PENDING)
    assert markup == {
        "inline_keyboard": [[
            {"text": "✅ 주문 확인", "callback_data": "aicc:confirm:" + NUMBER},
            {"text": "📋 주문 상세", "callback_data": "aicc:detail:" + NUMBER},
        ]]
    }
    assert len(markup["inline_keyboard"][0][0]["callback_data"].encode()) <= 64
    assert reply_markup(PENDING.replace("고객님 주문\n", "고객님 주문확인 완료\n")) is None
    assert reply_markup("현재 확인 가능한 주문이 없습니다.") is None


def test_callback_is_bound_to_trusted_private_bot_message():
    assert callback_command(callback_update(), CFG) == (
        "callback-10", USER, PHONE + " 고객 주문확인 #" + NUMBER
    )
    assert callback_command(callback_update(number="2610192106"), CFG) is None
    assert callback_command(callback_update(user=USER + 1), CFG) is None
    assert callback_command(callback_update(chat=CHAT + 1), CFG) is None
    assert callback_command(callback_update(bot="other_bot"), CFG) is None


def test_poll_sends_keyboard_and_button_dispatches_same_order(tmp_path):
    path = tmp_path / "cursor.sqlite3"
    cursor_db(path)
    incoming = {
        "update_id": 3,
        "message": {
            "chat": {"id": CHAT, "type": "private"},
            "from": {"id": USER, "is_bot": False},
            "text": PHONE + " 고객 주문확인",
        },
    }
    transport = FakeTransport([incoming])
    calls = []

    def client(text, update_id, actor):
        calls.append((text, update_id, actor))
        return PENDING

    poll_once(transport, client, CFG, path)
    assert transport.messages[0][1] == reply_markup(PENDING)
    assert calls == [(PHONE + " 고객 주문확인", 3 + (1 << 60), "telegram-user-" + str(USER))]

    transport.updates = [callback_update(update_id=4)]
    poll_once(transport, client, CFG, path)
    assert transport.answered == [("callback-10", "주문을 확인하고 있습니다.")]
    assert calls[-1] == (
        PHONE + " 고객 주문확인 #" + NUMBER, 4 + (1 << 60), "telegram-user-" + str(USER)
    )
    assert transport.messages[-1] == (PENDING, reply_markup(PENDING))
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT offset FROM cursor WHERE id=1").fetchone()[0] == 5


def test_invalid_callback_never_reaches_operator_bridge(tmp_path):
    path = tmp_path / "cursor.sqlite3"
    cursor_db(path)
    transport = FakeTransport([callback_update(update_id=8, number="2610192106")])
    calls = []
    poll_once(transport, lambda *args: calls.append(args) or "unexpected", CFG, path)
    assert calls == []
    assert transport.answered == [("callback-10", "이 주문에 사용할 수 없는 버튼입니다.")]


def test_telegram_transport_sends_inline_keyboard_and_callback_ack():
    session = Mock()
    session.post.return_value = SimpleNamespace(
        status_code=200,
        json=lambda: {"ok": True, "result": {"message_id": 9, "chat": {"id": CHAT}}},
    )
    session.get.return_value = SimpleNamespace(
        status_code=200, json=lambda: {"ok": True, "result": []}
    )
    transport = OrderTelegramTransport(
        token=SecretStr("123:" + "a" * 30), chat_id=CHAT, session=session
    )
    markup = reply_markup(PENDING)
    assert transport.send_message(PENDING, reply_markup=markup) == 9
    assert session.post.call_args.kwargs["json"] == {
        "chat_id": CHAT, "text": PENDING, "reply_markup": markup
    }

    session.post.return_value = SimpleNamespace(status_code=200, json=lambda: {"ok": True})
    assert transport.answer_callback_query("callback-10", text="확인 중")
    assert session.post.call_args.kwargs["json"] == {
        "callback_query_id": "callback-10", "text": "확인 중"
    }
    assert session.post.call_args.args[0].endswith("/answerCallbackQuery")

    assert transport.get_updates(4) == []
    assert session.get.call_args.kwargs["params"]["allowed_updates"] == '["message","callback_query"]'


def test_telegram_transport_rejects_arbitrary_reply_markup_shape():
    session = Mock()
    transport = OrderTelegramTransport(
        token=SecretStr("123:" + "a" * 30), chat_id=CHAT, session=session
    )
    with pytest.raises(TelegramDeliveryRejected, match="REPLY_MARKUP_INVALID"):
        transport.send_message("safe", reply_markup={"remove_keyboard": True})
    session.post.assert_not_called()

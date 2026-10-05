"""Explicit order-only Telegram transport/dispatcher; no runtime defaults.

Business state remains in the Mac ledger. This module does not register a
public webhook, activate a poller, read credentials, or send on import.
"""
from __future__ import annotations
import re
from pydantic import SecretStr
import requests

from .ledger import SQLiteOrderCreateLedger


class TelegramDeliveryUnknown(RuntimeError):
    pass


class TelegramDeliveryRejected(RuntimeError):
    pass


class OrderTelegramTransport:
    """Dedicated fixed numeric recipient; no mutable reply-chat or environment defaults."""
    def __init__(self, *, token: SecretStr, chat_id: int, session=None):
        if not isinstance(token, SecretStr) or not re.fullmatch(r"[0-9]+:[A-Za-z0-9_-]{20,}", token.get_secret_value()):
            raise ValueError("explicit Telegram bot credential required")
        if type(chat_id) is not int or chat_id == 0:
            raise ValueError("explicit numeric Telegram recipient required")
        self._token = token
        self.chat_id = chat_id
        self._session = session if session is not None else requests.Session()

    def __repr__(self):
        return "OrderTelegramTransport(configured=True)"

    def _url(self, method):
        return "https://api.telegram.org/bot" + self._token.get_secret_value() + "/" + method

    def send_message(self, text):
        if type(text) is not str or not 1 <= len(text) <= 4096:
            raise TelegramDeliveryRejected("MESSAGE_BOUNDS")
        try:
            response = self._session.post(self._url("sendMessage"),
                json={"chat_id":self.chat_id,"text":text},timeout=15,allow_redirects=False)
            if response.status_code in (400,401,403,404,429):
                raise TelegramDeliveryRejected("TELEGRAM_REJECTED")
            if response.status_code != 200:
                raise TelegramDeliveryUnknown("TELEGRAM_OUTCOME_UNKNOWN")
            value = response.json()
            if type(value) is not dict or value.get("ok") is not True:
                raise TelegramDeliveryUnknown("TELEGRAM_RECEIPT_INVALID")
            result = value.get("result")
            if (type(result) is not dict or type(result.get("message_id")) is not int
                or result['message_id'] <= 0 or type(result.get("chat")) is not dict
                or type(result['chat'].get('id')) is not int or result['chat']['id'] != self.chat_id):
                raise TelegramDeliveryUnknown("TELEGRAM_RECEIPT_INVALID")
            return result['message_id']
        except (TelegramDeliveryRejected, TelegramDeliveryUnknown):
            raise
        except Exception:
            # requests exception strings can include the credential-bearing URL.
            raise TelegramDeliveryUnknown("TELEGRAM_OUTCOME_UNKNOWN") from None

    def get_updates(self, offset):
        try:
            response = self._session.get(self._url("getUpdates"),params={"offset":offset,"limit":100,"timeout":0},
                timeout=15,allow_redirects=False)
            if response.status_code != 200: raise ValueError()
            value = response.json()
            if type(value) is not dict or value.get('ok') is not True or type(value.get('result')) is not list:
                raise ValueError()
            if len(value['result']) > 100: raise ValueError()
            return value['result']
        except Exception:
            raise TelegramDeliveryUnknown("TELEGRAM_POLL_UNAVAILABLE") from None


class OrderTelegramIntegration:
    """Explicit trusted bot transport + fixed operator chat/user allowlist.

    Operator decisions confirm/reject local review only. They never charge,
    change WooCommerce, refund, fulfill, or run generic Control Plane commands.
    """
    def __init__(self, *, ledger: SQLiteOrderCreateLedger, transport,
                 operator_chat_id: int, operator_user_ids: frozenset[int]):
        if type(ledger) is not SQLiteOrderCreateLedger:
            raise TypeError("durable order ledger required")
        if type(operator_chat_id) is not int or operator_chat_id == 0:
            raise ValueError("fixed operator chat required")
        if (type(operator_user_ids) is not frozenset or not operator_user_ids
            or any(type(v) is not int or v <= 0 for v in operator_user_ids)):
            raise ValueError("explicit Telegram operator allowlist required")
        if transport.chat_id != operator_chat_id:
            raise ValueError("transport recipient mismatch")
        self._ledger = ledger
        self._transport = transport
        self._chat = operator_chat_id
        self._users = operator_user_ids

    @staticmethod
    def _message(payload):
        labels = {"PENDING_REVIEW":"운영자 확인 대기", "CONFIRMED":"운영자 확인 완료", "REJECTED":"운영자 거절"}
        reference = payload['reference']
        items = "\n".join("상품: "+str(item['product_id'])+" / 옵션: "+str(item['variation_id'])+" / 수량: "+str(item['quantity'])
                          for item in payload['items'])
        if payload['line_count'] > len(payload['items']):
            items += "\n" + "전체 "+str(payload['line_count'])+"개 항목 중 "+str(len(payload['items']))+"개 표시"
        return ("[AIControlCenter 주문] " + labels.get(payload['review_state'],"주문 상태") + "\n"
            + "주문번호: " + str(payload['provider_order_id']) + "\n"
            + "수량: " + str(payload['quantity']) + "\n"
            + "금액: " + payload['total'] + " " + payload['currency'] + "\n"
            + items + "\n" + "참조: " + reference + "\n"
            + "/order_status " + reference + "\n"
            + "/order_confirm " + reference + "\n"
            + "/order_reject " + reference + "\n"
            + "운영자 확인은 결제·배송 확정이 아닙니다.")

    def dispatch_one(self):
        # A committed CLAIM precedes network I/O. Crashed/unknown claims never auto-retry.
        event = self._ledger.claim_notification()
        if event is None: return {"outcome":"IDLE"}
        key = event['event_key']
        try:
            if self._transport.chat_id != self._chat:
                raise TelegramDeliveryRejected("RECIPIENT_MISMATCH")
            receipt = self._transport.send_message(self._message(event['payload']))
            self._ledger.finish_notification(key,message_id=receipt)
            return {"outcome":"SENT","event_key":key}
        except TelegramDeliveryRejected:
            self._ledger.finish_notification(key,reason_code="TELEGRAM_REJECTED",definitive=True)
            return {"outcome":"FAILED","event_key":key}
        except Exception:
            try: self._ledger.finish_notification(key,reason_code="TELEGRAM_OUTCOME_UNKNOWN")
            except Exception: pass  # Preserve blocked CLAIMED or already committed SENT.
            return {"outcome":"UNKNOWN_OUTCOME","event_key":key}

    def poll_once(self):
        # Only trusted Bot API getUpdates output is accepted. No public webhook exists.
        updates = self._transport.get_updates(self._ledger.telegram_offset())
        if type(updates) is not list or len(updates)>100:
            raise TelegramDeliveryUnknown("TELEGRAM_POLL_INVALID")
        valid = [item for item in updates if type(item) is dict and type(item.get('update_id')) is int
                 and 0 <= item['update_id'] < 2**63-1]
        outcomes = []
        for update in sorted(valid,key=lambda v:v['update_id']):
            message = update.get('message')
            decision = reference = actor = None
            if type(message) is dict:
                chat, sender = message.get('chat'), message.get('from')
                if (type(chat) is dict and type(sender) is dict and type(chat.get('id')) is int
                    and type(sender.get('id')) is int and chat['id']==self._chat and sender['id'] in self._users
                    and sender.get('is_bot') is False and type(message.get('text')) is str):
                    match = re.fullmatch(r"/order_(status|confirm|reject) ([0-9a-f]{24})",message['text'])
                    if match:
                        decision = {"status":"STATUS","confirm":"CONFIRMED","reject":"REJECTED"}[match[1]]
                        reference = match[2]
                        actor = "telegram-user-"+str(sender['id'])
            outcomes.append(self._ledger.process_operator_update(update['update_id'],reference=reference,
                            decision=decision,actor_reference=actor))
        return {"outcome":"PROCESSED","updates":len(outcomes),"results":outcomes}

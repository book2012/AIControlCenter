"""Single-attempt Twilio Messaging transport for account-recovery links.

This is a transport adapter only. It does not resolve credentials, select a
customer, create/reset tokens, or retry ambiguous sends. A durable recovery
outbox must claim each send before calling this adapter and reconcile by the
returned Twilio Message SID.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import json
import re
from typing import Any
from urllib.parse import urlsplit

import requests


_ACCOUNT_SID = re.compile(r"^AC[0-9a-fA-F]{32}$")
_SERVICE_SID = re.compile(r"^MG[0-9a-fA-F]{32}$")
_MESSAGE_SID = re.compile(r"^SM[0-9a-fA-F]{32}$")
_PHONE = re.compile(r"^\+8210[0-9]{8}$")
_EVENT_ID = re.compile(r"^[A-Za-z0-9_-]{16,128}$")
_STATES = frozenset({
    "accepted", "scheduled", "queued", "sending", "sent", "delivered",
    "undelivered", "failed", "canceled",
})


class TwilioRecoveryMessagingError(RuntimeError):
    """Sanitized transport failure; never contains request or response data."""

    def __init__(self, code: str) -> None:
        self.code = code if code in {
            "CONFIGURATION_REQUIRED", "INVALID_REQUEST", "REJECTED",
            "UNKNOWN_OUTCOME", "MALFORMED_RESPONSE", "RECEIPT_MISMATCH",
        } else "UNKNOWN_OUTCOME"
        super().__init__(self.code)

    def __repr__(self) -> str:
        return f"TwilioRecoveryMessagingError(code={self.code!r})"


@dataclass(frozen=True)
class TwilioRecoveryMessagingConfig:
    environment: str
    account_sid: str
    auth_token: str
    messaging_service_sid: str
    test_phone: str
    allowed_link_hosts: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.environment != "DEV":
            raise ValueError("DEV_ONLY")
        if not _ACCOUNT_SID.fullmatch(self.account_sid):
            raise ValueError("CONFIGURATION_REQUIRED")
        if not isinstance(self.auth_token, str) or len(self.auth_token) < 16:
            raise ValueError("CONFIGURATION_REQUIRED")
        if not _SERVICE_SID.fullmatch(self.messaging_service_sid):
            raise ValueError("CONFIGURATION_REQUIRED")
        if not isinstance(self.test_phone, str) or not _PHONE.fullmatch(self.test_phone):
            raise ValueError("CONFIGURATION_REQUIRED")
        if (not self.allowed_link_hosts or any(
            not isinstance(host, str) or not host or "/" in host or ":" in host
            for host in self.allowed_link_hosts
        )):
            raise ValueError("CONFIGURATION_REQUIRED")

    @classmethod
    def from_mapping(cls, value: object) -> "TwilioRecoveryMessagingConfig":
        if type(value) is not dict or value.get("environment") != "DEV":
            raise ValueError("DEV_ONLY")
        credentials = value.get("credentials")
        if type(credentials) is not dict:
            raise ValueError("CONFIGURATION_REQUIRED")
        try:
            return cls(
                environment=value["environment"],
                account_sid=credentials["account_sid"],
                auth_token=credentials["auth_token"],
                messaging_service_sid=credentials["messaging_service_sid"],
                test_phone=value["test_phone"],
                allowed_link_hosts=tuple(value["allowed_link_hosts"]),
            )
        except (KeyError, TypeError):
            raise ValueError("CONFIGURATION_REQUIRED") from None

    def __repr__(self) -> str:
        return (
            "TwilioRecoveryMessagingConfig(environment='DEV', "
            "credentials=<redacted>, test_phone=<redacted>, messaging_service=<configured>)"
        )


@dataclass(frozen=True)
class TwilioMessageReceipt:
    event_id: str
    message_sid: str
    state: str
    recipient_binding: str

    def __repr__(self) -> str:
        return (
            "TwilioMessageReceipt("
            f"event_id={self.event_id!r}, message_sid={self.message_sid!r}, "
            f"state={self.state!r}, recipient_binding=<redacted>)"
        )


def _validate_link(body: str, allowed_hosts: tuple[str, ...]) -> None:
    if type(body) is not str or not 1 <= len(body) <= 1600:
        raise TwilioRecoveryMessagingError("INVALID_REQUEST")
    links = re.findall(r"https://[^\s<>]+", body)
    if len(links) != 1:
        raise TwilioRecoveryMessagingError("INVALID_REQUEST")
    try:
        parsed = urlsplit(links[0].rstrip(".,)"))
    except ValueError:
        raise TwilioRecoveryMessagingError("INVALID_REQUEST") from None
    try:
        host = (parsed.hostname or "").lower()
        port = parsed.port
        username, password, fragment = parsed.username, parsed.password, parsed.fragment
    except ValueError:
        raise TwilioRecoveryMessagingError("INVALID_REQUEST") from None
    if (
        parsed.scheme != "https" or host not in {h.lower() for h in allowed_hosts}
        or username is not None or password is not None
        or port not in (None, 443) or fragment
    ):
        raise TwilioRecoveryMessagingError("INVALID_REQUEST")


def _read_document(response: Any) -> object:
    body = bytearray()
    try:
        for chunk in response.iter_content(chunk_size=8192):
            if len(body) + len(chunk) > 65536:
                raise ValueError("response too large")
            body.extend(chunk)
        return json.loads(body.decode("utf-8"))
    finally:
        response.close()


class TwilioRecoveryLinkSMS:
    """Pinned one-attempt Messaging API client; DEV and configured hosts only."""

    def __init__(self, config: TwilioRecoveryMessagingConfig, *, session: Any = None) -> None:
        if type(config) is not TwilioRecoveryMessagingConfig:
            raise ValueError("CONFIGURATION_REQUIRED")
        self._config = config
        self._session = session or requests.Session()
        self._session.trust_env = False

    def __repr__(self) -> str:
        return "TwilioRecoveryLinkSMS(environment='DEV', credentials=<redacted>)"

    def send(self, recipient: str, body: str, event_id: str) -> TwilioMessageReceipt:
        if (
            type(recipient) is not str or recipient != self._config.test_phone
            or type(event_id) is not str or not _EVENT_ID.fullmatch(event_id)
        ):
            raise TwilioRecoveryMessagingError("INVALID_REQUEST")
        _validate_link(body, self._config.allowed_link_hosts)
        url = (
            "https://api.twilio.com/2010-04-01/Accounts/"
            f"{self._config.account_sid}/Messages.json"
        )
        try:
            response = self._session.post(
                url,
                auth=(self._config.account_sid, self._config.auth_token),
                data={
                    "To": recipient,
                    "MessagingServiceSid": self._config.messaging_service_sid,
                    "Body": body,
                },
                timeout=15,
                allow_redirects=False,
                stream=True,
            )
            status_code = response.status_code
            if status_code not in (200, 201):
                response.close()
                code = "REJECTED" if status_code in (400, 401, 403, 404, 429) else "UNKNOWN_OUTCOME"
                raise TwilioRecoveryMessagingError(code)
            document = _read_document(response)
        except TwilioRecoveryMessagingError:
            raise
        except Exception:
            raise TwilioRecoveryMessagingError("UNKNOWN_OUTCOME") from None
        return self._receipt(document, recipient, event_id)

    def reconcile(self, receipt: TwilioMessageReceipt) -> TwilioMessageReceipt:
        if type(receipt) is not TwilioMessageReceipt or not _MESSAGE_SID.fullmatch(receipt.message_sid):
            raise TwilioRecoveryMessagingError("INVALID_REQUEST")
        url = (
            "https://api.twilio.com/2010-04-01/Accounts/"
            f"{self._config.account_sid}/Messages/{receipt.message_sid}.json"
        )
        try:
            response = self._session.get(
                url,
                auth=(self._config.account_sid, self._config.auth_token),
                timeout=15,
                allow_redirects=False,
                stream=True,
            )
            status_code = response.status_code
            if status_code != 200:
                response.close()
                raise TwilioRecoveryMessagingError(
                    "REJECTED" if status_code in (400, 401, 403, 404, 429)
                    else "UNKNOWN_OUTCOME"
                )
            document = _read_document(response)
        except TwilioRecoveryMessagingError:
            raise
        except Exception:
            raise TwilioRecoveryMessagingError("UNKNOWN_OUTCOME") from None
        result = self._receipt(document, self._config.test_phone, receipt.event_id)
        if result.message_sid != receipt.message_sid:
            raise TwilioRecoveryMessagingError("RECEIPT_MISMATCH")
        if result.recipient_binding != receipt.recipient_binding:
            raise TwilioRecoveryMessagingError("RECEIPT_MISMATCH")
        return result

    def _receipt(self, document: object, recipient: str | None, event_id: str) -> TwilioMessageReceipt:
        if type(document) is not dict:
            raise TwilioRecoveryMessagingError("MALFORMED_RESPONSE")
        sid, state = document.get("sid"), document.get("status")
        to, service_sid = document.get("to"), document.get("messaging_service_sid")
        if (
            type(sid) is not str or not _MESSAGE_SID.fullmatch(sid)
            or type(state) is not str or state not in _STATES
            or (recipient is not None and to != recipient)
            or service_sid != self._config.messaging_service_sid
            or type(to) is not str or not _PHONE.fullmatch(to)
        ):
            raise TwilioRecoveryMessagingError("RECEIPT_MISMATCH")
        # Binding is intentionally non-reversible and scoped to this DEV adapter.
        return TwilioMessageReceipt(event_id, sid, state.upper(), "DEV_FIXED_TEST_RECIPIENT")

"""DEV fixed-recipient Twilio Verify adapter for account recovery.

The transport is injected so importing this module cannot send SMS. Composition
must inject the existing fixed-test-phone DEV Verify port; recipient scope is
checked again here before either provider operation.
"""
from __future__ import annotations

import re
from typing import Protocol


class _FixedDevVerifyTransport(Protocol):
    phone: object

    def invoke(self, path: str, body: dict) -> dict: ...


class TwilioRecoveryVerifyAdapter:
    """Bind account-recovery challenges to the already configured DEV test phone."""

    def __init__(self, transport: _FixedDevVerifyTransport) -> None:
        configured_phone = getattr(getattr(transport, "phone", None), "value", None)
        if type(configured_phone) is not str or not re.fullmatch(r"\+8210[0-9]{8}", configured_phone):
            raise ValueError("DEV_RECOVERY_PHONE_CONFIGURATION_INVALID")
        self._transport = transport
        self._phone = configured_phone

    def start(self, phone: str, event_id: str) -> str:
        if phone != self._phone or type(event_id) is not str or not event_id:
            raise ValueError("DEV_RECOVERY_RECIPIENT_REJECTED")
        result = self._transport.invoke(
            "Verifications", {"To": self._phone, "Channel": "sms", "Locale": "ko"},
        )
        if (type(result) is not dict or result.get("to") != self._phone
                or result.get("channel") != "sms" or result.get("status") != "pending"
                or not re.fullmatch(r"VE[0-9a-fA-F]{32}", result.get("sid", ""))):
            raise RuntimeError("DEV_RECOVERY_PROVIDER_EVIDENCE_INVALID")
        return result["sid"]

    def verify(self, phone: str, verification_id: str, code: str) -> bool:
        if (phone != self._phone or type(verification_id) is not str
                or not re.fullmatch(r"VE[0-9a-fA-F]{32}", verification_id)
                or type(code) is not str or not re.fullmatch(r"[0-9]{4,10}", code)):
            return False
        try:
            result = self._transport.invoke(
                "VerificationCheck",
                {"VerificationSid": verification_id, "Code": code},
            )
        except Exception as error:
            # The existing fixed DEV transport classifies definitive Twilio
            # rejection separately from ambiguous network/provider outcomes.
            if getattr(error, "code", None) == "REJECTED":
                return False
            raise
        return bool(
            type(result) is dict
            and result.get("sid") == verification_id
            and result.get("to") == self._phone
            and result.get("channel") == "sms"
            and result.get("status") == "approved"
        )


__all__ = ["TwilioRecoveryVerifyAdapter"]

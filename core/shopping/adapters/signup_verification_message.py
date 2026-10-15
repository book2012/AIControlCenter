"""Signup verification message contract for fake-provider tests.

Production Twilio Verify generates and sends the OTP using an approved
provider-side template. This helper formats test previews only; it does not
generate codes or send messages.
"""
from __future__ import annotations

import re


SIGNUP_OTP_CODE_LENGTH = 4
SIGNUP_SMS_TEMPLATE = "[Agachichi] 인증번호 {code} 입니다"
_CODE = re.compile(r"[0-9]{4}\Z", re.ASCII)


def render_signup_sms_preview(code: str) -> str:
    """Render the approved copy shape for a fake-provider preview."""
    if type(code) is not str or not _CODE.fullmatch(code):
        raise ValueError("SIGNUP_OTP_CODE_INVALID")
    return SIGNUP_SMS_TEMPLATE.format(code=code)


__all__ = [
    "SIGNUP_OTP_CODE_LENGTH",
    "SIGNUP_SMS_TEMPLATE",
    "render_signup_sms_preview",
]

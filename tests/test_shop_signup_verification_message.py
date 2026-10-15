import pytest

from core.shopping.adapters.signup_verification_message import (
    SIGNUP_OTP_CODE_LENGTH,
    SIGNUP_SMS_TEMPLATE,
    render_signup_sms_preview,
)


def test_signup_sms_copy_uses_agachichi_brand_and_four_digit_code():
    assert SIGNUP_OTP_CODE_LENGTH == 4
    assert SIGNUP_SMS_TEMPLATE == "[Agachichi] 인증번호 {code} 입니다"
    assert render_signup_sms_preview("0427") == "[Agachichi] 인증번호 0427 입니다"


@pytest.mark.parametrize("code", ["427", "12345", "12a4", "", None, 1234])
def test_signup_sms_preview_rejects_codes_outside_four_ascii_digits(code):
    with pytest.raises(ValueError, match="SIGNUP_OTP_CODE_INVALID"):
        render_signup_sms_preview(code)

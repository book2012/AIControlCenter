import pytest

from core.shopping.account_registration import (
    SignupCandidate,
    SignupInputError,
    ValidatedSignupCandidate,
    validate_signup_candidate,
)


def candidate(**overrides):
    values = {
        "login_id": "user_01",
        "email": "customer@example.com",
        "password": "secure-pass-123",
        "password_confirmation": "secure-pass-123",
        "phone": "+821012345678",
        "terms_accepted": True,
        "terms_version": "terms-2026-10-16",
        "privacy_notice_version": "privacy-2026-10-16",
    }
    values.update(overrides)
    return SignupCandidate(**values)


def test_valid_candidate_is_returned_as_unverified_minimal_contract():
    result = validate_signup_candidate(candidate())
    assert type(result) is ValidatedSignupCandidate
    assert result.login_id == "user_01"
    assert result.phone == "+821012345678"
    assert result.terms_version == "terms-2026-10-16"
    assert result.privacy_notice_version == "privacy-2026-10-16"
    assert not hasattr(result, "full_name")


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("login_id", "a", "SIGNUP_LOGIN_ID_INVALID"),
        ("login_id", "한글아이디", "SIGNUP_LOGIN_ID_INVALID"),
        ("login_id", "1" * 21, "SIGNUP_LOGIN_ID_INVALID"),
        ("email", "not-an-email", "SIGNUP_EMAIL_INVALID"),
        ("email", "a@localhost", "SIGNUP_EMAIL_INVALID"),
        ("password", "short", "SIGNUP_PASSWORD_INVALID"),
        ("password_confirmation", "different-password", "SIGNUP_PASSWORD_INVALID"),
        ("phone", "01012345678", "SIGNUP_PHONE_INVALID"),
        ("phone", "+821199999999", "SIGNUP_PHONE_INVALID"),
        ("terms_accepted", False, "SIGNUP_TERMS_REQUIRED"),
        ("terms_version", "", "SIGNUP_TERMS_VERSION_INVALID"),
        ("privacy_notice_version", "", "SIGNUP_PRIVACY_NOTICE_VERSION_INVALID"),
    ],
)
def test_invalid_input_returns_stable_code_without_echoing_values(field, value, code):
    with pytest.raises(SignupInputError) as exc:
        validate_signup_candidate(candidate(**{field: value}))
    assert exc.value.code == code
    assert str(exc.value) == code


def test_candidate_representations_redact_email_phone_and_password():
    draft = candidate()
    validated = validate_signup_candidate(draft)
    rendered = repr(draft) + repr(validated)
    for private in (
        "customer@example.com",
        "+821012345678",
        "secure-pass-123",
    ):
        assert private not in rendered


def test_candidate_requires_exact_type_and_strict_boolean_terms_acceptance():
    with pytest.raises(SignupInputError) as exc:
        validate_signup_candidate(object())
    assert exc.value.code == "SIGNUP_INPUT_INVALID"

    with pytest.raises(SignupInputError) as exc:
        validate_signup_candidate(candidate(terms_accepted=1))
    assert exc.value.code == "SIGNUP_TERMS_REQUIRED"


@pytest.mark.parametrize("field", ["full_name", "privacy_accepted"])
def test_candidate_rejects_name_and_blanket_privacy_consent_fields(field):
    with pytest.raises(TypeError):
        candidate(**{field: "홍길동" if field == "full_name" else True})

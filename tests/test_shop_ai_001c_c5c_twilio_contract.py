from __future__ import annotations

import pytest

from core.shopping.adapters.twilio_verify_read import (
    TwilioReadRequestSpec,
    TwilioServiceSid,
    TwilioVerificationSid,
    TwilioVerifyReadError,
    build_service_read_request,
    build_verification_read_request,
)
from core.shopping.ports.provider_activation import ProviderOperation


SERVICE = "VA" + "a" * 32
VERIFY = "VE" + "b" * 32


def test_exact_twilio_sid_contracts() -> None:
    assert str(TwilioServiceSid(SERVICE)) == SERVICE
    assert str(TwilioVerificationSid(VERIFY)) == VERIFY


@pytest.mark.parametrize(
    "value",
    [
        "",
        "VA",
        "va" + "a" * 32,
        "VA" + "a" * 31,
        "VA" + "a" * 33,
        "VA" + "g" * 32,
        "VA" + "a" * 31 + "/",
        "VA" + "a" * 31 + "?",
    ],
)
def test_service_sid_rejects_non_exact_values(value: str) -> None:
    with pytest.raises(TwilioVerifyReadError):
        TwilioServiceSid(value)


@pytest.mark.parametrize(
    "value",
    [
        "",
        "VE",
        "ve" + "b" * 32,
        "VE" + "b" * 31,
        "VE" + "b" * 33,
        "VE" + "g" * 32,
        "VE" + "b" * 31 + "/",
        "VE" + "b" * 31 + "?",
    ],
)
def test_verification_sid_rejects_non_exact_values(value: str) -> None:
    with pytest.raises(TwilioVerifyReadError):
        TwilioVerificationSid(value)


def test_service_request_is_exact_get_only_spec() -> None:
    request = build_service_read_request(
        TwilioServiceSid(SERVICE)
    )

    assert request.operation is ProviderOperation.READ_HEALTH
    assert request.method == "GET"
    assert request.path == f"/v2/Services/{SERVICE}"
    assert "?" not in request.path
    assert "://" not in request.path


def test_verification_request_is_exact_get_only_spec() -> None:
    request = build_verification_read_request(
        TwilioServiceSid(SERVICE),
        TwilioVerificationSid(VERIFY),
    )

    assert request.operation is ProviderOperation.READ_EVIDENCE
    assert request.method == "GET"
    assert request.path == (
        f"/v2/Services/{SERVICE}/Verifications/{VERIFY}"
    )


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", f"/v2/Services/{SERVICE}"),
        ("PUT", f"/v2/Services/{SERVICE}"),
        ("PATCH", f"/v2/Services/{SERVICE}"),
        ("DELETE", f"/v2/Services/{SERVICE}"),
        ("GET", f"/v2/Services/{SERVICE}?PageSize=1"),
        ("GET", f"/v2/Services/{SERVICE}#fragment"),
        ("GET", f"https://evil.example/v2/Services/{SERVICE}"),
        ("GET", f"/v2/Services/../{SERVICE}"),
    ],
)
def test_request_spec_rejects_method_and_path_injection(
    method: str,
    path: str,
) -> None:
    with pytest.raises(TwilioVerifyReadError):
        TwilioReadRequestSpec(
            operation=ProviderOperation.READ_HEALTH,
            method=method,
            path=path,
        )

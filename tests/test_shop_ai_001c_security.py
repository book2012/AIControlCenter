from __future__ import annotations

import ast
from pathlib import Path

import pytest

from core.shopping.customer_auth import (
    RECEIPT_MAX_LIFETIME, ReceiptLifecycle, ReceiptValidationResult,
    TrustedReceiptBinding, TrustedVerificationContext, TrustedVerificationReceipt,
    VerificationPurpose, validate_trusted_receipt,
)


ROOT = Path(__file__).parents[1]
SOURCE_PATHS = (
    ROOT / "core/shopping/customer_auth.py",
    ROOT / "core/shopping/phone_normalization.py",
    ROOT / "core/shopping/ports/phone_verification.py",
    ROOT / "core/shopping/phone_verification_service.py",
)


def test_new_production_sources_have_no_network_provider_ubuntu_or_api_activation_imports() -> None:
    forbidden = {"socket", "requests", "httpx", "urllib3", "twilio", "vonage", "boto3", "core.api.app"}
    for path in SOURCE_PATHS:
        tree = ast.parse(path.read_text())
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        rendered = "\n".join(imports).lower()
        assert not any(value in rendered for value in forbidden), path
        assert "ubuntu" not in path.read_text().lower()


def test_trusted_receipt_and_context_never_carry_phone_otp_or_credentials() -> None:
    from datetime import datetime, timedelta, timezone

    now = datetime(2026, 9, 27, 12, 0, tzinfo=timezone.utc)
    receipt = TrustedVerificationReceipt(
        receipt_id="AG-VRF-" + "3" * 12 + "4" + "3" * 3 + "8" + "3" * 15,
        purpose=VerificationPurpose.SESSION_ISSUANCE,
        browser_challenge="AG-CHL-" + "2" * 12 + "4" + "2" * 3 + "8" + "2" * 15,
        issuer_ref="AG-ISS-" + "4" * 12 + "4" + "4" * 3 + "8" + "4" * 15,
        customer_id="AG-CUS-" + "5" * 12 + "4" + "5" * 3 + "8" + "5" * 15,
        issued_at=now,
        expires_at=now + timedelta(minutes=5),
    )
    context = TrustedVerificationContext(accepted_bindings=frozenset({
        TrustedReceiptBinding(receipt.receipt_id, receipt.issuer_ref, receipt.customer_id),
    }))
    rendered = repr(receipt) + repr(context)
    for secret in ("+821012345678", "123456", "provider-secret", "api-key"):
        assert secret not in rendered


def test_existing_b3a_lifecycle_and_time_guards_remain_fail_closed() -> None:
    from datetime import datetime, timedelta, timezone

    now = datetime(2026, 9, 27, 12, 0, tzinfo=timezone.utc)
    receipt = TrustedVerificationReceipt(
        receipt_id="AG-VRF-" + "3" * 12 + "4" + "3" * 3 + "8" + "3" * 15,
        purpose=VerificationPurpose.SESSION_ISSUANCE,
        browser_challenge="AG-CHL-" + "2" * 12 + "4" + "2" * 3 + "8" + "2" * 15,
        issuer_ref="AG-ISS-" + "4" * 12 + "4" + "4" * 3 + "8" + "4" * 15,
        customer_id="AG-CUS-" + "5" * 12 + "4" + "5" * 3 + "8" + "5" * 15,
        issued_at=now,
        expires_at=now + timedelta(minutes=5),
    )
    context = TrustedVerificationContext(accepted_bindings=frozenset({
        TrustedReceiptBinding(receipt.receipt_id, receipt.issuer_ref, receipt.customer_id),
    }))
    assert validate_trusted_receipt(
        receipt, now=now, expected_challenge=receipt.browser_challenge, context=context,
    ) is ReceiptValidationResult.ACCEPTED
    assert validate_trusted_receipt(
        receipt, now=now + RECEIPT_MAX_LIFETIME, expected_challenge=receipt.browser_challenge,
        context=context,
    ) is ReceiptValidationResult.EXPIRED
    revoked = receipt.model_copy(update={"lifecycle": ReceiptLifecycle.REVOKED})
    assert validate_trusted_receipt(
        revoked, now=now, expected_challenge=receipt.browser_challenge, context=context,
    ) is ReceiptValidationResult.INVALID_LIFECYCLE
    replayed = TrustedVerificationContext(
        accepted_bindings=context.accepted_bindings,
        consumed_receipt_ids=frozenset({receipt.receipt_id}),
    )
    assert validate_trusted_receipt(
        receipt, now=now, expected_challenge=receipt.browser_challenge, context=replayed,
    ) is ReceiptValidationResult.REPLAYED
    invalid_lifetime = receipt.model_dump()
    invalid_lifetime["expires_at"] = now + timedelta(minutes=6)
    with pytest.raises(ValueError):
        TrustedVerificationReceipt(**invalid_lifetime)

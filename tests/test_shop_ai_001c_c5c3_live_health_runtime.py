from __future__ import annotations

from datetime import timedelta
import inspect

import pytest

from core.secrets.ports import SecretReference
from core.shopping.adapters.twilio_verify_read import (
    TWILIO_PROVIDER_SOURCE,
    TwilioServiceSid,
    TwilioVerificationSid,
)
from core.shopping.governance.twilio_authenticated_read_authority import (
    TwilioAuthenticatedReadAuthority,
    TwilioAuthenticatedReadRequest,
)
from core.shopping.ports.provider_activation import (
    ProviderOperation,
    ProviderRequestIdentity,
)
from ops.macos.shopping.provider_secret_resolver import (
    ProviderSecretResolver,
)
from ops.macos.shopping.twilio_authenticated_read_live_health_runtime import (
    TwilioAuthenticatedReadLiveHealthRuntime,
    TwilioLiveReadHealthError,
)


SERVICE_SID = (
    "VA9e43965d4c5572a9e59df03e23e5e6ca"
)

KEY_SID = (
    b"SK" + (b"1" * 32)
)

SID_SERVICE = (
    "aicontrolcenter.twilio.nonprod.api-key-sid"
)

SECRET_SERVICE = (
    "aicontrolcenter.twilio.nonprod.api-key-secret"
)


def _reference(service: str) -> SecretReference:
    fields = SecretReference.model_fields

    required = [
        name
        for name, info in fields.items()
        if (
            name != "backend"
            and info.is_required()
        )
    ]

    assert len(required) == 1

    return SecretReference(
        **{
            "backend": "macos.keychain",
            required[0]: service,
        }
    )


def _request(
    operation=ProviderOperation.READ_HEALTH,
):
    return TwilioAuthenticatedReadRequest(
        provider_source=TWILIO_PROVIDER_SOURCE,
        operation=operation,
        identity=ProviderRequestIdentity(
            request_id="live-health-test-request",
            correlation_id=(
                "live-health-test-correlation"
            ),
        ),
        service_sid=TwilioServiceSid(
            SERVICE_SID
        ),
        verification_sid=(
            None
            if operation
            is ProviderOperation.READ_HEALTH
            else TwilioVerificationSid(
                "VE1234567890abcdef1234567890abcdef"
            )
        ),
    )


def _runtime(*, calls, reads):
    authority = TwilioAuthenticatedReadAuthority()

    sid_ref = _reference(SID_SERVICE)
    secret_ref = _reference(SECRET_SERVICE)

    def reader(reference):
        reads.append(reference.to_dict())

        values = set(
            value
            for value
            in reference.to_dict().values()
            if type(value) is str
        )

        if SID_SERVICE in values:
            return KEY_SID

        if SECRET_SERVICE in values:
            return b"test-secret-value"

        raise AssertionError(
            "unexpected secret reference"
        )

    resolver = ProviderSecretResolver(
        reader=reader,
        lease_ttl=timedelta(seconds=30),
    )

    def http_get(path, sid, secret):
        calls.append(
            {
                "path": path,
                "sid": sid,
                "secret": secret,
            }
        )

        return (
            200,
            {
                "sid": SERVICE_SID,
            },
        )

    runtime = (
        TwilioAuthenticatedReadLiveHealthRuntime(
            authority=authority,
            api_key_sid_reference=sid_ref,
            api_key_secret_reference=secret_ref,
            secret_resolver=resolver,
            http_get=http_get,
        )
    )

    return authority, runtime


def test_live_health_authorizes_before_secret_resolution():
    calls = []
    reads = []

    authority, runtime = _runtime(
        calls=calls,
        reads=reads,
    )

    request = _request()

    capability = authority.issue(
        request,
        ttl_seconds=30,
    )

    result = runtime.execute(
        request,
        capability=capability,
    )

    assert len(reads) == 2
    assert len(calls) == 1

    assert calls[0]["path"] == (
        f"/v2/Services/{SERVICE_SID}"
    )

    assert calls[0]["sid"] == KEY_SID

    status = getattr(
        result.status,
        "value",
        result.status,
    )

    assert status == "HEALTHY"


def test_denied_capability_performs_zero_secret_resolution():
    calls = []
    reads = []

    _, runtime = _runtime(
        calls=calls,
        reads=reads,
    )

    with pytest.raises(
        TwilioLiveReadHealthError
    ):
        runtime.execute(
            _request(),
            capability=None,
        )

    assert reads == []
    assert calls == []


def test_capability_is_one_shot():
    calls = []
    reads = []

    authority, runtime = _runtime(
        calls=calls,
        reads=reads,
    )

    request = _request()
    capability = authority.issue(
        request,
        ttl_seconds=30,
    )

    runtime.execute(
        request,
        capability=capability,
    )

    first_read_count = len(reads)
    first_call_count = len(calls)

    with pytest.raises(
        TwilioLiveReadHealthError
    ):
        runtime.execute(
            request,
            capability=capability,
        )

    assert len(reads) == first_read_count
    assert len(calls) == first_call_count


def test_live_read_evidence_is_not_enabled():
    calls = []
    reads = []

    authority, runtime = _runtime(
        calls=calls,
        reads=reads,
    )

    request = _request(
        ProviderOperation.READ_EVIDENCE
    )

    capability = authority.issue(
        request,
        ttl_seconds=30,
    )

    with pytest.raises(
        TwilioLiveReadHealthError
    ) as exc:
        runtime.execute(
            request,
            capability=capability,
        )

    assert (
        exc.value.reason_code
        == "LIVE_OPERATION_NOT_ENABLED"
    )

    assert reads == []
    assert calls == []


def test_live_runtime_properties_are_fail_closed():
    calls = []
    reads = []

    _, runtime = _runtime(
        calls=calls,
        reads=reads,
    )

    assert runtime.network_enabled is True
    assert (
        runtime.real_credential_resolution_enabled
        is True
    )
    assert runtime.sms_enabled is False
    assert runtime.max_attempts == 1
    assert runtime.retry_enabled is False
    assert runtime.fallback_enabled is False


def test_live_runtime_source_contains_no_write_http_verbs():
    import ops.macos.shopping.twilio_authenticated_read_live_health_runtime as module

    source = inspect.getsource(module)

    for verb in (
        '"POST"',
        '"PUT"',
        '"PATCH"',
        '"DELETE"',
    ):
        assert verb not in source
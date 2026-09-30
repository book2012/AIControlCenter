from datetime import datetime, timezone

import pytest

from core.secrets.ports import (
    EphemeralSecretLease,
    SecretLeaseConsumed,
    SecretReference,
)
from core.shopping.adapters.twilio_authenticated_read_offline_transport import (
    TwilioOfflineHttpObservation,
    TwilioOfflineReadExecutionError,
    build_twilio_offline_read_request_spec,
)
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
from core.shopping.ports.provider_authenticated_read import (
    ProviderReadResult,
    ProviderReadStatus,
)
from ops.macos.shopping.twilio_authenticated_read_offline_runtime import (
    build_twilio_authenticated_read_offline_runtime,
)


NOW = datetime(
    2026, 9, 30, 0, 0, tzinfo=timezone.utc
)

SERVICE = "VA" + ("1" * 32)
VERIFICATION = "VE" + ("2" * 32)


def _sid(cls, value):
    try:
        return cls(value=value)
    except TypeError:
        return cls(value)


def _request(operation=ProviderOperation.READ_HEALTH):
    return TwilioAuthenticatedReadRequest(
        provider_source=TWILIO_PROVIDER_SOURCE,
        operation=operation,
        identity=ProviderRequestIdentity(
            request_id="req-001",
            correlation_id="corr-001",
        ),
        service_sid=_sid(
            TwilioServiceSid,
            SERVICE,
        ),
        verification_sid=(
            _sid(
                TwilioVerificationSid,
                VERIFICATION,
            )
            if operation
            is ProviderOperation.READ_EVIDENCE
            else None
        ),
    )


class FakeResolver:
    def __init__(self):
        self.calls = 0
        self.leases = []

    def resolve(self, reference):
        self.calls += 1
        material = (
            "opaque-key-id"
            if reference.key_name.endswith("sid")
            else "opaque-key-material"
        )
        lease = EphemeralSecretLease(
            material,
            utc_clock=lambda: NOW,
        )
        self.leases.append(lease)
        return lease


class FailingResolver:
    def __init__(self):
        self.calls = 0

    def resolve(self, reference):
        self.calls += 1
        raise RuntimeError("unbounded internal failure")


class FakeExecutor:
    def __init__(self):
        self.calls = 0
        self.last_request = None

    def get(
        self,
        request,
        *,
        api_key_sid,
        api_key_secret,
    ):
        self.calls += 1
        self.last_request = request
        assert api_key_sid
        assert api_key_secret
        return TwilioOfflineHttpObservation(
            status_code=200,
            payload={"status": "ok"},
        )


class FailingExecutor(FakeExecutor):
    def get(
        self,
        request,
        *,
        api_key_sid,
        api_key_secret,
    ):
        self.calls += 1
        raise RuntimeError(
            "raw-provider-error-should-not-escape"
        )


class HealthNormalizer:
    def __init__(self):
        self.calls = 0

    def normalize(
        self,
        *,
        request,
        request_spec,
        observation,
    ):
        self.calls += 1
        return ProviderReadResult(
            provider_source=TWILIO_PROVIDER_SOURCE,
            operation=request.operation,
            identity=request.identity,
            status=ProviderReadStatus.HEALTHY,
            observed_at=NOW,
        )


SID_REF = SecretReference(
    backend='macos.keychain',
    key_name="twilio.api_key_sid",
)

SECRET_REF = SecretReference(
    backend='macos.keychain',
    key_name="twilio.api_key_secret",
)


def _runtime(
    *,
    resolver=None,
    executor=None,
    normalizer=None,
):
    authority = TwilioAuthenticatedReadAuthority(
        clock=lambda: NOW,
    )
    resolver = resolver or FakeResolver()
    executor = executor or FakeExecutor()
    normalizer = normalizer or HealthNormalizer()

    runtime = (
        build_twilio_authenticated_read_offline_runtime(
            authority=authority,
            api_key_sid_reference=SID_REF,
            api_key_secret_reference=SECRET_REF,
            secret_resolver=resolver,
            executor=executor,
            normalizer=normalizer,
        )
    )

    return (
        authority,
        runtime,
        resolver,
        executor,
        normalizer,
    )


def test_health_spec_is_exact_get_resource():
    spec = build_twilio_offline_read_request_spec(
        _request()
    )
    assert spec.method == "GET"
    assert spec.operation is ProviderOperation.READ_HEALTH
    assert spec.path == f"/v2/Services/{SERVICE}"


def test_evidence_spec_is_exact_get_resource():
    spec = build_twilio_offline_read_request_spec(
        _request(
            ProviderOperation.READ_EVIDENCE
        )
    )
    assert spec.method == "GET"
    assert spec.operation is ProviderOperation.READ_EVIDENCE
    assert spec.path == (
        f"/v2/Services/{SERVICE}"
        f"/Verifications/{VERIFICATION}"
    )


def test_missing_capability_stops_before_secret_resolution():
    (
        authority,
        runtime,
        resolver,
        executor,
        normalizer,
    ) = _runtime()

    with pytest.raises(
        TwilioOfflineReadExecutionError
    ) as exc:
        runtime.execute(
            _request(),
            capability=None,
        )

    assert exc.value.reason_code == (
        "AUTHORIZATION_REJECTED"
    )
    assert resolver.calls == 0
    assert executor.calls == 0
    assert normalizer.calls == 0
    assert authority.consumed_count == 0


def test_valid_capability_authorizes_before_resolver():
    (
        authority,
        runtime,
        resolver,
        executor,
        normalizer,
    ) = _runtime()

    request = _request()
    capability = authority.issue(request)

    result = runtime.execute(
        request,
        capability=capability,
    )

    assert result.status is ProviderReadStatus.HEALTHY
    assert authority.consumed_count == 1
    assert resolver.calls == 2
    assert executor.calls == 1
    assert normalizer.calls == 1


def test_secret_leases_are_consumed_once():
    (
        authority,
        runtime,
        resolver,
        executor,
        normalizer,
    ) = _runtime()

    request = _request()
    capability = authority.issue(request)

    runtime.execute(
        request,
        capability=capability,
    )

    assert len(resolver.leases) == 2

    for lease in resolver.leases:
        with pytest.raises(SecretLeaseConsumed):
            lease.consume()


def test_capability_cannot_retry_transport():
    (
        authority,
        runtime,
        resolver,
        executor,
        normalizer,
    ) = _runtime()

    request = _request()
    capability = authority.issue(request)

    runtime.execute(
        request,
        capability=capability,
    )

    with pytest.raises(
        TwilioOfflineReadExecutionError
    ) as exc:
        runtime.execute(
            request,
            capability=capability,
        )

    assert exc.value.reason_code == (
        "AUTHORIZATION_REJECTED"
    )
    assert resolver.calls == 2
    assert executor.calls == 1


def test_resolver_failure_is_bounded_and_no_executor():
    resolver = FailingResolver()

    (
        authority,
        runtime,
        _,
        executor,
        normalizer,
    ) = _runtime(
        resolver=resolver
    )

    request = _request()
    capability = authority.issue(request)

    with pytest.raises(
        TwilioOfflineReadExecutionError
    ) as exc:
        runtime.execute(
            request,
            capability=capability,
        )

    assert exc.value.reason_code == (
        "SECRET_RESOLUTION_FAILED"
    )
    assert resolver.calls == 1
    assert executor.calls == 0
    assert normalizer.calls == 0


def test_executor_failure_is_single_attempt_and_bounded():
    executor = FailingExecutor()

    (
        authority,
        runtime,
        resolver,
        _,
        normalizer,
    ) = _runtime(
        executor=executor
    )

    request = _request()
    capability = authority.issue(request)

    with pytest.raises(
        TwilioOfflineReadExecutionError
    ) as exc:
        runtime.execute(
            request,
            capability=capability,
        )

    assert exc.value.reason_code == (
        "OFFLINE_EXECUTOR_FAILED"
    )
    assert executor.calls == 1
    assert resolver.calls == 2
    assert normalizer.calls == 0
    assert (
        "raw-provider-error"
        not in str(exc.value)
    )


def test_offline_runtime_flags_remain_inert():
    (
        authority,
        runtime,
        resolver,
        executor,
        normalizer,
    ) = _runtime()

    assert runtime.network_enabled is False
    assert (
        runtime.real_credential_resolution_enabled
        is False
    )
    assert runtime.keychain_accessed is False
    assert runtime.sms_enabled is False
    assert runtime.transport.max_attempts == 1
    assert runtime.transport.retry_enabled is False
    assert runtime.transport.fallback_enabled is False
    assert runtime.generic_authorization_model == (
        "OFFLINE_DENY_ONLY"
    )


def test_runtime_and_transport_repr_are_secret_free():
    (
        authority,
        runtime,
        resolver,
        executor,
        normalizer,
    ) = _runtime()

    text = repr(runtime) + repr(runtime.transport)

    assert "opaque-key-id" not in text
    assert "opaque-key-material" not in text
    assert "twilio.api_key_secret" not in text
    assert "twilio.api_key_sid" not in text

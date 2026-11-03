from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol, runtime_checkable

from core.secrets.ports import (
    EphemeralSecretLease,
    SecretReference,
    SecretResolverPort,
)
from core.shopping.adapters.twilio_authenticated_read_secret_delivery import (
    TwilioCredentialReferences,
)
from core.shopping.adapters.twilio_verify_read import (
    TWILIO_PROVIDER_SOURCE,
    TwilioReadRequestSpec,
)
from core.shopping.governance.twilio_authenticated_read_authority import (
    TwilioAuthenticatedReadRequest,
)
from core.shopping.ports.provider_activation import ProviderOperation
from core.shopping.ports.provider_authenticated_read import (
    ProviderReadResult,
)
from core.shopping.adapters.twilio_authenticated_read_secret_composition import (
    TwilioAuthenticatedReadSecretComposition,
)


_REASONS = frozenset(
    {
        "AUTHORIZATION_REJECTED",
        "INVALID_REQUEST",
        "INVALID_RESOURCE_BINDING",
        "SECRET_RESOLUTION_FAILED",
        "SECRET_LEASE_FAILED",
        "OFFLINE_EXECUTOR_FAILED",
        "NORMALIZATION_FAILED",
        "NORMALIZED_RESULT_BINDING_REJECTED",
    }
)


class TwilioOfflineReadExecutionError(RuntimeError):
    """Bounded C5-C3C0 failure with no provider or secret payload."""

    __slots__ = ("reason_code",)

    def __init__(self, reason_code: str) -> None:
        if reason_code not in _REASONS:
            reason_code = "INVALID_REQUEST"
        self.reason_code = reason_code
        super().__init__(reason_code)

    def __repr__(self) -> str:
        return (
            "TwilioOfflineReadExecutionError("
            f"{self.reason_code!r})"
        )


@dataclass(frozen=True)
class TwilioOfflineHttpObservation:
    """Raw fake-provider observation contained inside this adapter."""

    status_code: int
    payload: Mapping[str, object]

    def __post_init__(self) -> None:
        if (
            type(self.status_code) is not int
            or not 100 <= self.status_code <= 599
        ):
            raise ValueError("offline observation is invalid")
        if not isinstance(self.payload, Mapping):
            raise TypeError("offline observation is invalid")

    def __repr__(self) -> str:
        return (
            "TwilioOfflineHttpObservation("
            f"status_code={self.status_code!r}, payload=<redacted>)"
        )


@runtime_checkable
class TwilioOfflineHttpGetExecutor(Protocol):
    """Injected fake GET seam. It has no network implementation."""

    def get(
        self,
        request: TwilioReadRequestSpec,
        *,
        api_key_sid: str | bytes,
        api_key_secret: str | bytes,
    ) -> TwilioOfflineHttpObservation:
        ...


@runtime_checkable
class TwilioOfflineObservationNormalizer(Protocol):
    """Provider adapter normalization seam."""

    def normalize(
        self,
        *,
        request: TwilioAuthenticatedReadRequest,
        request_spec: TwilioReadRequestSpec,
        observation: TwilioOfflineHttpObservation,
    ) -> ProviderReadResult:
        ...


def _sid_value(value: object) -> str:
    raw = getattr(value, "value", None)
    if type(raw) is not str or not raw:
        raise TwilioOfflineReadExecutionError(
            "INVALID_RESOURCE_BINDING"
        )
    return raw


def build_twilio_offline_read_request_spec(
    request: TwilioAuthenticatedReadRequest,
) -> TwilioReadRequestSpec:
    if type(request) is not TwilioAuthenticatedReadRequest:
        raise TwilioOfflineReadExecutionError(
            "INVALID_REQUEST"
        )

    service_sid = _sid_value(request.service_sid)

    if request.operation is ProviderOperation.READ_HEALTH:
        if request.verification_sid is not None:
            raise TwilioOfflineReadExecutionError(
                "INVALID_RESOURCE_BINDING"
            )
        path = f"/v2/Services/{service_sid}"

    elif request.operation is ProviderOperation.READ_EVIDENCE:
        if request.verification_sid is None:
            raise TwilioOfflineReadExecutionError(
                "INVALID_RESOURCE_BINDING"
            )
        verification_sid = _sid_value(
            request.verification_sid
        )
        path = (
            f"/v2/Services/{service_sid}"
            f"/Verifications/{verification_sid}"
        )

    else:
        raise TwilioOfflineReadExecutionError(
            "INVALID_REQUEST"
        )

    try:
        return TwilioReadRequestSpec(
            operation=request.operation,
            method="GET",
            path=path,
        )
    except Exception:
        raise TwilioOfflineReadExecutionError(
            "INVALID_RESOURCE_BINDING"
        ) from None


class TwilioOfflineAuthenticatedReadTransport:
    """
    Authorization-first C5-C3C0 provider-specific transport.

    This object has no production network implementation.
    """

    __slots__ = (
        "_secret_composition",
        "_secret_resolver",
        "_executor",
        "_normalizer",
    )

    def __init__(
        self,
        *,
        secret_composition: TwilioAuthenticatedReadSecretComposition,
        secret_resolver: SecretResolverPort,
        executor: TwilioOfflineHttpGetExecutor,
        normalizer: TwilioOfflineObservationNormalizer,
    ) -> None:
        if (
            type(secret_composition)
            is not TwilioAuthenticatedReadSecretComposition
        ):
            raise TypeError(
                "offline secret composition is required"
            )
        if not isinstance(
            secret_resolver,
            SecretResolverPort,
        ):
            raise TypeError(
                "secret resolver port is required"
            )
        if not isinstance(
            executor,
            TwilioOfflineHttpGetExecutor,
        ):
            raise TypeError(
                "offline GET executor is required"
            )
        if not isinstance(
            normalizer,
            TwilioOfflineObservationNormalizer,
        ):
            raise TypeError(
                "offline observation normalizer is required"
            )

        self._secret_composition = secret_composition
        self._secret_resolver = secret_resolver
        self._executor = executor
        self._normalizer = normalizer

    @staticmethod
    def _references(
        credentials: TwilioCredentialReferences,
    ) -> tuple[SecretReference, SecretReference]:
        if type(credentials) is not TwilioCredentialReferences:
            raise TwilioOfflineReadExecutionError(
                "SECRET_RESOLUTION_FAILED"
            )

        sid_ref = getattr(
            credentials,
            "api_key_sid_reference",
            None,
        )
        secret_ref = getattr(
            credentials,
            "api_key_secret_reference",
            None,
        )

        if (
            type(sid_ref) is not SecretReference
            or type(secret_ref) is not SecretReference
        ):
            raise TwilioOfflineReadExecutionError(
                "SECRET_RESOLUTION_FAILED"
            )

        return sid_ref, secret_ref

    def execute(
        self,
        request: TwilioAuthenticatedReadRequest,
        *,
        capability: object | None,
    ) -> ProviderReadResult:
        if type(request) is not TwilioAuthenticatedReadRequest:
            raise TwilioOfflineReadExecutionError(
                "INVALID_REQUEST"
            )

        request_spec = build_twilio_offline_read_request_spec(
            request
        )

        preparation = self._secret_composition.prepare(
            request,
            capability=capability,
        )

        if not preparation.authorization.allowed:
            raise TwilioOfflineReadExecutionError(
                "AUTHORIZATION_REJECTED"
            )

        plan = preparation.plan
        if plan is None:
            raise TwilioOfflineReadExecutionError(
                "AUTHORIZATION_REJECTED"
            )

        credentials = getattr(plan, "credentials", None)
        sid_ref, secret_ref = self._references(
            credentials
        )

        try:
            sid_lease = self._secret_resolver.resolve(
                sid_ref
            )
            secret_lease = self._secret_resolver.resolve(
                secret_ref
            )
        except Exception:
            raise TwilioOfflineReadExecutionError(
                "SECRET_RESOLUTION_FAILED"
            ) from None

        if (
            type(sid_lease) is not EphemeralSecretLease
            or type(secret_lease) is not EphemeralSecretLease
        ):
            raise TwilioOfflineReadExecutionError(
                "SECRET_RESOLUTION_FAILED"
            )

        api_key_sid: str | bytes | None = None
        api_key_secret: str | bytes | None = None

        try:
            try:
                api_key_sid = sid_lease.consume()
                api_key_secret = secret_lease.consume()
            except Exception:
                raise TwilioOfflineReadExecutionError(
                    "SECRET_LEASE_FAILED"
                ) from None

            try:
                observation = self._executor.get(
                    request_spec,
                    api_key_sid=api_key_sid,
                    api_key_secret=api_key_secret,
                )
            except Exception:
                raise TwilioOfflineReadExecutionError(
                    "OFFLINE_EXECUTOR_FAILED"
                ) from None

        finally:
            api_key_sid = None
            api_key_secret = None

        if type(observation) is not TwilioOfflineHttpObservation:
            raise TwilioOfflineReadExecutionError(
                "OFFLINE_EXECUTOR_FAILED"
            )

        try:
            result = self._normalizer.normalize(
                request=request,
                request_spec=request_spec,
                observation=observation,
            )
        except Exception:
            raise TwilioOfflineReadExecutionError(
                "NORMALIZATION_FAILED"
            ) from None

        if type(result) is not ProviderReadResult:
            raise TwilioOfflineReadExecutionError(
                "NORMALIZATION_FAILED"
            )

        if (
            str(result.provider_source)
            != TWILIO_PROVIDER_SOURCE
            or result.operation is not request.operation
            or result.identity != request.identity
        ):
            raise TwilioOfflineReadExecutionError(
                "NORMALIZED_RESULT_BINDING_REJECTED"
            )

        return result

    @property
    def network_enabled(self) -> bool:
        return False

    @property
    def max_attempts(self) -> int:
        return 1

    @property
    def retry_enabled(self) -> bool:
        return False

    @property
    def fallback_enabled(self) -> bool:
        return False

    def __repr__(self) -> str:
        return (
            "TwilioOfflineAuthenticatedReadTransport("
            "network_enabled=False, max_attempts=1, "
            "secrets=<redacted>)"
        )

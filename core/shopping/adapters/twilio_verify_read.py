from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import re

from core.shopping.ports.provider_activation import (
    ProviderOperation,
    ProviderRequestIdentity,
)
from core.shopping.ports.provider_authenticated_read import (
    ProviderReadResult,
    ProviderReadStatus,
)


TWILIO_PROVIDER_SOURCE = "twilio.verify.v2"

_SERVICE_SID_RE = re.compile(r"VA[0-9A-Fa-f]{32}\Z")
_VERIFICATION_SID_RE = re.compile(r"VE[0-9A-Fa-f]{32}\Z")

_SERVICE_PATH_RE = re.compile(
    r"/v2/Services/VA[0-9A-Fa-f]{32}\Z"
)
_VERIFICATION_PATH_RE = re.compile(
    r"/v2/Services/VA[0-9A-Fa-f]{32}"
    r"/Verifications/VE[0-9A-Fa-f]{32}\Z"
)


class TwilioVerifyReadError(RuntimeError):
    _ALLOWED = frozenset({
        "INVALID_SERVICE_SID",
        "INVALID_VERIFICATION_SID",
        "INVALID_REQUEST_SPEC",
        "INVALID_RESPONSE",
        "INVALID_TRANSPORT_FAILURE",
    })

    def __init__(self, reason_code: str) -> None:
        code = (
            reason_code
            if type(reason_code) is str and reason_code in self._ALLOWED
            else "INVALID_RESPONSE"
        )
        self.reason_code = code
        super().__init__(code)

    def __repr__(self) -> str:
        return (
            "TwilioVerifyReadError("
            f"reason_code={self.reason_code!r})"
        )


@dataclass(frozen=True, slots=True)
class TwilioServiceSid:
    value: str

    def __post_init__(self) -> None:
        if (
            type(self.value) is not str
            or _SERVICE_SID_RE.fullmatch(self.value) is None
        ):
            raise TwilioVerifyReadError("INVALID_SERVICE_SID")

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return "TwilioServiceSid(<bounded>)"


@dataclass(frozen=True, slots=True)
class TwilioVerificationSid:
    value: str

    def __post_init__(self) -> None:
        if (
            type(self.value) is not str
            or _VERIFICATION_SID_RE.fullmatch(self.value) is None
        ):
            raise TwilioVerifyReadError(
                "INVALID_VERIFICATION_SID"
            )

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return "TwilioVerificationSid(<bounded>)"


@dataclass(frozen=True, slots=True)
class TwilioReadRequestSpec:
    operation: ProviderOperation
    method: str
    path: str

    def __post_init__(self) -> None:
        if type(self.operation) is not ProviderOperation:
            raise TwilioVerifyReadError(
                "INVALID_REQUEST_SPEC"
            )

        if self.operation not in {
            ProviderOperation.READ_HEALTH,
            ProviderOperation.READ_EVIDENCE,
        }:
            raise TwilioVerifyReadError(
                "INVALID_REQUEST_SPEC"
            )

        if self.method != "GET":
            raise TwilioVerifyReadError(
                "INVALID_REQUEST_SPEC"
            )

        if type(self.path) is not str:
            raise TwilioVerifyReadError(
                "INVALID_REQUEST_SPEC"
            )

        if any(token in self.path for token in ("?", "#", "://", "..")):
            raise TwilioVerifyReadError(
                "INVALID_REQUEST_SPEC"
            )

        if self.operation is ProviderOperation.READ_HEALTH:
            valid = _SERVICE_PATH_RE.fullmatch(self.path)
        else:
            valid = _VERIFICATION_PATH_RE.fullmatch(
                self.path
            )

        if valid is None:
            raise TwilioVerifyReadError(
                "INVALID_REQUEST_SPEC"
            )

    def __repr__(self) -> str:
        return (
            "TwilioReadRequestSpec("
            f"operation={self.operation.value!r}, "
            "method='GET', path=<bounded>)"
        )


class TwilioVerificationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    CANCELED = "canceled"
    MAX_ATTEMPTS_REACHED = "max_attempts_reached"
    DELETED = "deleted"
    FAILED = "failed"
    EXPIRED = "expired"


class TwilioTransportFailure(str, Enum):
    TIMEOUT = "TIMEOUT"
    CONNECTION_LOST = "CONNECTION_LOST"
    UNCERTAIN_RESPONSE = "UNCERTAIN_RESPONSE"


@dataclass(frozen=True, slots=True)
class TwilioVerificationEvidence:
    read_result: ProviderReadResult
    provider_status: TwilioVerificationStatus | None

    def __post_init__(self) -> None:
        if type(self.read_result) is not ProviderReadResult:
            raise TypeError("provider read result is required")

        if (
            self.read_result.operation
            is not ProviderOperation.READ_EVIDENCE
        ):
            raise ValueError(
                "verification evidence requires READ_EVIDENCE"
            )

        if (
            self.provider_status is not None
            and type(self.provider_status)
            is not TwilioVerificationStatus
        ):
            raise TypeError(
                "provider status is invalid"
            )

    def to_log_dict(self) -> dict[str, object]:
        result = self.read_result.to_log_dict()

        if self.provider_status is not None:
            result["provider_status"] = (
                self.provider_status.value
            )

        return result

    def __repr__(self) -> str:
        return (
            "TwilioVerificationEvidence("
            "<bounded normalized evidence>)"
        )


def build_service_read_request(
    service_sid: TwilioServiceSid,
) -> TwilioReadRequestSpec:
    if type(service_sid) is not TwilioServiceSid:
        raise TwilioVerifyReadError(
            "INVALID_SERVICE_SID"
        )

    return TwilioReadRequestSpec(
        operation=ProviderOperation.READ_HEALTH,
        method="GET",
        path=f"/v2/Services/{service_sid}",
    )


def build_verification_read_request(
    service_sid: TwilioServiceSid,
    verification_sid: TwilioVerificationSid,
) -> TwilioReadRequestSpec:
    if type(service_sid) is not TwilioServiceSid:
        raise TwilioVerifyReadError(
            "INVALID_SERVICE_SID"
        )

    if type(verification_sid) is not TwilioVerificationSid:
        raise TwilioVerifyReadError(
            "INVALID_VERIFICATION_SID"
        )

    return TwilioReadRequestSpec(
        operation=ProviderOperation.READ_EVIDENCE,
        method="GET",
        path=(
            f"/v2/Services/{service_sid}"
            f"/Verifications/{verification_sid}"
        ),
    )


def _read_result(
    *,
    operation: ProviderOperation,
    identity: ProviderRequestIdentity,
    status: ProviderReadStatus,
    observed_at: datetime,
    verification_sid: TwilioVerificationSid | None = None,
) -> ProviderReadResult:
    if type(identity) is not ProviderRequestIdentity:
        raise TypeError("request identity is invalid")

    provider_verification_id = (
        str(verification_sid)
        if verification_sid is not None
        else None
    )

    return ProviderReadResult(
        provider_source=TWILIO_PROVIDER_SOURCE,
        operation=operation,
        identity=identity,
        status=status,
        observed_at=observed_at,
        provider_verification_id=provider_verification_id,
    )


def normalize_service_response(
    *,
    http_status: int,
    payload: Mapping[str, object] | None,
    expected_sid: TwilioServiceSid,
    identity: ProviderRequestIdentity,
    observed_at: datetime,
) -> ProviderReadResult:
    if type(http_status) is not int:
        raise TwilioVerifyReadError(
            "INVALID_RESPONSE"
        )

    if type(expected_sid) is not TwilioServiceSid:
        raise TwilioVerifyReadError(
            "INVALID_SERVICE_SID"
        )

    if http_status == 200:
        valid = (
            isinstance(payload, Mapping)
            and type(payload.get("sid")) is str
            and payload.get("sid") == str(expected_sid)
        )

        status = (
            ProviderReadStatus.HEALTHY
            if valid
            else ProviderReadStatus.MALFORMED
        )

    elif http_status == 404:
        status = ProviderReadStatus.NOT_FOUND

    elif http_status == 429 or 500 <= http_status <= 599:
        status = ProviderReadStatus.UNAVAILABLE

    else:
        status = ProviderReadStatus.UNAVAILABLE

    return _read_result(
        operation=ProviderOperation.READ_HEALTH,
        identity=identity,
        status=status,
        observed_at=observed_at,
    )


def normalize_verification_response(
    *,
    http_status: int,
    payload: Mapping[str, object] | None,
    expected_sid: TwilioVerificationSid,
    identity: ProviderRequestIdentity,
    observed_at: datetime,
) -> TwilioVerificationEvidence:
    if type(http_status) is not int:
        raise TwilioVerifyReadError(
            "INVALID_RESPONSE"
        )

    if type(expected_sid) is not TwilioVerificationSid:
        raise TwilioVerifyReadError(
            "INVALID_VERIFICATION_SID"
        )

    provider_status = None

    if http_status == 200:
        valid_payload = (
            isinstance(payload, Mapping)
            and type(payload.get("sid")) is str
            and payload.get("sid") == str(expected_sid)
            and type(payload.get("status")) is str
        )

        if valid_payload:
            try:
                provider_status = TwilioVerificationStatus(
                    payload["status"]
                )
            except ValueError:
                provider_status = None
                read_status = ProviderReadStatus.MALFORMED
            else:
                read_status = ProviderReadStatus.AVAILABLE
        else:
            read_status = ProviderReadStatus.MALFORMED

    elif http_status == 404:
        read_status = ProviderReadStatus.NOT_FOUND

    elif http_status == 429 or 500 <= http_status <= 599:
        read_status = ProviderReadStatus.UNAVAILABLE

    else:
        read_status = ProviderReadStatus.UNAVAILABLE

    verification_id = (
        expected_sid
        if read_status is ProviderReadStatus.AVAILABLE
        else None
    )

    result = _read_result(
        operation=ProviderOperation.READ_EVIDENCE,
        identity=identity,
        status=read_status,
        observed_at=observed_at,
        verification_sid=verification_id,
    )

    return TwilioVerificationEvidence(
        read_result=result,
        provider_status=provider_status,
    )


def normalize_transport_failure(
    *,
    operation: ProviderOperation,
    failure: TwilioTransportFailure,
    identity: ProviderRequestIdentity,
    observed_at: datetime,
) -> ProviderReadResult:
    if type(failure) is not TwilioTransportFailure:
        raise TwilioVerifyReadError(
            "INVALID_TRANSPORT_FAILURE"
        )

    if operation not in {
        ProviderOperation.READ_HEALTH,
        ProviderOperation.READ_EVIDENCE,
    }:
        raise TwilioVerifyReadError(
            "INVALID_TRANSPORT_FAILURE"
        )

    return _read_result(
        operation=operation,
        identity=identity,
        status=ProviderReadStatus.UNKNOWN_OUTCOME,
        observed_at=observed_at,
    )

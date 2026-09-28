"""Dedicated, provider-neutral C4 reconciliation port.

The capability below is an authorization object, not actor metadata.  A
caller must possess it both when constructing and when invoking the dedicated
reconciliation service; ordinary phone verification has no such authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Literal, Protocol, runtime_checkable

from pydantic import AliasChoices, ConfigDict, Field, model_validator

from core.shopping.customer_identity import ClosedContract, UTCTimestamp
from core.shopping.ports.phone_verification import (
    ChallengeReference, ChallengeStatus, ProviderSourceIdentifier,
    ProviderVerificationIdentifier, ReplayReference,
)


_REF = r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,158}[A-Za-z0-9]$|^[A-Za-z0-9]$"


class ReconciliationOperation(str, Enum):
    START = "START"
    VERIFY = "VERIFY"


class QuarantineStatus(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class StartReconciliationStatus(str, Enum):
    STARTED = "STARTED"
    PENDING = "PENDING"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class VerifyReconciliationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"


class _ReconciliationContract(ClosedContract):
    model_config = ConfigDict(
        extra="forbid", frozen=True, validate_default=True,
        revalidate_instances="always", hide_input_in_errors=True,
    )


class ReconciliationActor(_ReconciliationContract):
    """Audit metadata only; it does not confer reconciliation authority."""

    actor_ref: str = Field(strict=True, min_length=1, max_length=160, pattern=_REF)
    correlation_id: str = Field(strict=True, min_length=1, max_length=160, pattern=_REF)


class VerificationReconciliationCapability:
    """Opaque capability issued by the internal control-plane boundary."""

    __slots__ = ("_nonce",)
    _PREFIX = "shopping-verification-reconciliation/v1"
    _ISSUANCE_TOKEN = object()

    def __init__(self, nonce: object = None) -> None:
        if nonce is not self._ISSUANCE_TOKEN:
            raise TypeError("reconciliation capability is not caller-constructible")
        self._nonce = self._PREFIX

    @classmethod
    def issue(cls) -> "VerificationReconciliationCapability":
        return cls(cls._ISSUANCE_TOKEN)

    # Explicit test/in-process spelling; this still creates the same opaque
    # capability and carries no actor or provider data.
    issue_for_internal_use = issue


ReconciliationAuthorizationCapability = VerificationReconciliationCapability
VerificationReconciliationAuthorization = VerificationReconciliationCapability


class StartReconciliationCommand(_ReconciliationContract):
    operation: Literal[ReconciliationOperation.START] = ReconciliationOperation.START
    command_id: str = Field(strict=True, min_length=1, max_length=160, pattern=_REF)
    challenge_reference: ChallengeReference
    replay_reference: ReplayReference
    expected_challenge_version: int = Field(
        validation_alias=AliasChoices("expected_challenge_version", "challenge_version", "expected_version"),
        strict=True, ge=0,
    )
    expected_quarantine_version: int = Field(
        validation_alias=AliasChoices("expected_quarantine_version", "quarantine_version"),
        strict=True, ge=1,
    )
    provider_source: ProviderSourceIdentifier
    status: StartReconciliationStatus = Field(
        validation_alias=AliasChoices("status", "provider_status", "outcome"),
    )
    provider_verification_id: ProviderVerificationIdentifier | None = None
    started_at: UTCTimestamp | None = Field(default=None, validation_alias=AliasChoices("started_at", "provider_started_at"))
    provider_expires_at: UTCTimestamp | None = None
    actor_ref: str = Field(strict=True, min_length=1, max_length=160, pattern=_REF)
    correlation_id: str = Field(strict=True, min_length=1, max_length=160, pattern=_REF)
    actor: ReconciliationActor | None = None

    @model_validator(mode="before")
    @classmethod
    def flatten_actor_metadata(cls, value: object) -> object:
        if isinstance(value, dict):
            value = dict(value)
            for key, contract in (("challenge_reference", ChallengeReference),
                                  ("replay_reference", ReplayReference),
                                  ("provider_source", ProviderSourceIdentifier),
                                  ("provider_verification_id", ProviderVerificationIdentifier)):
                if type(value.get(key)) is str:
                    value[key] = contract(value=value[key])
        if isinstance(value, dict) and isinstance(value.get("actor"), dict):
            value = dict(value)
            value["actor"] = ReconciliationActor.model_validate(value["actor"])
        if isinstance(value, dict) and isinstance(value.get("actor"), ReconciliationActor):
            value = dict(value)
            value.setdefault("actor_ref", value["actor"].actor_ref)
            value.setdefault("correlation_id", value["actor"].correlation_id)
        return value


class VerifyReconciliationCommand(_ReconciliationContract):
    operation: Literal[ReconciliationOperation.VERIFY] = ReconciliationOperation.VERIFY
    command_id: str = Field(strict=True, min_length=1, max_length=160, pattern=_REF)
    challenge_reference: ChallengeReference
    replay_reference: ReplayReference
    expected_challenge_version: int = Field(
        validation_alias=AliasChoices("expected_challenge_version", "challenge_version", "expected_version"),
        strict=True, ge=0,
    )
    expected_quarantine_version: int = Field(
        validation_alias=AliasChoices("expected_quarantine_version", "quarantine_version"),
        strict=True, ge=1,
    )
    provider_source: ProviderSourceIdentifier
    provider_verification_id: ProviderVerificationIdentifier
    status: VerifyReconciliationStatus = Field(
        validation_alias=AliasChoices("status", "provider_status", "outcome"),
    )
    verified_at: UTCTimestamp | None = Field(default=None, validation_alias=AliasChoices("verified_at", "provider_verified_at"))
    provider_expires_at: UTCTimestamp | None = None
    actor_ref: str = Field(strict=True, min_length=1, max_length=160, pattern=_REF)
    correlation_id: str = Field(strict=True, min_length=1, max_length=160, pattern=_REF)
    actor: ReconciliationActor | None = None

    @model_validator(mode="before")
    @classmethod
    def flatten_actor_metadata(cls, value: object) -> object:
        if isinstance(value, dict):
            value = dict(value)
            for key, contract in (("challenge_reference", ChallengeReference),
                                  ("replay_reference", ReplayReference),
                                  ("provider_source", ProviderSourceIdentifier),
                                  ("provider_verification_id", ProviderVerificationIdentifier)):
                if type(value.get(key)) is str:
                    value[key] = contract(value=value[key])
        if isinstance(value, dict) and isinstance(value.get("actor"), dict):
            value = dict(value)
            value["actor"] = ReconciliationActor.model_validate(value["actor"])
        if isinstance(value, dict) and isinstance(value.get("actor"), ReconciliationActor):
            value = dict(value)
            value.setdefault("actor_ref", value["actor"].actor_ref)
            value.setdefault("correlation_id", value["actor"].correlation_id)
        return value


@dataclass(frozen=True)
class ReconciliationResult:
    """Durable result projection returned by the dedicated service."""

    challenge_reference: ChallengeReference
    lifecycle: ChallengeStatus
    status: str
    challenge_version: int
    quarantine_version: int
    command_id: str
    replayed: bool = False
    start_evidence: object | None = None
    verification_outcome: object | None = None
    attempt_id: str | None = None
    receipt_id: str | None = None

    @property
    def outcome(self) -> str:
        return self.status

    @property
    def start_result(self) -> object | None:
        return self.start_evidence

    @property
    def verification(self) -> object | None:
        return self.verification_outcome

    @property
    def receipt(self) -> object | None:
        value = self.verification_outcome
        return None if value is None else getattr(value, "receipt", None)

    @property
    def context(self) -> object | None:
        value = self.verification_outcome
        return None if value is None else getattr(value, "context", None)


@runtime_checkable
class PhoneVerificationReconciliationPort(Protocol):
    def reconcile_start(
        self,
        command: StartReconciliationCommand,
        *,
        capability: VerificationReconciliationCapability,
    ) -> ReconciliationResult:
        ...

    def reconcile_verify(
        self,
        command: VerifyReconciliationCommand,
        *,
        capability: VerificationReconciliationCapability,
    ) -> ReconciliationResult:
        ...


# Concise aliases for callers that use the term command/evidence explicitly.
StartReconciliationRequest = StartReconciliationCommand
VerifyReconciliationRequest = VerifyReconciliationCommand
ReconciliationAuthorization = VerificationReconciliationCapability
ReconcileStartCommand = StartReconciliationCommand
ReconcileVerifyCommand = VerifyReconciliationCommand
StartReconciliationEvidence = StartReconciliationCommand
VerifyReconciliationEvidence = VerifyReconciliationCommand
VerificationReconciliationCommand = StartReconciliationCommand
VerificationReconciliationPort = PhoneVerificationReconciliationPort


__all__ = [
    "ReconciliationOperation", "QuarantineStatus", "StartReconciliationStatus",
    "VerifyReconciliationStatus", "ReconciliationActor",
    "VerificationReconciliationCapability", "ReconciliationAuthorizationCapability",
    "VerificationReconciliationAuthorization", "StartReconciliationCommand",
    "VerifyReconciliationCommand", "ReconciliationResult",
    "PhoneVerificationReconciliationPort", "StartReconciliationRequest",
    "VerifyReconciliationRequest", "ReconciliationAuthorization",
    "ReconcileStartCommand", "ReconcileVerifyCommand",
    "StartReconciliationEvidence", "VerifyReconciliationEvidence",
    "VerificationReconciliationCommand", "VerificationReconciliationPort",
]

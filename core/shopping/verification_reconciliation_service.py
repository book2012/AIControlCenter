"""Durable C4 reconciliation authority for quarantined provider outcomes."""
from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import re
import sqlite3
from pathlib import Path
from typing import Callable
import uuid

from core.shopping.customer_auth import (
    ReceiptLifecycle, TrustedReceiptBinding, TrustedVerificationContext,
    TrustedVerificationReceipt, TrustedVerificationSeam, VerificationPurpose,
    validate_trusted_receipt,
)
from core.shopping.customer_identity import require_utc
from core.shopping.customer_persistence import (
    BUSY_TIMEOUT_MS, PersistenceError, SQLiteVerificationRepository, _utc,
)
from core.shopping.phone_normalization import OpaquePhoneBinding
from core.shopping.ports.phone_verification import (
    ChallengeReference, ChallengeStartResult, ChallengeStatus,
    ChallengeVerificationRequest, ChallengeVerificationResult,
    ProviderSourceIdentifier, ProviderVerificationIdentifier, ReplayReference,
    VerificationStatus,
)
from core.shopping.ports.phone_verification_reconciliation import (
    ReconciliationResult, StartReconciliationCommand,
    StartReconciliationStatus, ReconciliationAuthorizationCapability,
    VerificationReconciliationCapability,
    VerifyReconciliationCommand, VerifyReconciliationStatus,
)
from core.shopping.phone_verification_service import (
    PhoneVerificationRejected, TrustedPhoneVerification, _dt, _uuid4_shaped,
)


class VerificationReconciliationError(RuntimeError):
    """Sanitized fail-closed reconciliation error."""


class ReconciliationAuthorizationError(VerificationReconciliationError):
    pass


class ReconciliationConflict(VerificationReconciliationError):
    pass


_OPAQUE = re.compile(r"^AG-[A-Z]{3}-[0-9a-f]{12}4[0-9a-f]{3}[89ab][0-9a-f]{15}$")


def _as_ref(value: object, kind: type) -> object:
    if isinstance(value, kind):
        return value
    if type(value) is str:
        return kind(value=value)
    raise ValueError("reconciliation reference is invalid")


class VerificationReconciliationService:
    """Only C4's dedicated service can consume an OPEN quarantine."""

    def __init__(
        self,
        repository: SQLiteVerificationRepository | None = None,
        authorization: VerificationReconciliationCapability | None = None,
        *,
        capability: VerificationReconciliationCapability | None = None,
        authorization_capability: VerificationReconciliationCapability | None = None,
        database_path: str | Path | None = None,
        utc_clock: Callable[[], datetime] | None = None,
        clock: Callable[[], datetime] | None = None,
        evidence_max_age: timedelta = timedelta(minutes=5),
        issuer_ref: str | None = None,
        event_id_factory: Callable[[], str] | None = None,
        audit_failure_hook: Callable[[str], None] | None = None,
        busy_timeout_ms: int = BUSY_TIMEOUT_MS,
    ) -> None:
        supplied_capabilities = tuple(
            value for value in (authorization, capability, authorization_capability)
            if value is not None
        )
        if any(type(value) is not VerificationReconciliationCapability for value in supplied_capabilities):
            raise ReconciliationAuthorizationError("reconciliation capability is required")
        if supplied_capabilities and any(value is not supplied_capabilities[0] for value in supplied_capabilities[1:]):
            raise ReconciliationAuthorizationError("reconciliation capability is invalid")
        capability = supplied_capabilities[0] if supplied_capabilities else None
        if type(capability) is not VerificationReconciliationCapability:
            raise ReconciliationAuthorizationError("reconciliation capability is required")
        if repository is not None and database_path is not None:
            raise ValueError("choose a verification repository or database path")
        if repository is None:
            if database_path is None:
                raise ValueError("a provisioned verification repository is required")
            repository = SQLiteVerificationRepository(database_path, busy_timeout_ms=busy_timeout_ms)
        utc_clock = utc_clock if utc_clock is not None else clock
        if not callable(utc_clock):
            raise TypeError("an injected UTC clock is required")
        if type(evidence_max_age) is not timedelta or not timedelta(0) < evidence_max_age:
            raise ValueError("evidence age is invalid")
        if issuer_ref is None:
            issuer_ref = _uuid4_shaped("AG-ISS-", "reconciliation-issuer")
        if type(issuer_ref) is not str or _OPAQUE.fullmatch(issuer_ref) is None:
            raise ValueError("issuer reference is invalid")
        self._repository = repository
        self.database_path = str(repository.database_path)
        self._capability = capability
        self._clock = utc_clock
        self._evidence_max_age = evidence_max_age
        self._issuer_ref = issuer_ref
        self._event_id_factory = event_id_factory or (lambda: "AG-REC-" + uuid.uuid4().hex)
        self._audit_failure_hook = audit_failure_hook

    def _require_capability(self, capability: object | None) -> None:
        if type(self._capability) is not VerificationReconciliationCapability:
            raise ReconciliationAuthorizationError("reconciliation capability is required")
        if type(capability) is not VerificationReconciliationCapability:
            raise ReconciliationAuthorizationError("reconciliation capability is required")
        if capability is not self._capability:
            raise ReconciliationAuthorizationError("reconciliation capability is invalid")

    def _invocation_capability(
        self,
        capability: object | None,
        authorization: object | None,
    ) -> object | None:
        if capability is not None and authorization is not None and capability is not authorization:
            raise ReconciliationAuthorizationError("reconciliation capability is invalid")
        return capability if capability is not None else authorization

    def _now(self) -> datetime:
        try:
            return require_utc(self._clock())
        except (TypeError, ValueError, AttributeError, OverflowError):
            raise VerificationReconciliationError("reconciliation clock rejected") from None

    @staticmethod
    def _reject_future_evidence(command: object, now: datetime) -> None:
        for field in ("started_at", "verified_at"):
            evidence_at = getattr(command, field, None)
            if evidence_at is not None and evidence_at > now:
                raise VerificationReconciliationError("reconciliation evidence timestamp rejected")

    def _open(self) -> sqlite3.Connection:
        try:
            return self._repository.open()
        except (PersistenceError, sqlite3.Error, OSError):
            raise VerificationReconciliationError("verification storage unavailable") from None

    def _audit(self, connection: sqlite3.Connection, *, customer: str, challenge: str,
               actor: str, correlation: str, now: datetime, outcome: str) -> None:
        if self._audit_failure_hook is not None:
            try:
                self._audit_failure_hook("PHONE_VERIFICATION_RECONCILIATION")
            except Exception:
                raise VerificationReconciliationError("reconciliation audit persistence failed") from None
        try:
            connection.execute(
                "INSERT INTO shopping_auth_audit(event_id,actor_ref,resource_ref,action,outcome,correlation_id,occurred_at) VALUES(?,?,?,?,?,?,?)",
                (self._event_id_factory(), actor, challenge,
                 "PHONE_VERIFICATION_RECONCILIATION", outcome, correlation, _utc(now)),
            )
        except sqlite3.Error:
            raise VerificationReconciliationError("reconciliation audit persistence failed") from None

    @staticmethod
    def _challenge(connection: sqlite3.Connection, reference: str) -> sqlite3.Row:
        row = connection.execute(
            "SELECT * FROM shopping_verification_challenges WHERE challenge_id=?",
            (reference,),
        ).fetchone()
        if row is None:
            raise ReconciliationConflict("unknown challenge")
        return row

    @staticmethod
    def _quarantine(connection: sqlite3.Connection, reference: str) -> sqlite3.Row:
        row = connection.execute(
            "SELECT * FROM shopping_verification_unknown_outcomes WHERE challenge_id=?",
            (reference,),
        ).fetchone()
        if row is None or row["state"] != "OPEN":
            raise ReconciliationConflict("open quarantine is required")
        return row

    @staticmethod
    def _command_event(connection: sqlite3.Connection, command_id: str) -> sqlite3.Row | None:
        return connection.execute(
            "SELECT * FROM shopping_verification_reconciliation_events WHERE command_id=?",
            (command_id,),
        ).fetchone()

    @staticmethod
    def _same_command(event: sqlite3.Row, command: object) -> bool:
        status = command.status.value
        provider_id = getattr(command, "provider_verification_id", None)
        provider_id = None if provider_id is None else str(provider_id)
        values_match = (
            event["challenge_id"] == str(command.challenge_reference)
            and event["operation"] == command.operation.value
            and event["provider_source"] == str(command.provider_source)
            and event["provider_verification_id"] == provider_id
            and event["provider_status"] == status
            and int(event["challenge_version"]) == int(command.expected_challenge_version) + 1
            and int(event["quarantine_version"]) == int(command.expected_quarantine_version) + 1
            and event["actor_ref"] == command.actor_ref
            and event["correlation_id"] == command.correlation_id
        )
        if not values_match:
            return False
        for field, column in (("started_at", "provider_started_at"),
                              ("verified_at", "provider_verified_at"),
                              ("provider_expires_at", "provider_expires_at")):
            value = getattr(command, field, None)
            stored = event[column]
            if (None if value is None else _utc(value)) != stored:
                return False
        return True

    def _replay_event(self, connection: sqlite3.Connection, event: sqlite3.Row,
                      command: object) -> ReconciliationResult:
        quarantine = connection.execute(
            "SELECT * FROM shopping_verification_unknown_outcomes WHERE quarantine_id=?",
            (event["quarantine_id"],),
        ).fetchone()
        if (
            quarantine is None
            or quarantine["challenge_id"] != str(command.challenge_reference)
            or quarantine["provider_source"] != str(command.provider_source)
            or quarantine["replay_reference"] != str(command.replay_reference)
        ):
            raise ReconciliationConflict("reconciliation command replay conflict")
        if not self._same_command(event, command):
            raise ReconciliationConflict("reconciliation command replay conflict")
        result = self._result_from_event(connection, event, replayed=True)
        return result

    def _result_from_event(self, connection: sqlite3.Connection, event: sqlite3.Row,
                           *, replayed: bool) -> ReconciliationResult:
        challenge = self._challenge(connection, event["challenge_id"])
        lifecycle = ChallengeStatus(event["to_lifecycle"])
        start_evidence = None
        verification_outcome = None
        attempt_id = receipt_id = None
        if event["operation"] == "START" and lifecycle in {ChallengeStatus.STARTED, ChallengeStatus.PENDING}:
            start_evidence = self._start_evidence(challenge)
        if event["operation"] == "VERIFY":
            attempt = connection.execute(
                "SELECT * FROM shopping_verification_attempts WHERE challenge_id=?",
                (event["challenge_id"],),
            ).fetchone()
            if attempt is not None:
                attempt_id, receipt_id = attempt["attempt_id"], attempt["receipt_id"]
                if attempt["outcome"] == VerificationStatus.SUCCESS.value:
                    verification_outcome = self._verified_outcome(connection, challenge, attempt)
        return ReconciliationResult(
            challenge_reference=ChallengeReference(value=event["challenge_id"]),
            lifecycle=lifecycle, status=event["provider_status"],
            challenge_version=int(event["challenge_version"]),
            quarantine_version=int(event["quarantine_version"]),
            command_id=event["command_id"], replayed=replayed,
            start_evidence=start_evidence, verification_outcome=verification_outcome,
            attempt_id=attempt_id, receipt_id=receipt_id,
        )

    @staticmethod
    def _start_evidence(row: sqlite3.Row) -> ChallengeStartResult:
        return ChallengeStartResult(
            provider_source=ProviderSourceIdentifier(value=row["provider_source"]),
            provider_verification_id=ProviderVerificationIdentifier(value=row["provider_verification_id"]),
            purpose=VerificationPurpose(row["purpose"]),
            challenge_reference=ChallengeReference(value=row["challenge_id"]),
            replay_reference=ReplayReference(value=row["replay_reference"]),
            phone_binding=OpaquePhoneBinding(row["phone_binding"]),
            status=ChallengeStatus(row["provider_start_status"]),
            started_at=_dt(row["provider_started_at"]),
            provider_expires_at=None if row["provider_expires_at"] is None else _dt(row["provider_expires_at"]),
        )

    def _verified_outcome(self, connection: sqlite3.Connection, challenge: sqlite3.Row,
                          attempt: sqlite3.Row) -> TrustedPhoneVerification:
        receipt_row = connection.execute(
            "SELECT * FROM shopping_trusted_receipts WHERE attempt_id=?",
            (attempt["attempt_id"],),
        ).fetchone()
        if (
            receipt_row is None
            or receipt_row["lifecycle"] != ReceiptLifecycle.ISSUED.value
            or challenge["receipt_id"] != receipt_row["receipt_id"]
            or attempt["challenge_id"] != challenge["challenge_id"]
            or attempt["outcome"] != VerificationStatus.SUCCESS.value
            or attempt["receipt_id"] != receipt_row["receipt_id"]
            or receipt_row["challenge_id"] != challenge["challenge_id"]
            or receipt_row["attempt_id"] != attempt["attempt_id"]
            or receipt_row["customer_id"] != challenge["customer_id"]
            or receipt_row["browser_challenge"] != challenge["browser_challenge"]
            or receipt_row["purpose"] != challenge["purpose"]
            or receipt_row["provider_source"] != attempt["provider_source"]
            or receipt_row["provider_verification_id"] != attempt["provider_verification_id"]
            or receipt_row["phone_binding"] != attempt["phone_binding"]
        ):
            raise ReconciliationConflict("durable verification receipt is missing")
        receipt = TrustedVerificationReceipt(
            receipt_id=receipt_row["receipt_id"], purpose=VerificationPurpose(receipt_row["purpose"]),
            browser_challenge=receipt_row["browser_challenge"], issuer_ref=receipt_row["issuer_ref"],
            customer_id=receipt_row["customer_id"], issued_at=_dt(receipt_row["issued_at"]),
            expires_at=_dt(receipt_row["expires_at"]), lifecycle=ReceiptLifecycle.ISSUED,
        )
        context = TrustedVerificationContext(accepted_bindings=frozenset({
            TrustedReceiptBinding(receipt.receipt_id, receipt.issuer_ref, receipt.customer_id),
        }))
        evidence = ChallengeVerificationResult(
            provider_source=ProviderSourceIdentifier(value=attempt["provider_source"]),
            provider_verification_id=ProviderVerificationIdentifier(value=attempt["provider_verification_id"]),
            purpose=VerificationPurpose(attempt["challenge_id"] and challenge["purpose"]),
            challenge_reference=ChallengeReference(value=challenge["challenge_id"]),
            replay_reference=ReplayReference(value=attempt["replay_reference"]),
            phone_binding=OpaquePhoneBinding(attempt["phone_binding"]),
            status=VerificationStatus.SUCCESS,
            verified_at=_dt(attempt["provider_verified_at"] or attempt["attempted_at"]),
            provider_expires_at=None if attempt["provider_expires_at"] is None else _dt(attempt["provider_expires_at"]),
        )
        outcome = TrustedPhoneVerification(
            seam=TrustedVerificationSeam(receipt=receipt, context=context),
            verification_evidence=evidence,
        )
        if validate_trusted_receipt(
            receipt, now=self._now(), expected_challenge=receipt.browser_challenge,
            context=context,
        ).value != "ACCEPTED":
            raise ReconciliationConflict("durable verification receipt is no longer valid")
        return outcome

    def _append_event(self, connection: sqlite3.Connection, *, command: object,
                      quarantine: sqlite3.Row, challenge: sqlite3.Row,
                      from_lifecycle: str, to_lifecycle: str,
                      q_version: int, c_version: int, status: str,
                      provider_id: str | None, started_at: datetime | None,
                      verified_at: datetime | None, provider_expires_at: datetime | None,
                      now: datetime, reason: str, outcome: str = "APPLIED") -> sqlite3.Row:
        event_id = self._event_id_factory()
        connection.execute(
            "INSERT INTO shopping_verification_reconciliation_events "
            "(event_id,command_id,quarantine_id,challenge_id,operation,from_lifecycle,to_lifecycle,"
            "quarantine_version,challenge_version,provider_source,provider_verification_id,provider_status,"
            "provider_started_at,provider_verified_at,provider_expires_at,actor_ref,correlation_id,"
            "occurred_at,outcome,reason_code) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (event_id, command.command_id, quarantine["quarantine_id"], challenge["challenge_id"],
             command.operation.value, from_lifecycle, to_lifecycle, q_version, c_version,
             str(command.provider_source), provider_id, status,
             None if started_at is None else _utc(started_at),
             None if verified_at is None else _utc(verified_at),
             None if provider_expires_at is None else _utc(provider_expires_at),
             command.actor_ref, command.correlation_id, _utc(now), outcome, reason),
        )
        return connection.execute(
            "SELECT * FROM shopping_verification_reconciliation_events WHERE event_id=?",
            (event_id,),
        ).fetchone()

    def _validate_versions(self, challenge: sqlite3.Row, quarantine: sqlite3.Row,
                           command: object) -> None:
        if int(challenge["version"]) != command.expected_challenge_version:
            raise ReconciliationConflict("stale challenge version")
        if int(quarantine["version"]) != command.expected_quarantine_version:
            raise ReconciliationConflict("stale quarantine version")
        if quarantine["provider_source"] != str(command.provider_source):
            raise ReconciliationConflict("reconciliation provider source conflict")
        if quarantine["replay_reference"] != str(command.replay_reference):
            raise ReconciliationConflict("reconciliation replay conflict")

    def reconcile_start(self, command: StartReconciliationCommand, *, capability: object | None = None,
                        authorization: object | None = None) -> ReconciliationResult:
        self._require_capability(self._invocation_capability(capability, authorization))
        if type(command) is not StartReconciliationCommand:
            raise VerificationReconciliationError("start reconciliation command is malformed")
        now = self._now()
        self._reject_future_evidence(command, now)
        connection = self._open()
        try:
            connection.execute("BEGIN IMMEDIATE")
            now = self._now()
            self._reject_future_evidence(command, now)
            prior = self._command_event(connection, command.command_id)
            if prior is not None:
                result = self._replay_event(connection, prior, command)
                connection.commit()
                return result
            challenge = self._challenge(connection, str(command.challenge_reference))
            quarantine = self._quarantine(connection, str(command.challenge_reference))
            self._validate_versions(challenge, quarantine, command)
            if quarantine["operation"] != "START" or challenge["status"] != ChallengeStatus.START_UNKNOWN.value:
                raise ReconciliationConflict("START quarantine is not open")
            provider_id = None if command.provider_verification_id is None else str(command.provider_verification_id)
            started_at = command.started_at
            provider_expires_at = command.provider_expires_at
            if command.status in {StartReconciliationStatus.STARTED, StartReconciliationStatus.PENDING}:
                if provider_id is None or started_at is None:
                    raise VerificationReconciliationError("accepted START evidence requires provider identity and time")
                if started_at > now or now - started_at > self._evidence_max_age:
                    raise VerificationReconciliationError("START evidence timestamp rejected")
                if now >= _dt(challenge["expires_at"]):
                    raise VerificationReconciliationError("START evidence exceeds local expiry")
                if provider_expires_at is not None and provider_expires_at <= now:
                    raise VerificationReconciliationError("START evidence is expired")
                status = command.status.value
                new_lifecycle = command.status.value
            else:
                if provider_id is not None or started_at is not None or provider_expires_at is not None:
                    raise VerificationReconciliationError("terminal START evidence cannot contain provider identity")
                status = command.status.value
                new_lifecycle = command.status.value
                provider_expires_at = started_at = None
            new_c = int(challenge["version"]) + 1
            new_q = int(quarantine["version"]) + 1
            if connection.execute(
                "UPDATE shopping_verification_challenges SET status=?,provider_challenge_reference=?,"
                "provider_verification_id=?,provider_started_at=?,provider_expires_at=?,provider_start_status=?,version=? "
                "WHERE challenge_id=? AND status=? AND version=?",
                (new_lifecycle, None,
                 provider_id, None if started_at is None else _utc(started_at),
                 None if provider_expires_at is None else _utc(provider_expires_at),
                 status if status in {"STARTED", "PENDING"} else None,
                 new_c, challenge["challenge_id"], ChallengeStatus.START_UNKNOWN.value,
                 command.expected_challenge_version),
            ).rowcount != 1:
                raise ReconciliationConflict("stale challenge version")
            if connection.execute(
                "UPDATE shopping_verification_unknown_outcomes SET state='RESOLVED',updated_at=?,version=?,challenge_version=?,last_command_id=? "
                "WHERE challenge_id=? AND state='OPEN' AND version=? AND challenge_version=?",
                (_utc(now), new_q, new_c, command.command_id, challenge["challenge_id"],
                 command.expected_quarantine_version, command.expected_challenge_version),
            ).rowcount != 1:
                raise ReconciliationConflict("stale quarantine version")
            event = self._append_event(
                connection, command=command, quarantine=quarantine, challenge=challenge,
                from_lifecycle=ChallengeStatus.START_UNKNOWN.value, to_lifecycle=new_lifecycle,
                q_version=new_q, c_version=new_c, status=status, provider_id=provider_id,
                started_at=started_at, verified_at=None, provider_expires_at=provider_expires_at,
                now=now, reason="EXPLICIT_RECONCILIATION",
            )
            self._audit(connection, customer=challenge["customer_id"], challenge=challenge["challenge_id"],
                        actor=command.actor_ref, correlation=command.correlation_id, now=now, outcome="APPLIED")
            result = self._result_from_event(connection, event, replayed=False)
            connection.commit()
            return result
        except (VerificationReconciliationError, PhoneVerificationRejected):
            if connection.in_transaction:
                connection.rollback()
            raise
        except (sqlite3.Error, PersistenceError, OSError, TypeError, ValueError):
            if connection.in_transaction:
                connection.rollback()
            raise VerificationReconciliationError("reconciliation persistence failed") from None
        finally:
            connection.close()

    def reconcile_verify(self, command: VerifyReconciliationCommand, *, capability: object | None = None,
                         authorization: object | None = None) -> ReconciliationResult:
        self._require_capability(self._invocation_capability(capability, authorization))
        if type(command) is not VerifyReconciliationCommand:
            raise VerificationReconciliationError("verify reconciliation command is malformed")
        now = self._now()
        self._reject_future_evidence(command, now)
        connection = self._open()
        try:
            connection.execute("BEGIN IMMEDIATE")
            now = self._now()
            self._reject_future_evidence(command, now)
            prior = self._command_event(connection, command.command_id)
            if prior is not None:
                result = self._replay_event(connection, prior, command)
                connection.commit()
                return result
            challenge = self._challenge(connection, str(command.challenge_reference))
            quarantine = self._quarantine(connection, str(command.challenge_reference))
            self._validate_versions(challenge, quarantine, command)
            if quarantine["operation"] != "VERIFY" or challenge["status"] != ChallengeStatus.VERIFY_UNKNOWN.value:
                raise ReconciliationConflict("VERIFY quarantine is not open")
            if challenge["provider_verification_id"] != str(command.provider_verification_id):
                raise ReconciliationConflict("provider identifier is not bound to the challenge")
            status = command.status
            if status is VerifyReconciliationStatus.VERIFIED:
                if command.verified_at is None:
                    raise VerificationReconciliationError("verification evidence timestamp rejected")
                if now - command.verified_at > self._evidence_max_age:
                    raise VerificationReconciliationError("verification evidence is too old")
                if now >= _dt(challenge["expires_at"]) or command.verified_at >= _dt(challenge["expires_at"]):
                    raise VerificationReconciliationError("verification exceeds local expiry")
                if command.provider_expires_at is not None and command.provider_expires_at <= now:
                    raise VerificationReconciliationError("verification provider evidence is expired")
            attempt_id = receipt_id = None
            if status is not VerifyReconciliationStatus.UNKNOWN:
                attempt_id = _uuid4_shaped("AG-ATT-", "reconciliation-attempt:" + str(command.replay_reference))
                receipt_id = _uuid4_shaped("AG-VRF-", "reconciliation-receipt:" + str(command.replay_reference)) if status is VerifyReconciliationStatus.VERIFIED else None
                existing_attempt = connection.execute(
                    "SELECT * FROM shopping_verification_attempts WHERE replay_reference=?",
                    (str(command.replay_reference),),
                ).fetchone()
                if existing_attempt is not None and existing_attempt["attempt_id"] != attempt_id:
                    raise ReconciliationConflict("verification replay conflict")
                if existing_attempt is not None and (
                    existing_attempt["challenge_id"] != challenge["challenge_id"]
                    or existing_attempt["provider_source"] != str(command.provider_source)
                    or existing_attempt["provider_verification_id"] != str(command.provider_verification_id)
                    or existing_attempt["phone_binding"] != challenge["phone_binding"]
                    or existing_attempt["outcome"] != (
                        VerificationStatus.SUCCESS.value
                        if status is VerifyReconciliationStatus.VERIFIED
                        else status.value
                    )
                    or (
                        status is VerifyReconciliationStatus.VERIFIED
                        and existing_attempt["receipt_id"] != receipt_id
                    )
                ):
                    raise ReconciliationConflict("verification replay conflict")
                if existing_attempt is None:
                    connection.execute(
                        "INSERT INTO shopping_verification_attempts "
                        "(attempt_id,challenge_id,replay_reference,provider_source,provider_verification_id,phone_binding,outcome,attempted_at,provider_verified_at,provider_expires_at,receipt_id) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                        (attempt_id, challenge["challenge_id"], challenge["replay_reference"],
                         str(command.provider_source), str(command.provider_verification_id), challenge["phone_binding"],
                         VerificationStatus.SUCCESS.value if status is VerifyReconciliationStatus.VERIFIED else status.value,
                         _utc(now), None if command.verified_at is None else _utc(command.verified_at),
                         None if command.provider_expires_at is None else _utc(command.provider_expires_at), receipt_id),
                    )
                    if status is VerifyReconciliationStatus.VERIFIED:
                        receipt_expires = min(_dt(challenge["expires_at"]), now + timedelta(minutes=5))
                        connection.execute(
                            "INSERT INTO shopping_trusted_receipts "
                            "(receipt_id,challenge_id,attempt_id,customer_id,issuer_ref,browser_challenge,purpose,provider_source,provider_verification_id,phone_binding,issued_at,expires_at,lifecycle,version) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,0)",
                            (receipt_id, challenge["challenge_id"], attempt_id, challenge["customer_id"], self._issuer_ref,
                             challenge["browser_challenge"], challenge["purpose"], str(command.provider_source),
                             str(command.provider_verification_id), challenge["phone_binding"], _utc(now), _utc(receipt_expires), "ISSUED"),
                        )
            new_lifecycle = (
                ChallengeStatus.VERIFY_UNKNOWN
                if status is VerifyReconciliationStatus.UNKNOWN
                else ChallengeStatus.VERIFIED
                if status is VerifyReconciliationStatus.VERIFIED
                else ChallengeStatus(status.value)
            )
            new_c = int(challenge["version"]) + 1
            new_q = int(quarantine["version"]) + 1
            if connection.execute(
                "UPDATE shopping_verification_challenges SET status=?,receipt_id=?,version=? "
                "WHERE challenge_id=? AND status=? AND version=?",
                (new_lifecycle.value, receipt_id, new_c, challenge["challenge_id"],
                 ChallengeStatus.VERIFY_UNKNOWN.value, command.expected_challenge_version),
            ).rowcount != 1:
                raise ReconciliationConflict("stale challenge version")
            if connection.execute(
                "UPDATE shopping_verification_unknown_outcomes SET state=?,updated_at=?,version=?,challenge_version=?,last_command_id=? "
                "WHERE challenge_id=? AND state='OPEN' AND version=? AND challenge_version=?",
                ("OPEN" if status is VerifyReconciliationStatus.UNKNOWN else "RESOLVED", _utc(now), new_q, new_c,
                 command.command_id, challenge["challenge_id"], command.expected_quarantine_version,
                 command.expected_challenge_version),
            ).rowcount != 1:
                raise ReconciliationConflict("stale quarantine version")
            event = self._append_event(
                connection, command=command, quarantine=quarantine, challenge=challenge,
                from_lifecycle=ChallengeStatus.VERIFY_UNKNOWN.value, to_lifecycle=new_lifecycle.value,
                q_version=new_q, c_version=new_c, status=status.value,
                provider_id=str(command.provider_verification_id), started_at=None,
                verified_at=command.verified_at, provider_expires_at=command.provider_expires_at,
                now=now, reason="EXPLICIT_RECONCILIATION",
                outcome="QUARANTINED" if status is VerifyReconciliationStatus.UNKNOWN else "APPLIED",
            )
            self._audit(connection, customer=challenge["customer_id"], challenge=challenge["challenge_id"],
                        actor=command.actor_ref, correlation=command.correlation_id, now=now,
                        outcome="QUARANTINED" if status is VerifyReconciliationStatus.UNKNOWN else "APPLIED")
            result = self._result_from_event(connection, event, replayed=False)
            connection.commit()
            return result
        except (VerificationReconciliationError, PhoneVerificationRejected):
            if connection.in_transaction:
                connection.rollback()
            raise
        except (sqlite3.Error, PersistenceError, OSError, TypeError, ValueError):
            if connection.in_transaction:
                connection.rollback()
            raise VerificationReconciliationError("reconciliation persistence failed") from None
        finally:
            connection.close()

    def reconcile(self, command: object, *, capability: object | None = None,
                  authorization: object | None = None) -> ReconciliationResult:
        if type(command) is StartReconciliationCommand:
            return self.reconcile_start(command, capability=capability, authorization=authorization)
        if type(command) is VerifyReconciliationCommand:
            return self.reconcile_verify(command, capability=capability, authorization=authorization)
        raise VerificationReconciliationError("reconciliation command is malformed")

    # Explicit spellings make the quarantine boundary difficult to confuse
    # with ordinary START/VERIFY authority.
    reconcile_start_unknown = reconcile_start
    reconcile_verify_unknown = reconcile_verify


PhoneVerificationReconciliationService = VerificationReconciliationService
ReconciliationService = VerificationReconciliationService
AuthorizationError = ReconciliationAuthorizationError
ReconciliationCapability = VerificationReconciliationCapability


__all__ = [
    "VerificationReconciliationError", "ReconciliationAuthorizationError",
    "ReconciliationConflict", "VerificationReconciliationService",
    "PhoneVerificationReconciliationService", "ReconciliationService",
    "AuthorizationError", "ReconciliationCapability",
    "ReconciliationAuthorizationCapability",
]

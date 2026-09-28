"""Durable Control Plane seam for provider-neutral phone verification."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import os
from pathlib import Path
import re
import sqlite3
import tempfile
from typing import Callable
import uuid

from pydantic import TypeAdapter

from core.shopping.customer_auth import (
    RECEIPT_MAX_LIFETIME, ReceiptLifecycle, ReceiptValidationResult,
    TrustedReceiptBinding, TrustedVerificationContext, TrustedVerificationReceipt,
    TrustedVerificationSeam, VerificationPurpose, validate_trusted_receipt,
)
from core.shopping.customer_identity import CustomerId, require_utc
from core.shopping.customer_persistence import (
    BUSY_TIMEOUT_MS, PersistenceError, SQLiteVerificationRepository, _utc,
)
from core.shopping.phone_normalization import (
    CanonicalPhone, OpaquePhoneBinding, derive_phone_binding, normalize_phone,
)
from core.shopping.ports.destination_resolution import (
    DestinationHandle, DestinationResolutionPort,
    DestinationScope,
)
from core.shopping.ports.phone_verification import (
    ChallengeReference, ChallengeStartRequest, ChallengeStartResult,
    ChallengeStatus, ChallengeSubject, ChallengeVerificationRequest,
    ChallengeVerificationResult, PhoneVerificationPort,
    ProviderSourceIdentifier, ProviderVerificationIdentifier, ReplayReference,
    VerificationStatus,
)

_OPAQUE = re.compile(r"^AG-[A-Z]{3}-[0-9a-f]{12}4[0-9a-f]{3}[89ab][0-9a-f]{15}$")
_CUSTOMER_ID = TypeAdapter(CustomerId)


class PhoneVerificationError(RuntimeError):
    """Sanitized fail-closed error; provider details never cross the seam."""


class PhoneVerificationRejected(PhoneVerificationError):
    pass


@dataclass(frozen=True)
class PhoneChallenge:
    start_evidence: ChallengeStartResult
    customer_id: str
    browser_challenge: str
    local_expires_at: datetime

    def __repr__(self) -> str:
        return ("PhoneChallenge(start_evidence=<validated>, "
                f"customer_id={self.customer_id!r}, "
                f"browser_challenge={self.browser_challenge!r}, "
                f"local_expires_at={self.local_expires_at!r})")


@dataclass(frozen=True)
class TrustedPhoneVerification:
    seam: TrustedVerificationSeam
    verification_evidence: ChallengeVerificationResult

    @property
    def receipt(self) -> TrustedVerificationReceipt:
        return self.seam.receipt

    @property
    def context(self) -> TrustedVerificationContext:
        return self.seam.context

    @property
    def trusted_receipt(self) -> TrustedVerificationReceipt:
        return self.seam.receipt

    @property
    def trusted_context(self) -> TrustedVerificationContext:
        return self.seam.context

    def __repr__(self) -> str:
        return "TrustedPhoneVerification(seam=<trusted receipt/context>, verification_evidence=<validated>)"


PhoneVerificationOutcome = TrustedPhoneVerification


def _uuid4_shaped(prefix: str, seed: str) -> str:
    raw = bytearray(hashlib.sha256(seed.encode("utf-8")).digest()[:16])
    raw[6] = (raw[6] & 0x0F) | 0x40
    raw[8] = (raw[8] & 0x3F) | 0x80
    return prefix + uuid.UUID(bytes=bytes(raw)).hex


def _as_identifier(value: object, kind: type) -> object:
    if isinstance(value, kind):
        return value
    if type(value) is str:
        try:
            return kind(value=value)
        except (TypeError, ValueError):
            pass
    raise PhoneVerificationRejected("phone verification evidence rejected")


def _opaque_ref(prefix: str, value: object) -> str:
    return value if type(value) is str and _OPAQUE.fullmatch(value) else _uuid4_shaped(prefix, str(value))


def _dt(value: object) -> datetime:
    if type(value) is not str:
        raise ValueError
    return require_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))


def _value(row: sqlite3.Row, name: str) -> object:
    try:
        return row[name]
    except (IndexError, KeyError):
        raise PhoneVerificationRejected("verification storage row is malformed") from None


def _provider_failure_code(error: BaseException) -> str | None:
    for attribute in ("code", "failure_code", "reason_code"):
        candidate = getattr(error, attribute, None)
        candidate = getattr(candidate, "value", candidate)
        if type(candidate) is str:
            return candidate
    return None


class PhoneVerificationService:
    """Provider-neutral policy over durable v3 verification state."""

    def __init__(
        self, port: PhoneVerificationPort, utc_clock: Callable[[], datetime] | None = None,
        phone_binding_key: bytes | None = None, *, clock: Callable[[], datetime] | None = None,
        binding_key: bytes | None = None, provider_source: ProviderSourceIdentifier | str = "synthetic.mock",
        issuer_ref: str | None = None, challenge_lifetime: timedelta = timedelta(minutes=5),
        evidence_max_age: timedelta = timedelta(minutes=5), database_path: str | Path | None = None,
        repository: SQLiteVerificationRepository | None = None, busy_timeout_ms: int = BUSY_TIMEOUT_MS,
        event_id_factory: Callable[[], str] | None = None,
        audit_failure_hook: Callable[[str], None] | None = None,
        destination_resolution: DestinationResolutionPort | None = None,
        destination_resolver: DestinationResolutionPort | None = None,
    ) -> None:
        if not hasattr(port, "start_challenge") or not hasattr(port, "verify_challenge"):
            raise TypeError("a phone verification port is required")
        utc_clock = utc_clock if utc_clock is not None else clock
        phone_binding_key = phone_binding_key if phone_binding_key is not None else binding_key
        if not callable(utc_clock):
            raise TypeError("an injected UTC clock is required")
        if type(phone_binding_key) is not bytes or not phone_binding_key:
            raise ValueError("phone binding key must be non-empty injected bytes")
        if destination_resolution is not None and destination_resolver is not None:
            raise ValueError("choose one destination resolution port")
        if destination_resolution is None:
            destination_resolution = destination_resolver
        destination_issue = None
        if destination_resolution is not None:
            destination_issue = getattr(destination_resolution, "issue_destination", None)
            if not callable(destination_issue):
                destination_issue = getattr(destination_resolution, "issue", None)
            if not callable(destination_issue):
                raise TypeError("a destination resolution port is required")
        if repository is not None and database_path is not None:
            raise ValueError("choose a verification repository or database path")
        if repository is None:
            if database_path is None:
                # Pre-C1 mock compatibility still uses SQLite, never a Python
                # state authority. Production callers must provide a path.
                handle, database_path = tempfile.mkstemp(prefix="aicc-verification-")
                os.close(handle)
                SQLiteVerificationRepository.initialize_schema(database_path)
            repository = SQLiteVerificationRepository(database_path, busy_timeout_ms=busy_timeout_ms)
        self._port, self._clock, self._binding_key = port, utc_clock, phone_binding_key
        self._destination_resolution = destination_resolution
        self._destination_issue = destination_issue
        self._repository = repository
        self.database_path = str(repository.database_path)
        self._provider_source = _as_identifier(provider_source, ProviderSourceIdentifier)
        issuer_ref = issuer_ref or _uuid4_shaped("AG-ISS-", "issuer:" + str(self._provider_source))
        if type(issuer_ref) is not str or not issuer_ref.startswith("AG-ISS-") or _OPAQUE.fullmatch(issuer_ref) is None:
            raise ValueError("issuer reference is invalid")
        if type(challenge_lifetime) is not timedelta or not timedelta(0) < challenge_lifetime <= RECEIPT_MAX_LIFETIME:
            raise ValueError("challenge lifetime is outside the local policy")
        if type(evidence_max_age) is not timedelta or not timedelta(0) < evidence_max_age <= RECEIPT_MAX_LIFETIME:
            raise ValueError("evidence age is outside the local policy")
        self._issuer_ref, self._challenge_lifetime, self._evidence_max_age = issuer_ref, challenge_lifetime, evidence_max_age
        self._event_id_factory = event_id_factory or (lambda: "AG-AUD-" + uuid.uuid4().hex)
        self._audit_failure_hook = audit_failure_hook

    def _now(self) -> datetime:
        try:
            return require_utc(self._clock())
        except (TypeError, ValueError, AttributeError, OverflowError):
            raise PhoneVerificationRejected("phone verification policy rejected") from None

    def _open(self) -> sqlite3.Connection:
        try:
            return self._repository.open()
        except (PersistenceError, sqlite3.Error, OSError):
            raise PhoneVerificationRejected("phone verification storage unavailable") from None

    def _reference(self, value: object | None, kind: type, prefix: str, seed: str) -> object:
        return kind(value=_uuid4_shaped(prefix, seed + ":" + uuid.uuid4().hex)) if value is None else _as_identifier(value, kind)

    @staticmethod
    def _matches(row: sqlite3.Row, *, challenge: str, customer: str, replay: str,
                 binding: OpaquePhoneBinding, purpose: VerificationPurpose, browser: str,
                 provider_source: ProviderSourceIdentifier) -> bool:
        return (row["challenge_id"] == challenge and row["customer_id"] == customer
                and row["replay_reference"] == replay and row["phone_binding"] == str(binding)
                and row["purpose"] == purpose.value and row["browser_challenge"] == browser
                and row["provider_source"] == str(provider_source))

    @staticmethod
    def _start_rows(connection: sqlite3.Connection, *, challenge: str, replay: str) -> list[sqlite3.Row]:
        return connection.execute(
            "SELECT * FROM shopping_verification_challenges "
            "WHERE challenge_id=? OR replay_reference=?",
            (challenge, replay),
        ).fetchall()

    def _existing_start(
        self,
        rows: list[sqlite3.Row],
        *,
        challenge: str,
        customer: str,
        replay: str,
        binding: OpaquePhoneBinding,
        purpose: VerificationPurpose,
        browser: str,
        now: datetime,
    ) -> ChallengeStartResult | None:
        if not rows:
            return None
        if len(rows) != 1 or not self._matches(
            rows[0], challenge=challenge, customer=customer, replay=replay,
            binding=binding, purpose=purpose, browser=browser,
            provider_source=self._provider_source,
        ):
            raise PhoneVerificationRejected("challenge reference conflict")
        row = rows[0]
        try:
            status = ChallengeStatus(row["status"])
        except (TypeError, ValueError):
            raise PhoneVerificationRejected("verification storage row is malformed") from None
        if status in {ChallengeStatus.START_CLAIMED, ChallengeStatus.START_UNKNOWN,
                      ChallengeStatus.VERIFY_UNKNOWN}:
            raise PhoneVerificationRejected("challenge start is in-flight or unknown")
        if status in {ChallengeStatus.FAILED, ChallengeStatus.REJECTED,
                      ChallengeStatus.EXPIRED}:
            raise PhoneVerificationRejected("challenge start is terminal")
        result = self._start_from_row(row)
        if result.started_at > now:
            raise PhoneVerificationRejected("challenge start timestamp is in the future")
        return result

    @staticmethod
    def _start_from_row(row: sqlite3.Row) -> ChallengeStartResult:
        try:
            lifecycle = ChallengeStatus(row["status"])
            provider_status = ChallengeStatus(row["provider_start_status"])
            if lifecycle in {
                ChallengeStatus.START_CLAIMED, ChallengeStatus.START_UNKNOWN,
                ChallengeStatus.VERIFY_UNKNOWN, ChallengeStatus.FAILED,
                ChallengeStatus.REJECTED, ChallengeStatus.EXPIRED,
            } or provider_status not in {ChallengeStatus.STARTED, ChallengeStatus.PENDING}:
                raise PhoneVerificationRejected("challenge start evidence is unavailable")
            return ChallengeStartResult(
                provider_source=ProviderSourceIdentifier(value=row["provider_source"]),
                provider_verification_id=ProviderVerificationIdentifier(value=row["provider_verification_id"]),
                purpose=VerificationPurpose(row["purpose"]), challenge_reference=ChallengeReference(value=row["challenge_id"]),
                replay_reference=ReplayReference(value=row["replay_reference"]), phone_binding=OpaquePhoneBinding(row["phone_binding"]),
                status=provider_status, started_at=_dt(row["provider_started_at"]),
                provider_expires_at=None if row["provider_expires_at"] is None else _dt(row["provider_expires_at"]),
            )
        except PhoneVerificationRejected:
            raise
        except (TypeError, ValueError, KeyError, IndexError):
            raise PhoneVerificationRejected("verification storage row is malformed") from None

    def _stored_start(self, challenge: str) -> ChallengeStartResult | None:
        connection = self._open()
        try:
            row = connection.execute("SELECT * FROM shopping_verification_challenges WHERE challenge_id=?", (challenge,)).fetchone()
            if row is None:
                return None
            result = self._start_from_row(row)
            if result.started_at > self._now():
                raise PhoneVerificationRejected("challenge start timestamp is in the future")
            return result
        except (sqlite3.Error, PersistenceError):
            raise PhoneVerificationRejected("phone verification storage unavailable") from None
        finally:
            connection.close()

    def _issue_destination(
        self,
        canonical: CanonicalPhone,
        *,
        customer: str,
        purpose: VerificationPurpose,
        challenge: ChallengeReference,
        replay: ReplayReference,
        binding: OpaquePhoneBinding,
        browser: str,
    ) -> DestinationHandle | None:
        if self._destination_resolution is None:
            return None
        scope = DestinationScope(
            provider_source=str(self._provider_source), purpose=purpose,
            challenge_reference=str(challenge), replay_reference=str(replay),
            customer_id=customer, phone_binding=binding,
            browser_challenge=browser,
        )
        try:
            handle = self._destination_issue(canonical, scope)
        except Exception:
            raise PhoneVerificationRejected("phone verification destination unavailable") from None
        if type(handle) is not DestinationHandle:
            raise PhoneVerificationRejected("phone verification destination unavailable")
        return handle

    def start_challenge(self, phone: CanonicalPhone | str, *, customer_id: str,
                        browser_challenge: str | None = None, country_calling_code: str | None = None,
                        country_code: str | None = None, national_trunk_prefix: str | None = None,
                        purpose: VerificationPurpose = VerificationPurpose.SESSION_ISSUANCE,
                        challenge_reference: ChallengeReference | str | None = None,
                        replay_reference: ReplayReference | str | None = None) -> ChallengeStartResult:
        try:
            if type(purpose) is not VerificationPurpose:
                raise ValueError
            customer = _CUSTOMER_ID.validate_python(customer_id)
            canonical = phone if isinstance(phone, CanonicalPhone) else normalize_phone(phone, country_calling_code=country_calling_code, country_code=country_code, national_trunk_prefix=national_trunk_prefix)
            browser = (_opaque_ref("AG-CHL-", "browser:" + str(customer) + ":" + canonical.value)
                       if browser_challenge is None else browser_challenge)
            if type(browser) is not str or _OPAQUE.fullmatch(browser) is None:
                raise ValueError
            challenge = self._reference(challenge_reference, ChallengeReference, "AG-CHL-", "challenge:" + browser)
            replay = self._reference(replay_reference, ReplayReference, "AG-RPL-", "replay:" + str(challenge))
            now, binding = self._now(), derive_phone_binding(canonical, self._binding_key)
        except (TypeError, ValueError, PhoneVerificationRejected):
            raise PhoneVerificationRejected("phone verification request rejected") from None
        expires = min(now + self._challenge_lifetime, now + RECEIPT_MAX_LIFETIME)
        claim_token = uuid.uuid4().hex
        connection = self._open()
        try:
            # Phase A: this short transaction is the only authority that can
            # grant the right to invoke the provider.  It is committed before
            # any provider code runs.
            connection.execute("BEGIN IMMEDIATE")
            existing = self._existing_start(
                self._start_rows(connection, challenge=str(challenge), replay=str(replay)),
                challenge=str(challenge), customer=customer, replay=str(replay),
                binding=binding, purpose=purpose, browser=browser,
                now=now,
            )
            if existing is not None:
                connection.commit()
                return existing
            connection.execute(
                "INSERT INTO shopping_verification_challenges "
                "(challenge_id,customer_id,phone_binding,provider_source,"
                "provider_challenge_reference,provider_verification_id,replay_reference,"
                "purpose,browser_challenge,status,created_at,expires_at,"
                "provider_started_at,provider_expires_at,provider_start_status,"
                "receipt_id,start_claim_token,version) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)",
                (str(challenge), customer, str(binding), str(self._provider_source),
                 None, None, str(replay), purpose.value, browser,
                 ChallengeStatus.START_CLAIMED.value, _utc(now), _utc(expires),
                 None, None, None, None, claim_token),
            )
            connection.commit()
        except PhoneVerificationRejected:
            if connection.in_transaction:
                connection.rollback()
            raise
        except (sqlite3.Error, PersistenceError, OSError):
            if connection.in_transaction:
                connection.rollback()
            raise PhoneVerificationRejected("phone verification storage unavailable") from None
        finally:
            connection.close()

        try:
            destination_handle = self._issue_destination(
                canonical, customer=customer, purpose=purpose, challenge=challenge,
                replay=replay, binding=binding, browser=browser,
            )
            request = ChallengeStartRequest(
                provider_source=self._provider_source, purpose=purpose,
                challenge_reference=challenge, replay_reference=replay,
                subject=ChallengeSubject(phone_binding=binding),
                destination_handle=destination_handle,
            )
        except PhoneVerificationRejected:
            self._mark_start_failed(str(challenge), claim_token, version=0)
            raise
        except Exception:
            self._mark_start_failed(str(challenge), claim_token, version=0)
            raise PhoneVerificationRejected("phone verification destination unavailable") from None
        try:
            result = self._port.start_challenge(request)
        except Exception as error:
            if _provider_failure_code(error) == "REJECTED":
                self._mark_start_rejected(str(challenge), claim_token, version=0)
                raise PhoneVerificationRejected("phone verification provider rejected the challenge") from None
            self._mark_start_unknown(str(challenge), claim_token, version=0)
            raise PhoneVerificationRejected("phone verification provider failed") from None
        try:
            evidence_now = self._now()
            if type(result) is not ChallengeStartResult:
                raise PhoneVerificationRejected("phone verification evidence rejected")
            self._validate_start(result, request=request, now=evidence_now)
        except PhoneVerificationRejected:
            self._mark_start_unknown(str(challenge), claim_token, version=0)
            raise

        # Phase C: only the claim owner may durably publish provider evidence.
        connection = self._open()
        try:
            connection.execute("BEGIN IMMEDIATE")
            projection_now = self._now()
            self._validate_start(result, request=request, now=projection_now)
            row = connection.execute(
                "SELECT * FROM shopping_verification_challenges WHERE challenge_id=?",
                (str(challenge),),
            ).fetchone()
            if row is None or not self._matches(
                row, challenge=str(challenge), customer=customer, replay=str(replay),
                binding=binding, purpose=purpose, browser=browser,
                provider_source=self._provider_source,
            ) or row["status"] != ChallengeStatus.START_CLAIMED.value \
                    or int(row["version"]) != 0 or row["start_claim_token"] != claim_token:
                raise PhoneVerificationRejected("challenge start claim is no longer owned")
            if projection_now >= _dt(row["expires_at"]):
                raise PhoneVerificationRejected("local challenge expired")
            collision = connection.execute(
                "SELECT 1 FROM shopping_verification_challenges "
                "WHERE provider_source=? AND provider_verification_id=?",
                (str(result.provider_source), str(result.provider_verification_id)),
            ).fetchone()
            if collision is not None:
                raise PhoneVerificationRejected("ambiguous provider verification identifier")
            connection.execute(
                "UPDATE shopping_verification_challenges SET "
                "provider_challenge_reference=?,provider_verification_id=?,status=?,"
                "provider_started_at=?,provider_expires_at=?,provider_start_status=?,"
                "version=version+1 "
                "WHERE challenge_id=? AND status=? AND version=? AND start_claim_token=? "
                "AND provider_start_status IS NULL",
                (str(result.challenge_reference), str(result.provider_verification_id),
                 result.status.value, _utc(result.started_at),
                 None if result.provider_expires_at is None else _utc(result.provider_expires_at),
                 result.status.value,
                 str(challenge), ChallengeStatus.START_CLAIMED.value, 0, claim_token),
            )
            stored = connection.execute(
                "SELECT * FROM shopping_verification_challenges WHERE challenge_id=?",
                (str(challenge),),
            ).fetchone()
            if stored is None:
                raise PhoneVerificationRejected("challenge start persistence failed")
            persisted = self._start_from_row(stored)
            if persisted != result:
                raise PhoneVerificationRejected("challenge start persistence failed")
            connection.commit()
            return persisted
        except PhoneVerificationRejected:
            if connection.in_transaction: connection.rollback()
            self._mark_start_unknown(str(challenge), claim_token, version=0)
            raise
        except (sqlite3.Error, PersistenceError, OSError, TypeError, ValueError):
            if connection.in_transaction: connection.rollback()
            self._mark_start_unknown(str(challenge), claim_token, version=0)
            raise PhoneVerificationRejected("phone verification storage unavailable") from None
        finally:
            connection.close()

    def _mark_start_unknown(self, challenge: str, claim_token: str, *, version: int) -> None:
        """Atomically quarantine an ambiguous START outcome."""
        connection = self._open()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM shopping_verification_challenges WHERE challenge_id=?",
                (challenge,),
            ).fetchone()
            if (row is None or row["status"] != ChallengeStatus.START_CLAIMED.value
                    or int(row["version"]) != version or row["start_claim_token"] != claim_token):
                raise PhoneVerificationRejected("challenge start claim is no longer owned")
            now = self._now()
            next_version = version + 1
            quarantine_id = _uuid4_shaped("AG-QTN-", "start:" + challenge)
            command_id = "start-unknown:" + challenge
            connection.execute(
                "INSERT INTO shopping_verification_unknown_outcomes "
                "(quarantine_id,challenge_id,customer_id,provider_source,provider_verification_id,replay_reference,purpose,operation,state,reason_code,opened_at,updated_at,version,challenge_version,provider_status,provider_started_at,provider_verified_at,provider_expires_at,last_command_id) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (quarantine_id, challenge, row["customer_id"], row["provider_source"], None,
                 row["replay_reference"], row["purpose"], "START", "OPEN", "UNKNOWN_OUTCOME",
                 _utc(now), _utc(now), 1, next_version, "UNKNOWN_OUTCOME", None, None, None, command_id),
            )
            connection.execute(
                "UPDATE shopping_verification_challenges SET status=?,version=? "
                "WHERE challenge_id=? AND status=? AND version=? AND start_claim_token=?",
                (ChallengeStatus.START_UNKNOWN.value, next_version, challenge,
                 ChallengeStatus.START_CLAIMED.value, version, claim_token),
            )
            connection.execute(
                "INSERT INTO shopping_verification_reconciliation_events "
                "(event_id,command_id,quarantine_id,challenge_id,operation,from_lifecycle,to_lifecycle,quarantine_version,challenge_version,provider_source,provider_verification_id,provider_status,provider_started_at,provider_verified_at,provider_expires_at,actor_ref,correlation_id,occurred_at,outcome,reason_code) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("AG-REC-" + uuid.uuid4().hex, command_id, quarantine_id, challenge,
                 "START", ChallengeStatus.START_CLAIMED.value, ChallengeStatus.START_UNKNOWN.value,
                 1, next_version, row["provider_source"], None, "UNKNOWN_OUTCOME", None, None, None,
                 "system:phone-verification", command_id, _utc(now), "QUARANTINED", "UNKNOWN_OUTCOME"),
            )
            self._audit(connection, customer=row["customer_id"], challenge=challenge,
                        correlation_id=command_id, now=now, outcome="UNKNOWN_QUARANTINED")
            connection.commit()
        except PhoneVerificationRejected:
            if connection.in_transaction:
                connection.rollback()
            raise
        except (sqlite3.Error, PersistenceError, OSError, ValueError, TypeError):
            if connection.in_transaction:
                connection.rollback()
            raise PhoneVerificationRejected("phone verification quarantine persistence failed") from None
        finally:
            connection.close()

    def _mark_start_rejected(self, challenge: str, claim_token: str, *, version: int) -> None:
        """Atomically project structured provider rejection as terminal evidence."""
        connection = self._open()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM shopping_verification_challenges WHERE challenge_id=?",
                (challenge,),
            ).fetchone()
            if (row is None or row["status"] != ChallengeStatus.START_CLAIMED.value
                    or int(row["version"]) != version or row["start_claim_token"] != claim_token):
                raise PhoneVerificationRejected("challenge start claim is no longer owned")
            now = self._now()
            terminal_status = (
                ChallengeStatus.EXPIRED
                if now >= _dt(row["expires_at"])
                else ChallengeStatus.REJECTED
            )
            if connection.execute(
                "UPDATE shopping_verification_challenges SET status=?,version=version+1 "
                "WHERE challenge_id=? AND status=? AND version=? AND start_claim_token=?",
                (terminal_status.value, challenge,
                 ChallengeStatus.START_CLAIMED.value, version, claim_token),
            ).rowcount != 1:
                raise PhoneVerificationRejected("challenge start claim is no longer owned")
            self._audit(
                connection, customer=row["customer_id"], challenge=challenge,
                correlation_id="start-rejected:" + challenge, now=now,
                outcome=terminal_status.value,
            )
            connection.commit()
        except PhoneVerificationRejected:
            if connection.in_transaction:
                connection.rollback()
            raise
        except (sqlite3.Error, PersistenceError, OSError, ValueError, TypeError):
            if connection.in_transaction:
                connection.rollback()
            raise PhoneVerificationRejected("phone verification rejection persistence failed") from None
        finally:
            connection.close()

    def _mark_verify_unknown(self, request: ChallengeVerificationRequest,
                             challenge: sqlite3.Row, *, reason: str = "UNKNOWN_OUTCOME") -> None:
        """Atomically quarantine an ambiguous VERIFY execution."""
        connection = self._open()
        try:
            connection.execute("BEGIN IMMEDIATE")
            current = connection.execute(
                "SELECT * FROM shopping_verification_challenges WHERE challenge_id=?",
                (str(request.challenge_reference),),
            ).fetchone()
            if current is None or current["status"] not in {
                ChallengeStatus.STARTED.value, ChallengeStatus.PENDING.value,
            } or int(current["version"]) != int(challenge["version"]):
                raise PhoneVerificationRejected("challenge state conflict")
            now = self._now()
            next_version = int(current["version"]) + 1
            quarantine_id = _uuid4_shaped("AG-QTN-", "verify:" + str(request.challenge_reference))
            command_id = "verify-unknown:" + str(request.challenge_reference)
            connection.execute(
                "INSERT INTO shopping_verification_unknown_outcomes "
                "(quarantine_id,challenge_id,customer_id,provider_source,provider_verification_id,replay_reference,purpose,operation,state,reason_code,opened_at,updated_at,version,challenge_version,provider_status,provider_started_at,provider_verified_at,provider_expires_at,last_command_id) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (quarantine_id, current["challenge_id"], current["customer_id"], current["provider_source"],
                 current["provider_verification_id"], current["replay_reference"], current["purpose"],
                 "VERIFY", "OPEN", reason, _utc(now), _utc(now), 1, next_version, reason,
                 current["provider_started_at"], None, None, command_id),
            )
            if connection.execute(
                "UPDATE shopping_verification_challenges SET status=?,version=? WHERE challenge_id=? AND status IN ('STARTED','PENDING') AND version=?",
                (ChallengeStatus.VERIFY_UNKNOWN.value, next_version, current["challenge_id"], int(challenge["version"])),
            ).rowcount != 1:
                raise PhoneVerificationRejected("challenge state conflict")
            connection.execute(
                "INSERT INTO shopping_verification_reconciliation_events "
                "(event_id,command_id,quarantine_id,challenge_id,operation,from_lifecycle,to_lifecycle,quarantine_version,challenge_version,provider_source,provider_verification_id,provider_status,provider_started_at,provider_verified_at,provider_expires_at,actor_ref,correlation_id,occurred_at,outcome,reason_code) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("AG-REC-" + uuid.uuid4().hex, command_id, quarantine_id, current["challenge_id"],
                 "VERIFY", current["status"], ChallengeStatus.VERIFY_UNKNOWN.value, 1, next_version,
                 current["provider_source"], current["provider_verification_id"], reason,
                 current["provider_started_at"], None, None, "system:phone-verification", command_id,
                 _utc(now), "QUARANTINED", reason),
            )
            self._audit(connection, customer=current["customer_id"], challenge=current["challenge_id"],
                        correlation_id=command_id, now=now, outcome="UNKNOWN_QUARANTINED")
            connection.commit()
        except PhoneVerificationRejected:
            if connection.in_transaction:
                connection.rollback()
            raise
        except (sqlite3.Error, PersistenceError, OSError, ValueError, TypeError):
            if connection.in_transaction:
                connection.rollback()
            raise PhoneVerificationRejected("phone verification quarantine persistence failed") from None
        finally:
            connection.close()

    def _mark_start_failed(self, challenge: str, claim_token: str, *, version: int) -> None:
        """Record a local pre-provider failure without implying provider invocation."""
        try:
            connection = self._open()
        except PhoneVerificationRejected:
            return
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "UPDATE shopping_verification_challenges SET status=?,version=version+1 "
                "WHERE challenge_id=? AND status=? AND version=? AND start_claim_token=?",
                (ChallengeStatus.FAILED.value, challenge,
                 ChallengeStatus.START_CLAIMED.value, version, claim_token),
            )
            connection.commit()
        except (sqlite3.Error, PersistenceError, OSError):
            if connection.in_transaction:
                connection.rollback()
        finally:
            connection.close()

    def _validate_start(self, result: ChallengeStartResult, *, request: ChallengeStartRequest, now: datetime) -> None:
        if result.provider_source != request.provider_source or result.purpose is not request.purpose or result.challenge_reference != request.challenge_reference or result.replay_reference != request.replay_reference or result.phone_binding != request.subject.phone_binding:
            raise PhoneVerificationRejected("challenge binding rejected")
        if result.status not in {ChallengeStatus.STARTED, ChallengeStatus.PENDING}:
            raise PhoneVerificationRejected("challenge did not start")
        if result.started_at > now or now - result.started_at > self._evidence_max_age:
            raise PhoneVerificationRejected("invalid challenge timestamp")
        if result.provider_expires_at is not None and result.provider_expires_at <= now:
            raise PhoneVerificationRejected("challenge evidence expired")

    def verification_request(self, start: ChallengeStartResult, *, otp: str) -> ChallengeVerificationRequest:
        if type(start) is not ChallengeStartResult or self._stored_start(str(start.challenge_reference)) != start:
            raise PhoneVerificationRejected("unknown challenge")
        try:
            return ChallengeVerificationRequest(provider_source=start.provider_source, provider_verification_id=start.provider_verification_id, purpose=start.purpose, challenge_reference=start.challenge_reference, replay_reference=start.replay_reference, phone_binding=start.phone_binding, otp=otp)
        except (TypeError, ValueError):
            raise PhoneVerificationRejected("verification request is malformed") from None

    def _audit(self, connection: sqlite3.Connection, *, customer: str, challenge: str, correlation_id: str, now: datetime, outcome: str) -> None:
        action = "PHONE_VERIFICATION"
        if self._audit_failure_hook is not None:
            try: self._audit_failure_hook(action)
            except Exception: raise PhoneVerificationRejected("authentication audit persistence failed") from None
        try:
            connection.execute("INSERT INTO shopping_auth_audit(event_id,actor_ref,resource_ref,action,outcome,correlation_id,occurred_at) VALUES(?,?,?,?,?,?,?)", (self._event_id_factory(), customer, challenge, action, outcome, correlation_id, _utc(now)))
        except sqlite3.Error:
            raise PhoneVerificationRejected("authentication audit persistence failed") from None

    def _replay_result(
        self,
        connection: sqlite3.Connection,
        row: sqlite3.Row,
        *,
        request: ChallengeVerificationRequest,
        now: datetime,
    ) -> TrustedPhoneVerification:
        """Rebuild a completed result only from mutually consistent durable rows."""
        try:
            challenge_row = connection.execute(
                "SELECT * FROM shopping_verification_challenges WHERE challenge_id=?",
                (row["challenge_id"],),
            ).fetchone()
            receipt_row = connection.execute(
                "SELECT * FROM shopping_trusted_receipts WHERE attempt_id=?",
                (row["attempt_id"],),
            ).fetchone()
            if (
                challenge_row is None or receipt_row is None
                or row["outcome"] != VerificationStatus.SUCCESS.value
                or receipt_row["lifecycle"] != ReceiptLifecycle.ISSUED.value
            ):
                raise PhoneVerificationRejected("verification replay rejected")
            try:
                durable_start = self._start_from_row(challenge_row)
            except PhoneVerificationRejected:
                raise PhoneVerificationRejected("verification replay rejected") from None
            expected = (
                str(request.challenge_reference), str(request.replay_reference),
                str(request.provider_source), str(request.provider_verification_id),
                request.purpose.value, str(request.phone_binding),
            )
            actual = (
                challenge_row["challenge_id"], challenge_row["replay_reference"],
                challenge_row["provider_source"], challenge_row["provider_verification_id"],
                challenge_row["purpose"], challenge_row["phone_binding"],
            )
            if (
                actual != expected
                or challenge_row["status"] != ChallengeStatus.VERIFIED.value
                or durable_start.provider_source != request.provider_source
                or durable_start.provider_verification_id != request.provider_verification_id
                or durable_start.purpose is not request.purpose
                or durable_start.challenge_reference != request.challenge_reference
                or durable_start.replay_reference != request.replay_reference
                or durable_start.phone_binding != request.phone_binding
            ):
                raise PhoneVerificationRejected("verification replay conflict")
            if (
                row["challenge_id"] != challenge_row["challenge_id"]
                or row["replay_reference"] != challenge_row["replay_reference"]
                or row["provider_source"] != challenge_row["provider_source"]
                or row["provider_verification_id"] != challenge_row["provider_verification_id"]
                or row["phone_binding"] != challenge_row["phone_binding"]
                or row["receipt_id"] != receipt_row["receipt_id"]
                or receipt_row["challenge_id"] != challenge_row["challenge_id"]
                or receipt_row["attempt_id"] != row["attempt_id"]
                or receipt_row["customer_id"] != challenge_row["customer_id"]
                or receipt_row["browser_challenge"] != challenge_row["browser_challenge"]
                or receipt_row["purpose"] != challenge_row["purpose"]
                or receipt_row["provider_source"] != row["provider_source"]
                or receipt_row["provider_verification_id"] != row["provider_verification_id"]
                or receipt_row["phone_binding"] != row["phone_binding"]
                or challenge_row["receipt_id"] != receipt_row["receipt_id"]
            ):
                raise PhoneVerificationRejected("verification replay conflict")
            receipt = TrustedVerificationReceipt(
                receipt_id=receipt_row["receipt_id"],
                purpose=VerificationPurpose(receipt_row["purpose"]),
                browser_challenge=receipt_row["browser_challenge"],
                issuer_ref=receipt_row["issuer_ref"],
                customer_id=receipt_row["customer_id"],
                issued_at=_dt(receipt_row["issued_at"]),
                expires_at=_dt(receipt_row["expires_at"]),
                lifecycle=ReceiptLifecycle.ISSUED,
            )
            if (
                receipt.issued_at != _dt(row["attempted_at"])
                or receipt.expires_at > _dt(challenge_row["expires_at"])
            ):
                raise PhoneVerificationRejected("verification replay conflict")
            context = TrustedVerificationContext(
                accepted_bindings=frozenset({
                    TrustedReceiptBinding(receipt.receipt_id, receipt.issuer_ref, receipt.customer_id),
                }),
            )
            evidence = ChallengeVerificationResult(
                provider_source=ProviderSourceIdentifier(value=row["provider_source"]),
                provider_verification_id=ProviderVerificationIdentifier(value=row["provider_verification_id"]),
                purpose=receipt.purpose,
                challenge_reference=ChallengeReference(value=row["challenge_id"]),
                replay_reference=ReplayReference(value=row["replay_reference"]),
                phone_binding=OpaquePhoneBinding(row["phone_binding"]),
                status=VerificationStatus(row["outcome"]),
                verified_at=_dt(row["provider_verified_at"] or row["attempted_at"]),
                provider_expires_at=(
                    None if row["provider_expires_at"] is None
                    else _dt(row["provider_expires_at"])
                ),
            )
            outcome = TrustedPhoneVerification(
                seam=TrustedVerificationSeam(receipt=receipt, context=context),
                verification_evidence=evidence,
            )
            if validate_trusted_receipt(
                receipt, now=now, expected_challenge=receipt.browser_challenge,
                context=context,
            ) is not ReceiptValidationResult.ACCEPTED:
                raise PhoneVerificationRejected("verification replay rejected")
            return outcome
        except (TypeError, ValueError, KeyError, IndexError):
            raise PhoneVerificationRejected("verification storage row is malformed") from None

    def verify_challenge(self, request: ChallengeVerificationRequest | ChallengeStartResult | None = None, *, challenge_reference: ChallengeReference | str | None = None, replay_reference: ReplayReference | str | None = None, otp: str | None = None, correlation_id: str | None = None) -> TrustedPhoneVerification:
        if type(request) is ChallengeStartResult:
            if otp is None: raise PhoneVerificationRejected("verification OTP is required")
            request = self.verification_request(request, otp=otp)
        if request is None:
            if challenge_reference is None or replay_reference is None or otp is None: raise PhoneVerificationRejected("verification request is incomplete")
            start = self._stored_start(str(_as_identifier(challenge_reference, ChallengeReference)))
            if start is None or str(start.replay_reference) != str(_as_identifier(replay_reference, ReplayReference)): raise PhoneVerificationRejected("replay reference conflict")
            request = self.verification_request(start, otp=otp)
        if type(request) is not ChallengeVerificationRequest: raise PhoneVerificationRejected("verification request is malformed")
        connection = self._open()
        try:
            challenge = connection.execute("SELECT * FROM shopping_verification_challenges WHERE challenge_id=?", (str(request.challenge_reference),)).fetchone()
            if challenge is None: raise PhoneVerificationRejected("unknown challenge")
            binding = OpaquePhoneBinding(challenge["phone_binding"])
            request_source = str(request.provider_source)
            request_purpose = request.purpose.value if isinstance(request.purpose, VerificationPurpose) else str(request.purpose)
            if (request_source != challenge["provider_source"] or str(request.provider_verification_id) != challenge["provider_verification_id"] or request_purpose != challenge["purpose"] or str(request.replay_reference) != challenge["replay_reference"] or request.phone_binding != binding):
                raise PhoneVerificationRejected("verification binding rejected")
            now = self._now()
            prior = connection.execute("SELECT * FROM shopping_verification_attempts WHERE replay_reference=?", (str(request.replay_reference),)).fetchone()
            if prior is not None:
                return self._replay_result(connection, prior, request=request, now=now)
            if _dt(challenge["provider_started_at"]) > now:
                raise PhoneVerificationRejected("challenge start timestamp is in the future")
            status = ChallengeStatus(challenge["status"])
            if status in {ChallengeStatus.VERIFIED, ChallengeStatus.FAILED,
                          ChallengeStatus.REJECTED, ChallengeStatus.EXPIRED,
                          ChallengeStatus.START_UNKNOWN, ChallengeStatus.VERIFY_UNKNOWN}:
                raise PhoneVerificationRejected("challenge is terminal or quarantined")
            if now >= _dt(challenge["expires_at"]):
                connection.execute("BEGIN IMMEDIATE")
                changed = connection.execute("UPDATE shopping_verification_challenges SET status='EXPIRED',version=version+1 WHERE challenge_id=? AND status IN ('STARTED','PENDING') AND version=?", (str(request.challenge_reference), int(challenge["version"]))).rowcount
                if changed != 1: raise PhoneVerificationRejected("challenge state conflict")
                connection.commit()
                raise PhoneVerificationRejected("local challenge expired")
        except PhoneVerificationRejected:
            if connection.in_transaction: connection.rollback()
            raise
        except (sqlite3.Error, PersistenceError, OSError, ValueError):
            if connection.in_transaction: connection.rollback()
            raise PhoneVerificationRejected("phone verification storage unavailable") from None
        finally:
            if not connection.in_transaction:
                try: connection.close()
                except sqlite3.Error: pass
        now = self._now()
        try:
            result = self._port.verify_challenge(request)
        except Exception as error:
            code = _provider_failure_code(error)
            # An explicitly structured provider rejection is terminal evidence,
            # not an ambiguous execution. All other provider exceptions remain
            # quarantined because execution may have reached the provider.
            if code == "REJECTED":
                result = ChallengeVerificationResult(
                    provider_source=request.provider_source,
                    provider_verification_id=request.provider_verification_id,
                    purpose=request.purpose,
                    challenge_reference=request.challenge_reference,
                    replay_reference=request.replay_reference,
                    phone_binding=request.phone_binding,
                    status=VerificationStatus.REJECTED,
                    verified_at=self._now(),
                )
            else:
                reason = code if code in {
                    "UNKNOWN_OUTCOME", "TIMEOUT", "PROVIDER_UNAVAILABLE",
                    "AMBIGUOUS_PROVIDER_IDENTIFIER", "MALFORMED_RESPONSE",
                } else "UNKNOWN_OUTCOME"
                self._mark_verify_unknown(request, challenge, reason=reason)
                raise PhoneVerificationRejected("phone verification provider failed") from None
        if type(result) is not ChallengeVerificationResult:
            self._mark_verify_unknown(request, challenge, reason="MALFORMED_RESPONSE")
            raise PhoneVerificationRejected("phone verification evidence rejected")
        try:
            evidence_now = self._now()
            self._validate_verification(result, request=request, challenge=challenge, now=evidence_now)
        except PhoneVerificationRejected:
            self._mark_verify_unknown(request, challenge, reason="INVALID_EVIDENCE")
            raise
        correlation_id = correlation_id or _uuid4_shaped("AG-COR-", "verify:" + str(request.replay_reference))
        if type(correlation_id) is not str or not 1 <= len(correlation_id) <= 160: raise PhoneVerificationRejected("verification request rejected")
        connection = self._open()
        try:
            connection.execute("BEGIN IMMEDIATE")
            projection_now = self._now()
            current = connection.execute("SELECT * FROM shopping_verification_challenges WHERE challenge_id=?", (str(request.challenge_reference),)).fetchone()
            if current is None: raise PhoneVerificationRejected("unknown challenge")
            current_purpose = current["purpose"]
            if (current["provider_source"] != str(request.provider_source)
                    or current["provider_verification_id"] != str(request.provider_verification_id)
                    or current_purpose != (request.purpose.value if isinstance(request.purpose, VerificationPurpose) else str(request.purpose))
                    or current["replay_reference"] != str(request.replay_reference)
                    or current["phone_binding"] != str(request.phone_binding)):
                raise PhoneVerificationRejected("verification binding rejected")
            prior = connection.execute("SELECT * FROM shopping_verification_attempts WHERE replay_reference=?", (str(request.replay_reference),)).fetchone()
            if prior is not None:
                if (prior["challenge_id"], prior["provider_source"], prior["provider_verification_id"], prior["phone_binding"]) != (str(request.challenge_reference), str(request.provider_source), str(request.provider_verification_id), str(request.phone_binding)): raise PhoneVerificationRejected("replay conflict")
                replay = self._replay_result(connection, prior, request=request, now=now)
                connection.commit()
                return replay
            if current["status"] not in (ChallengeStatus.STARTED.value, ChallengeStatus.PENDING.value): raise PhoneVerificationRejected("challenge is terminal")
            # This is the authoritative local-expiry check after the provider
            # returned and immediately before any terminal provider result is
            # published.  A late rejection cannot outrank local expiry.
            if projection_now >= _dt(current["expires_at"]):
                if connection.execute(
                    "UPDATE shopping_verification_challenges SET status='EXPIRED',version=version+1 "
                    "WHERE challenge_id=? AND status IN ('STARTED','PENDING') AND version=?",
                    (str(request.challenge_reference), int(current["version"])),
                ).rowcount != 1:
                    raise PhoneVerificationRejected("challenge state conflict")
                self._audit(
                    connection, customer=current["customer_id"],
                    challenge=str(request.challenge_reference),
                    correlation_id=correlation_id, now=projection_now,
                    outcome=ChallengeStatus.EXPIRED.value,
                )
                connection.commit()
                raise PhoneVerificationRejected("local challenge expired")
            if result.status is VerificationStatus.SUCCESS:
                self._validate_verification(result, request=request, challenge=current, now=projection_now)
            collision = connection.execute("SELECT 1 FROM shopping_verification_attempts WHERE provider_source=? AND provider_verification_id=?", (str(result.provider_source), str(result.provider_verification_id))).fetchone()
            if collision is not None: raise PhoneVerificationRejected("ambiguous provider verification identifier")
            attempt_id = _uuid4_shaped("AG-ATT-", "attempt:" + str(request.replay_reference))
            connection.execute("INSERT INTO shopping_verification_attempts (attempt_id,challenge_id,replay_reference,provider_source,provider_verification_id,phone_binding,outcome,attempted_at,provider_verified_at,provider_expires_at) VALUES(?,?,?,?,?,?,?,?,?,?)", (attempt_id, str(request.challenge_reference), str(request.replay_reference), str(result.provider_source), str(result.provider_verification_id), str(result.phone_binding), result.status.value, _utc(projection_now), _utc(result.verified_at), None if result.provider_expires_at is None else _utc(result.provider_expires_at)))
            if result.status is not VerificationStatus.SUCCESS:
                next_status = result.status.value if result.status in {
                    VerificationStatus.FAILED, VerificationStatus.REJECTED,
                    VerificationStatus.EXPIRED,
                } else ChallengeStatus.FAILED.value
                if connection.execute("UPDATE shopping_verification_challenges SET status=?,version=version+1 WHERE challenge_id=? AND status IN ('STARTED','PENDING') AND version=?", (next_status, str(request.challenge_reference), int(current["version"]))).rowcount != 1: raise PhoneVerificationRejected("challenge state conflict")
                self._audit(connection, customer=current["customer_id"], challenge=str(request.challenge_reference), correlation_id=correlation_id, now=projection_now, outcome="REJECTED")
                connection.commit(); raise PhoneVerificationRejected("verification did not succeed")
            receipt_id = _uuid4_shaped("AG-VRF-", "receipt:" + str(request.replay_reference))
            receipt_expires_at = min(_dt(current["expires_at"]), projection_now + RECEIPT_MAX_LIFETIME)
            if connection.execute("UPDATE shopping_verification_challenges SET status='VERIFIED',receipt_id=?,version=version+1 WHERE challenge_id=? AND status IN ('STARTED','PENDING') AND version=?", (receipt_id, str(request.challenge_reference), int(current["version"]))).rowcount != 1: raise PhoneVerificationRejected("challenge state conflict")
            connection.execute("INSERT INTO shopping_trusted_receipts (receipt_id,challenge_id,attempt_id,customer_id,issuer_ref,browser_challenge,purpose,provider_source,provider_verification_id,phone_binding,issued_at,expires_at,lifecycle,version) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,0)", (receipt_id, str(request.challenge_reference), attempt_id, current["customer_id"], self._issuer_ref, current["browser_challenge"], current["purpose"], str(result.provider_source), str(result.provider_verification_id), str(result.phone_binding), _utc(projection_now), _utc(receipt_expires_at), "ISSUED"))
            connection.execute("UPDATE shopping_verification_attempts SET receipt_id=? WHERE attempt_id=?", (receipt_id, attempt_id))
            self._audit(connection, customer=current["customer_id"], challenge=str(request.challenge_reference), correlation_id=correlation_id, now=projection_now, outcome="APPLIED")
            persisted_attempt = connection.execute(
                "SELECT * FROM shopping_verification_attempts WHERE attempt_id=?",
                (attempt_id,),
            ).fetchone()
            if persisted_attempt is None:
                raise PhoneVerificationRejected("verification result persistence failed")
            outcome = self._replay_result(
                connection, persisted_attempt, request=request, now=projection_now,
            )
            connection.commit()
            return outcome
        except PhoneVerificationRejected:
            if connection.in_transaction: connection.rollback()
            raise
        except (sqlite3.Error, PersistenceError, OSError, ValueError, TypeError):
            if connection.in_transaction: connection.rollback()
            raise PhoneVerificationRejected("phone verification storage unavailable") from None
        except Exception:
            if connection.in_transaction:
                connection.rollback()
            raise PhoneVerificationRejected("phone verification persistence failed") from None
        finally: connection.close()

    def _validate_verification(self, result: ChallengeVerificationResult, *, request: ChallengeVerificationRequest, challenge: sqlite3.Row, now: datetime) -> None:
        if result.provider_source != request.provider_source or result.provider_verification_id != request.provider_verification_id or result.purpose is not request.purpose or result.challenge_reference != request.challenge_reference or result.replay_reference != request.replay_reference or result.phone_binding != request.phone_binding: raise PhoneVerificationRejected("verification binding rejected")
        if result.verified_at > now:
            raise PhoneVerificationRejected("invalid verification timestamp")
        if result.status is not VerificationStatus.SUCCESS:
            if result.status not in {VerificationStatus.FAILED, VerificationStatus.EXPIRED, VerificationStatus.REJECTED}: raise PhoneVerificationRejected("verification evidence rejected")
            return
        if result.verified_at > now or now - result.verified_at > self._evidence_max_age: raise PhoneVerificationRejected("invalid verification timestamp")
        if result.provider_expires_at is not None and result.provider_expires_at <= now: raise PhoneVerificationRejected("verification evidence expired")
        if now >= _dt(challenge["expires_at"]) or result.verified_at >= _dt(challenge["expires_at"]): raise PhoneVerificationRejected("verification exceeds local expiry")


__all__ = ["PhoneChallenge", "PhoneVerificationError", "PhoneVerificationOutcome", "PhoneVerificationRejected", "PhoneVerificationService", "TrustedPhoneVerification"]

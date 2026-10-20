"""DEV-only one-number OTP authority using a registered Korean SENS sender."""
from datetime import datetime, timezone
import hashlib
import hmac
import os
from pathlib import Path
import re
import secrets
import sqlite3
import uuid

from core.shopping.phone_normalization import derive_phone_binding, normalize_phone
from core.shopping.ports.phone_verification import (
    ChallengeStartResult, ChallengeStatus, ChallengeVerificationResult,
    ProviderVerificationIdentifier, VerificationStatus,
)
from ops.macos.shopping.dev_sens_sms import SensSMS

SOURCE = "ncloud.sens.dev"


class FixedDevSensPort:
    source = SOURCE

    def __init__(self, sens_cfg, phone_cfg, binding_key, path, *, transport=None,
                 clock=lambda: datetime.now(timezone.utc)):
        if phone_cfg.get("environment") != "DEV" or phone_cfg.get("provider") != "sens_sms" or phone_cfg.get("enabled") is not True:
            raise ValueError("DEV_SENS_PHONE_DISABLED")
        self.phone = normalize_phone(phone_cfg["test_phone"])
        self.binding = derive_phone_binding(self.phone, binding_key)
        self.key = hashlib.sha256(b"aicc/dev-sens-otp/v1\0" + binding_key).digest()
        self.path = Path(path)
        if self.path.is_symlink():
            raise ValueError("PRIVATE_STORAGE_REQUIRED")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.transport = transport or SensSMS(sens_cfg)
        self.clock = clock
        self.last_error_code = None
        with sqlite3.connect(self.path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS sens_otp (
                id TEXT PRIMARY KEY, challenge TEXT UNIQUE NOT NULL, replay TEXT NOT NULL,
                binding TEXT NOT NULL, otp_hash TEXT NOT NULL, state TEXT NOT NULL,
                attempts INTEGER NOT NULL, expires REAL NOT NULL
            )""")
        os.chmod(self.path, 0o600)

    def _hash(self, identifier, code):
        return hmac.new(self.key, (identifier + ":" + code).encode(), hashlib.sha256).hexdigest()

    def start_challenge(self, request):
        if str(request.provider_source) != SOURCE or request.subject.phone_binding != self.binding:
            raise ValueError("SENS_CHALLENGE_DENIED")
        identifier = "SENS-" + uuid.uuid4().hex
        code = f"{secrets.randbelow(1000000):06d}"
        now = self.clock()
        expires = now.timestamp() + 300
        with sqlite3.connect(self.path) as db:
            db.execute("INSERT INTO sens_otp VALUES(?,?,?,?,?,'SENDING',0,?)",
                       (identifier, str(request.challenge_reference), str(request.replay_reference),
                        str(self.binding), self._hash(identifier, code), expires))
        try:
            self.transport.send(self.phone.value, f"[agachichi] 인증번호 {code} (5분 유효)")
        except Exception:
            with sqlite3.connect(self.path) as db:
                db.execute("UPDATE sens_otp SET state='UNKNOWN' WHERE id=? AND state='SENDING'", (identifier,))
            raise
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE sens_otp SET state='PENDING' WHERE id=? AND state='SENDING'", (identifier,))
        return ChallengeStartResult(
            provider_source=request.provider_source,
            provider_verification_id=ProviderVerificationIdentifier(value=identifier),
            purpose=request.purpose, challenge_reference=request.challenge_reference,
            replay_reference=request.replay_reference, phone_binding=request.subject.phone_binding,
            status=ChallengeStatus.PENDING, started_at=now,
        )

    def verify_challenge(self, request):
        if str(request.provider_source) != SOURCE or request.phone_binding != self.binding:
            raise ValueError("SENS_CHECK_DENIED")
        now = self.clock()
        identifier = str(request.provider_verification_id)
        with sqlite3.connect(self.path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT challenge,replay,binding,otp_hash,state,attempts,expires FROM sens_otp WHERE id=?",
                             (identifier,)).fetchone()
            if not row or row[0] != str(request.challenge_reference) or row[1] != str(request.replay_reference) or row[2] != str(self.binding) or row[4] != "PENDING":
                raise ValueError("SENS_CHECK_DENIED")
            if now.timestamp() >= row[6]:
                db.execute("UPDATE sens_otp SET state='EXPIRED' WHERE id=?", (identifier,))
                status = VerificationStatus.EXPIRED
            elif row[5] >= 3 or not re.fullmatch(r"[0-9]{6}", request.otp):
                db.execute("UPDATE sens_otp SET state='FAILED',attempts=attempts+1 WHERE id=?", (identifier,))
                status = VerificationStatus.REJECTED
            elif hmac.compare_digest(row[3], self._hash(identifier, request.otp)):
                db.execute("UPDATE sens_otp SET state='VERIFIED',attempts=attempts+1 WHERE id=?", (identifier,))
                status = VerificationStatus.SUCCESS
            else:
                db.execute("UPDATE sens_otp SET state='FAILED',attempts=attempts+1 WHERE id=?", (identifier,))
                status = VerificationStatus.REJECTED
        return ChallengeVerificationResult(
            provider_source=request.provider_source, provider_verification_id=request.provider_verification_id,
            purpose=request.purpose, challenge_reference=request.challenge_reference,
            replay_reference=request.replay_reference, phone_binding=request.phone_binding,
            status=status, verified_at=now,
        )

"""Durable single-use claim for governed Production Runtime activation."""
from __future__ import annotations

import fcntl
import os
import stat
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path

from core.deployment.contracts import canonical_json_bytes

from .authorization import canonical_digest
from .models import ProductionRuntimeActivationError


@dataclass(frozen=True, slots=True)
class ProductionRuntimeActivationClaimRequest:
    authorization_id: str
    authorization_digest: str
    activation_request_digest: str
    candidate_runtime_id: str
    candidate_source_commit: str
    governance_commit: str
    expected_current_runtime_id: str
    operator_identity: str
    claimed_at: str

    def __post_init__(self) -> None:
        if not self.authorization_id or not self.operator_identity or not self.claimed_at:
            raise ProductionRuntimeActivationError(
                "ACTIVATION_CLAIM_IDENTITY_INVALID"
            )
        for value in (
            self.authorization_digest,
            self.activation_request_digest,
        ):
            if not isinstance(value, str) or not value.startswith("sha256:") or len(value) != 71:
                raise ProductionRuntimeActivationError(
                    "ACTIVATION_CLAIM_DIGEST_INVALID"
                )


@dataclass(frozen=True, slots=True)
class ProductionRuntimeActivationClaimReceipt:
    claim_id: str
    claim_path: Path
    claim_digest: str
    request: ProductionRuntimeActivationClaimRequest


class ProductionRuntimeActivationClaimRegistry:
    """Single-use registry. Deliberately exposes no delete/reset/reuse operation."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def _validate_root(self) -> None:
        root = self.root
        if (
            not root.is_absolute()
            or ".." in root.parts
            or root.is_symlink()
            or not root.is_dir()
        ):
            raise ProductionRuntimeActivationError(
                "ACTIVATION_CLAIM_ROOT_INVALID"
            )
        info = root.stat()
        if info.st_uid != os.getuid():
            raise ProductionRuntimeActivationError(
                "ACTIVATION_CLAIM_ROOT_OWNER_INVALID"
            )
        if stat.S_IMODE(info.st_mode) != 0o700:
            raise ProductionRuntimeActivationError(
                "ACTIVATION_CLAIM_ROOT_MODE_INVALID"
            )

    def claim(
        self,
        request: ProductionRuntimeActivationClaimRequest,
    ) -> ProductionRuntimeActivationClaimReceipt:
        self._validate_root()

        claim_path = self.root / f"{request.authorization_id}.claim.json"
        payload = asdict(request)
        raw = canonical_json_bytes(payload)

        try:
            descriptor = os.open(
                claim_path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
        except FileExistsError as exc:
            raise ProductionRuntimeActivationError(
                "ACTIVATION_ALREADY_CLAIMED"
            ) from exc

        try:
            os.write(descriptor, raw)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

        try:
            directory = os.open(self.root, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except OSError:
            pass

        digest = canonical_digest(payload)
        return ProductionRuntimeActivationClaimReceipt(
            claim_id="activation-01c-claim-" + digest[7:39],
            claim_path=claim_path,
            claim_digest=digest,
            request=request,
        )

class ProductionRuntimeActivationExecutionLaneRegistry:
    """Reusable host-local serialization lane for Production pointer activation."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def _validate_root(self) -> None:
        root = self.root
        if (
            not root.is_absolute()
            or ".." in root.parts
            or root.is_symlink()
            or not root.is_dir()
        ):
            raise ProductionRuntimeActivationError(
                "ACTIVATION_EXECUTION_LANE_ROOT_INVALID"
            )
        info = root.stat()
        if info.st_uid != os.getuid():
            raise ProductionRuntimeActivationError(
                "ACTIVATION_EXECUTION_LANE_ROOT_OWNER_INVALID"
            )
        if stat.S_IMODE(info.st_mode) != 0o700:
            raise ProductionRuntimeActivationError(
                "ACTIVATION_EXECUTION_LANE_ROOT_MODE_INVALID"
            )

    @contextmanager
    def acquire(self):
        self._validate_root()
        lock_path = self.root / "production-runtime-activation.lock"

        flags = os.O_RDWR | os.O_CREAT
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW

        try:
            descriptor = os.open(lock_path, flags, 0o600)
        except OSError as exc:
            raise ProductionRuntimeActivationError(
                "ACTIVATION_EXECUTION_LANE_FILE_INVALID"
            ) from exc

        try:
            info = os.fstat(descriptor)
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) != 0o600
            ):
                raise ProductionRuntimeActivationError(
                    "ACTIVATION_EXECUTION_LANE_FILE_INVALID"
                )

            try:
                fcntl.flock(
                    descriptor,
                    fcntl.LOCK_EX | fcntl.LOCK_NB,
                )
            except BlockingIOError as exc:
                raise ProductionRuntimeActivationError(
                    "ACTIVATION_EXECUTION_LANE_BUSY"
                ) from exc

            try:
                yield
            finally:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)

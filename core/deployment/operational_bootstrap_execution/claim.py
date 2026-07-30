"""Canonical atomic adjacent-file permit claim registry."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .models import *


class StrictJsonArtifactReader:
    def read(self, path: Path) -> tuple[str, dict]:
        raw = path.read_text(encoding="utf-8")
        value = json.loads(raw)
        if not isinstance(value, dict) or canonical_json(value) != raw:
            raise OperationalBootstrapExecutionError("NON_CANONICAL_JSON_REJECTED")
        validate_safe(value)
        return raw, value


class AtomicPermitClaimFileRegistry:
    """There is deliberately no delete, reset, or reuse operation."""

    def claim(self, permit_path: Path,
              request: OperationalBootstrapClaimRequest) -> OperationalBootstrapClaimReceipt:
        parent = permit_path.parent
        if parent.is_symlink():
            raise OperationalBootstrapExecutionError("CLAIM_PARENT_SYMLINK_REJECTED")
        os.chmod(parent, 0o700)
        claim_path = permit_path.with_name(permit_path.name + ".claim.json")
        payload = request.as_dict()
        raw = canonical_json(payload).encode()
        try:
            descriptor = os.open(claim_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as exc:
            raise OperationalBootstrapExecutionError("PERMIT_ALREADY_CLAIMED") from exc
        try:
            os.write(descriptor, raw)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        try:
            directory = os.open(parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except OSError:
            pass
        digest = canonical_digest(payload)
        return OperationalBootstrapClaimReceipt(
            "m3-a4b2b2a-claim-" + digest[7:39], claim_path, digest, request)

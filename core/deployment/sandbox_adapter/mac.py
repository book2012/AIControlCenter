"""Constrained local filesystem implementation of the DPL executor port."""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

from core.deployment.contracts import canonical_json_bytes
from core.deployment.executor_contracts import (
    ExecutorOperation,
    create_executor_capability,
    create_executor_result,
    validate_executor_request,
)

_SUPPORTED = {
    ExecutorOperation.VERIFY_SANDBOX_TARGET.value,
    ExecutorOperation.PREPARE_SANDBOX.value,
    ExecutorOperation.COLLECT_EXECUTION_EVIDENCE.value,
}
_ALLOWED_ENVIRONMENTS = {"development", "test", "staging"}
_FORBIDDEN_KEYS = {"argv", "command", "script", "shell"}
_SECRET_MARKERS = ("credential", "password", "private_key", "secret", "token")
_PROTECTED_ROOTS = tuple(
    Path(value) for value in (
        "/System", "/Library", "/Applications", "/usr", "/bin", "/sbin", "/etc"
    )
)


class SandboxAdapterError(ValueError):
    """A redacted sandbox-boundary failure."""


def _digest_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _unsafe_input(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                return True
            normalized = key.lower()
            if normalized in _FORBIDDEN_KEYS or any(
                marker in normalized for marker in _SECRET_MARKERS
            ):
                return True
            if _unsafe_input(child):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_unsafe_input(child) for child in value)
    return False


class MacSandboxAdapter:
    """Materialize deterministic JSON evidence below one injected root."""

    def __init__(
        self,
        *,
        sandbox_root: Path | None,
        authorization: Mapping[str, Any],
        environment: str,
        capability_timestamp: str,
        repository_root: Path | None = None,
    ) -> None:
        self._root = sandbox_root
        self._authorization = copy.deepcopy(dict(authorization))
        self._repository_root = repository_root
        self._capability = create_executor_capability(
            executor_type="mac-sandbox",
            environment=environment,
            target_owner="mac-control-plane",
            operations=sorted(_SUPPORTED),
            capability_timestamp=capability_timestamp,
        )

    def capability(self) -> Mapping[str, Any]:
        return copy.deepcopy(self._capability)

    def execute(
        self, request: Mapping[str, Any], *, result_timestamp: str
    ) -> Mapping[str, Any]:
        request_copy = copy.deepcopy(dict(request))
        reasons = self._request_reasons(request_copy, result_timestamp)
        if reasons:
            return create_executor_result(
                request=request_copy,
                capability=self._capability,
                status="DENIED",
                reason_codes=reasons,
                result_timestamp=result_timestamp,
            )

        try:
            root = self._validated_root()
        except SandboxAdapterError:
            return create_executor_result(
                request=request_copy,
                capability=self._capability,
                status="DENIED",
                reason_codes=("SANDBOX_ROOT_DENIED",),
                result_timestamp=result_timestamp,
            )
        evidence: list[str] = []
        statuses: dict[str, str] = {}
        try:
            for operation in sorted(request_copy["operation_scope"]):
                if operation not in _SUPPORTED:
                    statuses[operation] = "UNAVAILABLE"
                    continue
                statuses[operation] = "ALLOWED"
                if operation == ExecutorOperation.PREPARE_SANDBOX.value:
                    manifest = self._manifest(request_copy)
                    evidence.append(
                        self._write_immutable(root, request_copy, "manifest.json", manifest)
                    )
                elif operation == ExecutorOperation.COLLECT_EXECUTION_EVIDENCE.value:
                    manifest = self._manifest(request_copy)
                    manifest_digest = self._write_immutable(
                        root, request_copy, "manifest.json", manifest
                    )
                    evidence_payload = {
                        "schema_version": "dpl/v1",
                        "adapter_type": "mac-sandbox",
                        "request_id": request_copy["request_id"],
                        "manifest_digest": manifest_digest,
                        "production_authorized": False,
                        "repository_writes": 0,
                        "production_writes": 0,
                        "ubuntu_changes": 0,
                        "network_accesses": 0,
                        "runtime_commands": 0,
                    }
                    evidence.extend(
                        (
                            manifest_digest,
                            self._write_immutable(
                                root, request_copy, "evidence.json", evidence_payload
                            ),
                        )
                    )
        except SandboxAdapterError:
            return create_executor_result(
                request=request_copy,
                capability=self._capability,
                status="DENIED",
                reason_codes=("IMMUTABLE_ARTIFACT_CONFLICT",),
                result_timestamp=result_timestamp,
            )

        overall = "UNAVAILABLE" if "UNAVAILABLE" in statuses.values() else "ALLOWED"
        reasons = ("UNSUPPORTED_OPERATION",) if overall == "UNAVAILABLE" else ()
        return create_executor_result(
            request=request_copy,
            capability=self._capability,
            status=overall,
            reason_codes=reasons,
            result_timestamp=result_timestamp,
            evidence_digests=evidence,
            operation_statuses=statuses,
        )

    def _request_reasons(
        self, request: Mapping[str, Any], validation_timestamp: str
    ) -> tuple[str, ...]:
        if _unsafe_input(request) or _unsafe_input(self._authorization):
            raise SandboxAdapterError("unsafe or unsupported sandbox input")
        report = validate_executor_request(
            request=request,
            capability=self._capability,
            authorization=self._authorization,
            validation_timestamp=validation_timestamp,
        )
        reasons = list(report["reason_codes"])
        if request.get("actor_identity") != self._authorization.get("requester_identity"):
            reasons.append("ACTOR_IDENTITY_MISMATCH")
        if request.get("environment") not in _ALLOWED_ENVIRONMENTS:
            reasons.append("ENVIRONMENT_DENIED")
        if request.get("production_authorized") is not False:
            reasons.append("PRODUCTION_AUTHORIZATION_DENIED")
        if request.get("target_owner") != "mac-control-plane":
            reasons.append("TARGET_OWNER_DENIED")
        return tuple(sorted(set(reasons)))

    def _validated_root(self) -> Path:
        if self._root is None:
            raise SandboxAdapterError("explicit sandbox root is required")
        root = Path(self._root)
        if not root.is_absolute() or root.is_symlink() or not root.is_dir():
            raise SandboxAdapterError("sandbox root is unavailable")
        self._reject_symlink_components(root)
        resolved = root.resolve(strict=True)
        for protected in _PROTECTED_ROOTS:
            if resolved == protected or protected in resolved.parents:
                raise SandboxAdapterError("protected sandbox root is denied")
        if self._repository_root is not None:
            repository = Path(self._repository_root).resolve(strict=True)
            if resolved == repository or repository in resolved.parents:
                raise SandboxAdapterError("repository sandbox root is denied")
        return resolved

    @staticmethod
    def _reject_symlink_components(path: Path) -> None:
        current = Path(path.anchor)
        for part in path.parts[1:]:
            current = current / part
            if current.is_symlink():
                raise SandboxAdapterError("symlink sandbox component is denied")

    @staticmethod
    def _manifest(request: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "schema_version": "dpl/v1",
            "adapter_type": "mac-sandbox",
            "request_id": request["request_id"],
            "authorization_id": request["execution_authorization_id"],
            "capability_id": request["capability_id"],
            "package_digest": request["package_digest"],
            "plan_digest": request["plan_digest"],
            "target_identity": request["target_identity"],
            "target_owner": request["target_owner"],
            "environment": request["environment"],
            "operation_scope": sorted(request["operation_scope"]),
            "actor_identity": request["actor_identity"],
            "production_authorized": False,
        }

    def _write_immutable(
        self, root: Path, request: Mapping[str, Any], name: str, payload: Mapping[str, Any]
    ) -> str:
        relative = PurePosixPath("artifacts", request["request_id"], name)
        if relative.is_absolute() or ".." in relative.parts:
            raise SandboxAdapterError("unsafe artifact path")
        parent = root / relative.parent
        self._mkdir_bounded(root, parent)
        self._reject_symlink_components(parent)
        target = parent / relative.name
        if target.is_symlink():
            raise SandboxAdapterError("symlink artifact is denied")
        content = canonical_json_bytes(payload)
        digest = _digest_bytes(content)
        if target.exists():
            if not target.is_file() or target.read_bytes() != content:
                raise SandboxAdapterError("immutable sandbox artifact conflict")
            if _digest_bytes(target.read_bytes()) != digest:
                raise SandboxAdapterError("sandbox digest verification failed")
            return digest
        temporary = parent / f"{relative.name}.atomic"
        if temporary.exists() or temporary.is_symlink():
            raise SandboxAdapterError("atomic sandbox path conflict")
        with temporary.open("xb") as stream:
            stream.write(content)
            stream.flush()
        temporary.replace(target)
        if target.is_symlink() or target.read_bytes() != content:
            raise SandboxAdapterError("sandbox digest verification failed")
        return digest

    @staticmethod
    def _mkdir_bounded(root: Path, target: Path) -> None:
        try:
            target.relative_to(root)
        except ValueError as error:
            raise SandboxAdapterError("sandbox path escaped root") from error
        current = root
        for part in target.relative_to(root).parts:
            current = current / part
            if current.exists():
                if current.is_symlink() or not current.is_dir():
                    raise SandboxAdapterError("sandbox path component is denied")
            else:
                current.mkdir()

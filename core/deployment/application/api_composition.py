"""Pure DPL v1 API response and audit-evidence composition."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from hashlib import sha256
from typing import Any

from core.deployment.contracts import (
    canonical_json_bytes,
    load_schema_registry,
    sha256_digest,
    validate_contract_payload,
)
from core.deployment.ports import AuditEvidenceSinkPort, ClockPort

_REDACTED = "Request could not be processed; sensitive details withheld."


class DeploymentApiComposer:
    def __init__(self, *, clock: ClockPort, sink: AuditEvidenceSinkPort) -> None:
        self._clock, self._sink = clock, sink

    @staticmethod
    def discover() -> dict[str, Any]:
        registry = load_schema_registry()
        return {
            "schema_version": "dpl/v1",
            "network_resolution": False,
            "contracts": [
                {
                    "name": name,
                    "schema_id": binding.schema_id,
                    "schema_version": binding.schema_version,
                }
                for name, binding in sorted(registry.contracts.items())
            ],
        }

    @staticmethod
    def inspect_package(package: Mapping[str, Any]) -> dict[str, Any]:
        copied = copy.deepcopy(dict(package))
        validate_contract_payload(
            registry=load_schema_registry(),
            contract_name="ImmutableDeploymentPackage",
            payload=copied,
        )
        return {
            "valid": True,
            "contract": "ImmutableDeploymentPackage",
            "package": copied,
            "package_digest": sha256_digest(copied),
        }

    def compose(
        self,
        *,
        operation: str,
        result: Mapping[str, Any],
        actor_identity: str,
        context_identity: str,
        request_identity: str,
        classification: str = "SUCCESS",
        subject_digest: str | None = None,
        error_code: str | None = None,
    ) -> dict[str, Any]:
        identity = {
            "operation": operation,
            "actor_identity": actor_identity,
            "context_identity": context_identity,
            "request_identity": request_identity,
            "subject_digest": subject_digest,
            "result_classification": classification,
        }
        evidence = {
            "schema_version": "dpl/v1",
            "event_id": f"dpl-{sha256(canonical_json_bytes(identity)).hexdigest()}",
            **identity,
            "timestamp": self._clock.now_utc(),
            "read_only": True,
            "production_writes": 0,
            "ubuntu_changes": 0,
            "error": (
                {"code": error_code, "message": _REDACTED}
                if error_code is not None
                else None
            ),
        }
        validate_contract_payload(
            registry=load_schema_registry(),
            contract_name="DeploymentAuditEvidence",
            payload=evidence,
        )
        self._sink.record(copy.deepcopy(evidence))
        response = {
            "schema_version": "dpl/v1",
            "read_only": True,
            "operation": operation,
            "result": copy.deepcopy(dict(result)),
            "audit_evidence": evidence,
        }
        validate_contract_payload(
            registry=load_schema_registry(),
            contract_name="DeploymentApiResponse",
            payload=response,
        )
        return response


__all__ = ("DeploymentApiComposer",)

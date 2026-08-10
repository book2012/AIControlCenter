"""Deterministic, read-only and local-only SEC-02 governance schema registry."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from jsonschema import Draft202012Validator

SCHEMA_FAMILY_VERSION = "governance/v1"
CONTRACT_NAMES = (
    "GovernanceAuthorizationRequest",
    "GovernancePreconditionSnapshot",
    "GovernanceAuthorizationDecision",
    "GovernanceAuthorizationReceipt",
    "GovernanceAuthorizationStateRecord",
    "GovernanceMutationBudget",
    "GovernanceAuthorizationConsumptionReceipt",
    "GovernanceExecutionRequest",
    "GovernanceExecutionReceipt",
    "GovernancePostconditionReport",
    "GovernanceFailureEvidence",
    "GovernanceEvidenceManifest",
    "GovernanceEvidenceBundle",
    "GovernanceAuditEvent",
    "GovernanceGitDocumentationGateReport",
    "GovernanceApiEnvelope",
)
_FILENAMES = (
    "governance-authorization-request.json",
    "governance-precondition-snapshot.json",
    "governance-authorization-decision.json",
    "governance-authorization-receipt.json",
    "governance-authorization-state-record.json",
    "governance-mutation-budget.json",
    "governance-authorization-consumption-receipt.json",
    "governance-execution-request.json",
    "governance-execution-receipt.json",
    "governance-postcondition-report.json",
    "governance-failure-evidence.json",
    "governance-evidence-manifest.json",
    "governance-evidence-bundle.json",
    "governance-audit-event.json",
    "governance-git-documentation-gate-report.json",
    "governance-api-envelope.json",
)


class GovernanceContractRegistryError(RuntimeError):
    """A local governance schema resource is missing or invalid."""


class UnknownGovernanceContractError(GovernanceContractRegistryError, KeyError):
    """The requested name is outside the frozen v1 contract family."""


@dataclass(frozen=True, slots=True)
class ContractSchemaBinding:
    contract_name: str
    resource_name: str
    schema_id: str
    schema_version: str = SCHEMA_FAMILY_VERSION


@dataclass(frozen=True, slots=True)
class GovernanceContractRegistry:
    schema_root: Path
    contracts: Mapping[str, ContractSchemaBinding]
    _schemas: Mapping[str, Mapping[str, Any]]

    @property
    def contract_names(self) -> tuple[str, ...]:
        return tuple(self.contracts)

    def contract_binding(self, contract_name: str) -> ContractSchemaBinding:
        try:
            return self.contracts[contract_name]
        except KeyError as error:
            raise UnknownGovernanceContractError(contract_name) from error

    def contract_schema(self, contract_name: str) -> dict[str, Any]:
        """Return an isolated copy; callers cannot mutate canonical registry data."""
        binding = self.contract_binding(contract_name)
        return deepcopy(dict(self._schemas[binding.schema_id]))


def _has_remote_ref(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            (key == "$ref" and isinstance(child, str) and child.startswith(("http://", "https://")))
            or _has_remote_ref(child)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return any(_has_remote_ref(child) for child in value)
    return False


def load_contract_registry(*, schema_root: Path | None = None) -> GovernanceContractRegistry:
    root = (schema_root or Path(__file__).resolve().parent / "schemas" / "v1").resolve()
    bindings: dict[str, ContractSchemaBinding] = {}
    schemas: dict[str, Mapping[str, Any]] = {}
    for contract_name, resource_name in zip(CONTRACT_NAMES, _FILENAMES, strict=True):
        candidate = (root / resource_name).resolve()
        if candidate.parent != root:
            raise GovernanceContractRegistryError("Schema resource escaped registry root.")
        try:
            schema = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise GovernanceContractRegistryError("Unable to load governance schema resource.") from error
        if not isinstance(schema, dict) or _has_remote_ref(schema):
            raise GovernanceContractRegistryError("Governance schema resource policy failed.")
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or schema_id in schemas:
            raise GovernanceContractRegistryError("Governance schema identity is invalid or duplicated.")
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as error:
            raise GovernanceContractRegistryError("Governance schema meta-validation failed.") from error
        bindings[contract_name] = ContractSchemaBinding(contract_name, resource_name, schema_id)
        schemas[schema_id] = MappingProxyType(schema)
    return GovernanceContractRegistry(root, MappingProxyType(bindings), MappingProxyType(schemas))


def load_schema_registry(*, schema_root: Path | None = None) -> GovernanceContractRegistry:
    """Repository-convention alias for the governance contract registry loader."""
    return load_contract_registry(schema_root=schema_root)

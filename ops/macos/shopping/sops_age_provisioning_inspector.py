"""Read-only SOPS/age provisioning planner using injected observations only."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import jsonschema

from core.secrets.provisioning import ProvisioningPlan, Readiness, plan_for
from ops.macos.shopping.sops_age_backend import (
    BackendDefinitionError,
    DEFINITION_PATH as BACKEND_DEFINITION_PATH,
    validate_definition as validate_backend_definition,
)
from ops.macos.shopping.secret_provisioning_observations import (
    FileObservation,
    ReadinessState,
    RuntimeProvisioningObservations,
)

ROOT = Path(__file__).resolve().parents[3]
PROVISIONING_DEFINITION_PATH = ROOT / "config/shopping-secret-provisioning.json"
PROVISIONING_SCHEMA_PATH = ROOT / "config/schemas/shopping-secret-provisioning.schema.json"


class ProvisioningDefinitionError(ValueError):
    """Canonical provisioning metadata is malformed."""


@dataclass(frozen=True, slots=True)
class ProvisioningObservations:
    sops_executable_present: bool
    age_executable_present: bool
    age_keygen_executable_present: bool
    control_plane_identity_metadata_safe_present: bool
    control_plane_recipient_metadata_registered_valid: bool
    offline_recovery_inbox_ready: bool
    offline_recovery_public_metadata_registered_valid: bool


def load_provisioning_definition(
    path: Path = PROVISIONING_DEFINITION_PATH,
) -> dict[str, Any]:
    definition = json.loads(path.read_text(encoding="utf-8"))
    validate_provisioning_definition(definition)
    return definition


def validate_provisioning_definition(definition: object) -> None:
    try:
        with PROVISIONING_SCHEMA_PATH.open(encoding="utf-8") as stream:
            schema = json.load(stream)
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(schema).validate(definition)
    except (OSError, json.JSONDecodeError, jsonschema.SchemaError, jsonschema.ValidationError) as exc:
        raise ProvisioningDefinitionError("provisioning definition is invalid") from exc


class SopsAgeProvisioningInspector:
    def __init__(
        self,
        provisioning_definition: Mapping[str, Any],
        backend_definition: Mapping[str, Any],
        observations: ProvisioningObservations,
        *,
        control_plane_home: Path,
    ) -> None:
        self._definition = dict(provisioning_definition)
        self._backend_definition = dict(backend_definition)
        self._observations = observations
        # Portable injection is retained as an explicit boundary; no ambient home lookup.
        self._control_plane_home = control_plane_home

    def inspect(self) -> tuple[ProvisioningPlan, ...]:
        try:
            validate_provisioning_definition(self._definition)
            validate_backend_definition(self._backend_definition)
            if self._backend_definition["definition_id"] != self._definition["backend_definition_id"]:
                raise ProvisioningDefinitionError("backend definition reference does not match")
        except (ProvisioningDefinitionError, BackendDefinitionError, KeyError):
            return self._malformed_plans()

        observed = self._observations
        identity_ready = observed.control_plane_identity_metadata_safe_present
        states = {
            "SOPS_PRESENT": (Readiness.READY if observed.sops_executable_present else Readiness.MISSING, ()),
            "AGE_TOOLING_PRESENT": (Readiness.READY if observed.age_executable_present and observed.age_keygen_executable_present else Readiness.MISSING, ()),
            "CONTROL_PLANE_IDENTITY_PRESENT": (
                Readiness.READY if identity_ready else (Readiness.BLOCKED if not observed.age_keygen_executable_present else Readiness.MISSING),
                () if identity_ready or observed.age_keygen_executable_present else ("AGE_KEYGEN_TOOLING_UNAVAILABLE",)),
            "CONTROL_PLANE_RECIPIENT_VALID": (
                Readiness.READY if observed.control_plane_recipient_metadata_registered_valid else (Readiness.MISSING if identity_ready else Readiness.BLOCKED),
                () if identity_ready else ("CONTROL_PLANE_IDENTITY_NOT_READY",)),
            "OFFLINE_RECOVERY_RECIPIENT_VALID": (
                Readiness.READY if observed.offline_recovery_public_metadata_registered_valid else Readiness.MISSING, ()),
            "OFFLINE_RECOVERY_INBOX_READY": (
                Readiness.READY if observed.offline_recovery_inbox_ready else Readiness.MISSING,
                (),
            ),
        }
        return tuple(
            plan_for(
                schema_version=self._definition["schema_version"],
                backend_definition_id=self._definition["backend_definition_id"],
                action=item["action_id"],
                readiness=readiness,
                missing_prerequisites=(
                    prerequisites if readiness is Readiness.BLOCKED
                    else ((item["missing_reason_code"],) if readiness is Readiness.MISSING else ())
                ),
            )
            for item in self._definition["actions"]
            for readiness, prerequisites in (states[item["planner_rule"]],)
        )

    def inspect_readiness_composition(
        self, observations: RuntimeProvisioningObservations
    ) -> dict[str, Any]:
        """Project injected postconditions without reading values or granting authority."""
        materialization_implemented = self._definition.get("materialization_implemented") is True
        facts: dict[str, dict[str, Any]] = {
            "sops": self._executable_fact(observations.sops),
            "age": self._executable_fact(observations.age),
            "age_keygen": self._executable_fact(observations.age_keygen),
            "control_plane_identity": self._file_fact(observations.control_plane_identity),
            "control_plane_recipient_registration": self._boolean_fact(
                observations.control_plane_recipient_registered, "registered"
            ),
            "offline_recovery_inbox": {
                **self._file_fact(observations.offline_recovery_inbox),
                "fixed_canonical_artifact": True,
                "contents_inspected": False,
            },
            "offline_recovery_recipient_registration": self._boolean_fact(
                observations.offline_recovery_recipient_registered, "registered"
            ),
            "secret_payload": {
                "state": self._configured_state(
                    observations.secret_payload_configured,
                    observations.secret_payload_ready,
                ),
                "configured": observations.secret_payload_configured,
                "ready": observations.secret_payload_ready,
            },
            "secret_materialization": {
                "state": (
                    ReadinessState.MISSING.value
                    if not materialization_implemented
                    else ReadinessState.BLOCKED.value
                ),
                "implemented": materialization_implemented,
                "ready": False,
            },
            "runtime_dependencies": {
                "state": self._configured_state(
                    observations.runtime_dependencies_configured,
                    observations.runtime_dependencies_ready,
                ),
                "configured": observations.runtime_dependencies_configured,
                "ready": observations.runtime_dependencies_ready,
            },
            "mariadb_continuity": {
                "state": ReadinessState.BLOCKED.value,
                "reason_codes": ["MARIADB_HISTORICAL_CREDENTIAL_CONTINUITY_UNRESOLVED"],
                "credential_values_inspected": False,
                "blocks": [
                    "DB_SECRET_PAYLOAD", "DB_SECRET_MATERIALIZATION",
                    "DB_DEPENDENT_VALIDATION", "WORDPRESS_WOOCOMMERCE_DB_CUTOVER",
                    "RUNTIME_CUTOVER", "SHOPPING_RUNTIME_ACTIVATED",
                ],
            },
        }
        activation_blocked = (
            facts["mariadb_continuity"]["state"] != ReadinessState.READY.value
            or facts["secret_payload"]["state"] != ReadinessState.READY.value
            or facts["secret_materialization"]["state"] != ReadinessState.READY.value
            or facts["runtime_dependencies"]["state"] != ReadinessState.READY.value
        )
        facts["runtime_activation"] = {
            "state": ReadinessState.BLOCKED.value if activation_blocked else ReadinessState.READY.value,
            "ready": not activation_blocked,
            "activated": False,
        }
        reason_codes = sorted({
            reason
            for fact in facts.values()
            for reason in fact.get("reason_codes", [])
        })
        for name, fact in facts.items():
            if fact["state"] != ReadinessState.READY.value and not fact.get("reason_codes"):
                reason_codes.append(f"{name.upper()}_{fact['state']}")
        return {
            "schema_version": "1.0",
            "inspection": "READ_ONLY",
            "owner": "MAC_MINI_M4_AICONTROLCENTER_CONTROL_PLANE",
            "value_free": True,
            "secret_values_read": False,
            "mutation_authority": False,
            "facts": facts,
            "overall_state": (
                ReadinessState.READY.value
                if all(fact["state"] == ReadinessState.READY.value for fact in facts.values())
                else ReadinessState.BLOCKED.value
            ),
            "reason_codes": sorted(set(reason_codes)),
        }

    @staticmethod
    def _configured_state(configured: bool, ready: bool) -> str:
        if not configured:
            return (
                ReadinessState.MALFORMED if ready else ReadinessState.MISSING
            ).value
        return (ReadinessState.READY if ready else ReadinessState.BLOCKED).value

    @staticmethod
    def _executable_fact(observation: Any) -> dict[str, Any]:
        state = ReadinessState.READY if observation.ready else (
            ReadinessState.MISSING if not observation.present else ReadinessState.UNSAFE
        )
        return {
            "state": state.value, "present": observation.present,
            "trusted": observation.trusted, "executable": observation.executable,
            "ready": observation.ready,
        }

    @staticmethod
    def _file_fact(observation: FileObservation) -> dict[str, Any]:
        state = ReadinessState.READY if observation.ready else (
            ReadinessState.MISSING if not observation.regular_file and not observation.symlink_rejected
            else ReadinessState.UNSAFE
        )
        return {
            "state": state.value, "present": observation.regular_file or observation.symlink_rejected,
            "regular_file": observation.regular_file,
            "symlink_rejected": observation.symlink_rejected,
            "expected_ownership": observation.expected_ownership,
            "safe_mode": observation.safe_mode, "nonempty": observation.nonempty,
            "ready": observation.ready,
        }

    @staticmethod
    def _boolean_fact(ready: bool, name: str) -> dict[str, Any]:
        return {
            "state": (ReadinessState.READY if ready else ReadinessState.MISSING).value,
            name: ready, "ready": ready,
        }

    def _malformed_plans(self) -> tuple[ProvisioningPlan, ...]:
        return (plan_for(
            schema_version="1.0", backend_definition_id="shopping-secret-backend",
            action="UNKNOWN_ACTION", readiness=Readiness.MALFORMED,
            missing_prerequisites=("MALFORMED_CONFIGURATION",),
        ),)


def load_backend_definition(path: Path = BACKEND_DEFINITION_PATH) -> dict[str, Any]:
    definition = json.loads(path.read_text(encoding="utf-8"))
    validate_backend_definition(definition)
    return definition


__all__ = (
    "ProvisioningDefinitionError", "ProvisioningObservations",
    "SopsAgeProvisioningInspector", "load_backend_definition",
    "load_provisioning_definition", "validate_provisioning_definition",
)

"""Pure conversion of validated read-side evidence into a safe action graph."""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from pathlib import PurePosixPath
from typing import Any

from core.deployment.contracts import (
    load_schema_registry,
    sha256_digest,
    validate_contract_payload,
    verify_digest,
)

from .graph import stable_topological_order
from .validation import validate_deployment_plan_report

_ACTION_TYPES = (
    "VALIDATE_PACKAGE",
    "VERIFY_DEPENDENCY_POLICY",
    "VERIFY_MAC_INVENTORY",
    "VERIFY_INGRESS_READINESS",
    "VERIFY_TARGET_PROFILE",
    "PREPARE_AUDIT_EVIDENCE",
    "REQUIRE_APPROVAL",
    "RECORD_BLOCKER",
)
_FORBIDDEN_KEYS = {
    "argv", "command", "environment", "execute", "execution", "password",
    "private_key", "script", "secret", "shell", "ssh_command", "token",
}
_REQUIRED_INVENTORY = {
    "git-repository", "runtime-metadata", "mac-production-profile",
    "launchd-services", "host-caddy", "public-edge-policy",
}


class PlanInputError(ValueError):
    """Raised without echoing potentially sensitive input content."""


def _security_check(value: Any, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise PlanInputError("unsafe or unsupported plan input")
            normalized = key.lower()
            if normalized in _FORBIDDEN_KEYS or any(
                marker in normalized
                for marker in ("credential", "secret_key", "_password", "_secret", "_token")
            ):
                raise PlanInputError("unsafe or unsupported plan input")
            if isinstance(child, str) and (
                normalized.endswith("_path") or normalized in {"path", "reference"}
            ):
                pure = PurePosixPath(child)
                if pure.is_absolute() or ".." in pure.parts:
                    raise PlanInputError("unsafe or unsupported plan input")
            _security_check(child, (*path, key))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            _security_check(child, path)


def _action_id(plan_seed: str, action_type: str) -> str:
    return "act-" + sha256_digest({"plan_seed": plan_seed, "type": action_type})[7:31]


class DeploymentPlanBuilder:
    """Build schema-valid plans without I/O, mutation, or authorization."""

    def build(
        self,
        *,
        package: Mapping[str, Any],
        package_digest: str,
        mac_inventory: Mapping[str, Any],
        ingress_readiness: Mapping[str, Any],
        dependency_policy: Mapping[str, Any],
        target_profile: Mapping[str, Any],
        actor_identity: str,
        context_identity: str,
        execution_authorized: bool = False,
        production_authorized: bool = False,
    ) -> dict[str, Any]:
        values = (package, mac_inventory, ingress_readiness, dependency_policy, target_profile)
        for value in values:
            _security_check(value)
        if execution_authorized or production_authorized:
            raise PlanInputError("authorization requests are prohibited in dry-run planning")

        package_copy, inventory_copy, ingress_copy, policy_copy, target_copy = (
            copy.deepcopy(dict(value)) for value in values
        )
        registry = load_schema_registry()
        validation_failures: list[str] = []
        for name, payload, code in (
            ("ImmutableDeploymentPackage", package_copy, "PACKAGE_INVALID"),
            ("InventoryResult", inventory_copy, "MAC_INVENTORY_INVALID"),
            ("IngressReadinessReport", ingress_copy, "INGRESS_EVIDENCE_INVALID"),
            ("DependencyBoundaryReport", policy_copy, "DEPENDENCY_POLICY_INVALID"),
            ("DeploymentTargetProfile", target_copy, "TARGET_PROFILE_INVALID"),
        ):
            try:
                validate_contract_payload(registry=registry, contract_name=name, payload=payload)
            except Exception:
                validation_failures.append(code)

        if not verify_digest(package_copy, package_digest):
            validation_failures.append("PACKAGE_DIGEST_MISMATCH")

        blockers = list(validation_failures)
        warnings: list[str] = []
        if policy_copy.get("overall_result") != "PASS":
            blockers.append("DEPENDENCY_POLICY_NOT_PASS")
        ingress_status = ingress_copy.get("overall_status")
        if ingress_status in {"NOT_READY", "INVALID", "UNAVAILABLE"}:
            blockers.append(f"INGRESS_{ingress_status}")
        elif ingress_status == "DEGRADED":
            warnings.append("INGRESS_OPTIONAL_OBSERVATION_DEGRADED")
        elif ingress_status != "READY":
            blockers.append("INGRESS_INCOMPLETE")

        items = {
            item.get("component_id"): item
            for item in inventory_copy.get("items", [])
            if isinstance(item, Mapping)
        }
        for component in sorted(_REQUIRED_INVENTORY):
            if items.get(component, {}).get("state") != "present":
                blockers.append(f"REQUIRED_INVENTORY_UNAVAILABLE:{component}")

        owner = target_copy.get("control_plane_owner")
        if owner != "aicontrolcenter" or target_copy.get("platform") != "macos":
            blockers.append("TARGET_OWNER_NOT_MAC_CONTROL_PLANE")
        if target_copy.get("public_edge_owner") != "host-caddy":
            blockers.append("HOST_CADDY_NOT_SOLE_PUBLIC_EDGE")
        if target_copy.get("cms_owner") == "ubuntu" or target_copy.get("commerce_owner") == "ubuntu":
            blockers.append("UBUNTU_APPLICATION_OWNERSHIP_PROHIBITED")
        if target_copy.get("control_plane_owner") == "ubuntu":
            blockers.append("UBUNTU_CONTROL_PLANE_PROHIBITED")

        blockers = sorted(set(blockers))
        if ingress_copy.get("warnings"):
            warnings.append("INGRESS_EVIDENCE_WARNING_PRESENT")
        warnings = sorted(set(warnings))
        evidence_digests = {
            "dependency_policy": sha256_digest(policy_copy),
            "ingress_readiness": sha256_digest(ingress_copy),
            "mac_inventory": sha256_digest(inventory_copy),
        }
        identity = {
            "schema_version": "dpl/v1",
            "package_digest": package_digest,
            "target_profile": target_copy,
            "actor_identity": actor_identity,
            "context_identity": context_identity,
            "evidence_digests": evidence_digests,
        }
        seed = sha256_digest(identity)
        plan_id = "plan-" + seed[7:39]

        definitions: list[tuple[str, tuple[str, ...], str, bool]] = [
            ("VALIDATE_PACKAGE", (), "LOW", False),
            ("VERIFY_DEPENDENCY_POLICY", ("VALIDATE_PACKAGE",), "LOW", False),
            ("VERIFY_MAC_INVENTORY", ("VALIDATE_PACKAGE",), "LOW", False),
            ("VERIFY_INGRESS_READINESS", ("VALIDATE_PACKAGE",), "LOW", False),
            ("VERIFY_TARGET_PROFILE", ("VALIDATE_PACKAGE",), "MEDIUM", False),
            (
                "PREPARE_AUDIT_EVIDENCE",
                ("VERIFY_DEPENDENCY_POLICY", "VERIFY_INGRESS_READINESS",
                 "VERIFY_MAC_INVENTORY", "VERIFY_TARGET_PROFILE"),
                "LOW",
                False,
            ),
        ]
        definitions.append(
            (
                "RECORD_BLOCKER" if blockers else "REQUIRE_APPROVAL",
                ("PREPARE_AUDIT_EVIDENCE",),
                "HIGH" if blockers else "MEDIUM",
                not blockers,
            )
        )
        ids = {kind: _action_id(seed, kind) for kind, *_ in definitions}
        actions = [
            {
                "action_id": ids[kind],
                "action_type": kind,
                "target": target_copy["target_id"],
                "dependency_ids": sorted(ids[item] for item in dependencies),
                "prerequisite_state": "SATISFIED" if not blockers else "BLOCKED",
                "result_expectation": {
                    "RECORD_BLOCKER": "Blockers remain visible; no execution occurs.",
                    "REQUIRE_APPROVAL": "Human approval is required; execution remains unauthorized.",
                }.get(kind, "Read-side evidence is verified without side effects."),
                "risk": risk,
                "approval_required": approval,
                "execution_authorized": False,
                "evidence_references": sorted(evidence_digests),
            }
            for kind, dependencies, risk, approval in definitions
        ]
        by_id = {item["action_id"]: item for item in actions}
        actions = [by_id[item] for item in stable_topological_order(actions)]
        edges = sorted(
            (
                {"from_action_id": dependency, "to_action_id": action["action_id"]}
                for action in actions for dependency in action["dependency_ids"]
            ),
            key=lambda item: (item["from_action_id"], item["to_action_id"]),
        )
        status = "BLOCKED" if blockers else "READY_FOR_APPROVAL"
        plan: dict[str, Any] = {
            "schema_version": "dpl/v1",
            "plan_id": plan_id,
            "plan_digest": "",
            "package_digest": package_digest,
            "target_identity": target_copy["target_id"],
            "target_profile": target_copy,
            "read_only": True,
            "dry_run": True,
            "execution_authorized": False,
            "production_authorized": False,
            "actions": actions,
            "dependency_edges": edges,
            "prerequisites": sorted(
                {"PACKAGE_VALID", "DEPENDENCY_POLICY_PASS", "MAC_INVENTORY_AVAILABLE",
                 "INGRESS_READY", "TARGET_PROFILE_VALID"}
            ),
            "blocking_reasons": blockers,
            "risk_level": "HIGH" if blockers else "MEDIUM",
            "approval_required": not blockers,
            "evidence_digests": evidence_digests,
            "warnings": warnings,
            "overall_status": status,
            "production_writes": 0,
            "ubuntu_changes": 0,
        }
        semantic = copy.deepcopy(plan)
        semantic.pop("plan_digest")
        plan["plan_digest"] = sha256_digest(semantic)
        report = {
            "schema_version": "dpl/v1",
            "read_only": True,
            "dry_run": True,
            "plan": plan,
            "overall_status": status,
            "blocking_reasons": blockers,
            "warnings": warnings,
            "production_writes": 0,
            "ubuntu_changes": 0,
        }
        validate_deployment_plan_report(report)
        return report


__all__ = ("DeploymentPlanBuilder", "PlanInputError", "_ACTION_TYPES")

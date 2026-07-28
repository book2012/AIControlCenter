"""Pure deterministic composition of the DPL v1 Mac inventory."""

from __future__ import annotations

import copy
from collections.abc import Callable, Mapping
from typing import Any

from core.deployment.contracts import (
    load_schema_registry,
    validate_contract_payload,
)
from core.deployment.ports import (
    CaddyDesiredStatePort,
    ClockPort,
    ColimaContractPort,
    ComposeDesiredStatePort,
    GitIdentityPort,
    LaunchdObservationPort,
    RuntimeMetadataPort,
)

_ORDER = (
    "git-repository",
    "runtime-metadata",
    "mac-production-profile",
    "launchd-services",
    "host-caddy",
    "colima-commerce",
    "compose-commerce",
    "wordpress",
    "woocommerce",
    "public-edge-policy",
)
_REDACTED_MESSAGE = "Observation failed; implementation details withheld."


def _safe_item(component_id: str, component_type: str, raw: Mapping[str, Any]) -> dict[str, Any]:
    copied = copy.deepcopy(dict(raw))
    state = copied.pop("state", "present")
    observed = copied.pop("observed", state not in {"unknown", "unavailable"})
    evidence = copied.pop("evidence", [])
    errors = copied.pop("errors", [])
    if state not in {"present", "absent", "unknown", "degraded", "unavailable"}:
        raise ValueError("unsupported component state")
    return {
        "component_id": component_id,
        "component_type": component_type,
        "observed": bool(observed),
        "state": state,
        "details": copied,
        "evidence": copy.deepcopy(evidence),
        "errors": copy.deepcopy(errors),
    }


def _unavailable(component_id: str, component_type: str) -> dict[str, Any]:
    return {
        "component_id": component_id,
        "component_type": component_type,
        "observed": False,
        "state": "unavailable",
        "details": {},
        "evidence": [],
        "errors": [{"code": "observation-unavailable", "message": _REDACTED_MESSAGE}],
    }


class MacInventoryService:
    def __init__(
        self,
        *,
        git: GitIdentityPort,
        runtime: RuntimeMetadataPort,
        launchd: LaunchdObservationPort,
        caddy: CaddyDesiredStatePort,
        colima: ColimaContractPort,
        compose: ComposeDesiredStatePort,
        clock: ClockPort,
    ) -> None:
        self._sources: dict[str, tuple[str, Callable[[], Mapping[str, Any]]]] = {
            "git-repository": ("repository", git.observe_git_identity),
            "runtime-metadata": ("runtime-metadata", runtime.observe_runtime_metadata),
            "launchd-services": ("service-supervision", launchd.observe_launchd),
            "host-caddy": ("public-edge", caddy.observe_caddy_desired_state),
            "colima-commerce": ("runtime-contract", colima.observe_colima_contract),
            "compose-commerce": ("compose-project", compose.observe_compose_desired_state),
        }
        self._clock = clock

    def _observe(self, component_id: str) -> dict[str, Any]:
        component_type, operation = self._sources[component_id]
        try:
            raw = operation()
            if not isinstance(raw, Mapping):
                raise ValueError("adapter result must be an object")
            return _safe_item(component_id, component_type, raw)
        except Exception:
            return _unavailable(component_id, component_type)

    def collect(self) -> dict[str, Any]:
        observed = {key: self._observe(key) for key in self._sources}
        profile_ok = all(
            observed[key]["state"] == "present"
            for key in ("git-repository", "runtime-metadata", "launchd-services")
        )
        observed["mac-production-profile"] = _safe_item(
            "mac-production-profile",
            "control-plane-profile",
            {
                "state": "present" if profile_ok else "degraded",
                "profile": "mac-standalone-production",
                "host_role": "brain",
                "control_plane_owner": "aicontrolcenter",
                "ubuntu_dependency": False,
                "evidence": [{"kind": "repository-config", "reference": "config/services/mac-standalone-production.json"}],
            },
        )
        compose_details = observed["compose-commerce"]["details"]
        compose_present = observed["compose-commerce"]["state"] == "present"
        observed["wordpress"] = _safe_item(
            "wordpress", "cms-engine", {
                "state": "present" if compose_present and compose_details.get("wordpress") else "degraded",
                "engine": "wordpress",
                "owner": "wordpress",
                "business_logic_owner": "aicontrolcenter",
                "exposure": compose_details.get("wordpress_exposure", "unknown"),
                "evidence": [{"kind": "compose-desired-state", "reference": "deploy/shopping/compose.yaml"}],
            }
        )
        observed["woocommerce"] = _safe_item(
            "woocommerce", "commerce-engine", {
                "state": "present" if compose_present and compose_details.get("woocommerce") else "degraded",
                "engine": "woocommerce",
                "owner": "woocommerce",
                "business_logic_owner": "aicontrolcenter",
                "ingress": "behind-host-caddy",
                "evidence": [{"kind": "compose-desired-state", "reference": "deploy/shopping/compose.yaml"}],
            }
        )
        edge_ok = (
            observed["host-caddy"]["state"] == "present"
            and observed["host-caddy"]["details"].get("sole_public_edge") is True
            and observed["colima-commerce"]["details"].get("public_ingress_owner") == "host-caddy"
            and compose_details.get("direct_public_ports") is False
        )
        observed["public-edge-policy"] = _safe_item(
            "public-edge-policy", "policy", {
                "state": "present" if edge_ok else "degraded",
                "owner": "host-caddy",
                "sole_public_edge": edge_ok,
                "direct_public_service_ports": False if edge_ok else "unknown",
                "live_network_test_performed": False,
                "evidence": [
                    {"kind": "caddy-desired-state", "reference": "ops/macos/caddy/Caddyfile"},
                    {"kind": "colima-contract", "reference": "ops/macos/colima/commerce-runtime.json"},
                    {"kind": "compose-desired-state", "reference": "deploy/shopping/compose.yaml"},
                ],
            }
        )
        payload = {
            "schema_version": "dpl/v1",
            "read_only": True,
            "captured_at": self._clock.now_utc(),
            "target": {
                "platform": "macos",
                "role": "control-plane",
                "profile": "mac-standalone-production",
            },
            "items": [observed[key] for key in _ORDER],
        }
        validate_contract_payload(
            registry=load_schema_registry(),
            contract_name="InventoryResult",
            payload=payload,
        )
        return payload


__all__ = ("MacInventoryService",)

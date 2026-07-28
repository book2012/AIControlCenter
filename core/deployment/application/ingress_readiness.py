"""Deterministic, read-only ingress desired-state correlation."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any

from core.deployment.contracts import load_schema_registry, validate_contract_payload
from core.deployment.ports import IngressContractPort, IngressEvidencePort

_COMPONENTS = ("caddy", "colima-commerce", "compose-commerce", "ingress-contract")
_REDACTED = "Evidence is unavailable or invalid; details withheld."


class IngressReadinessService:
    def __init__(
        self,
        *,
        contract: IngressContractPort,
        caddy: IngressEvidencePort,
        colima: IngressEvidencePort,
        compose: IngressEvidencePort,
    ) -> None:
        self._contract, self._sources = contract, {
            "caddy": caddy, "colima-commerce": colima, "compose-commerce": compose
        }

    def evaluate(self) -> dict[str, Any]:
        registry = load_schema_registry()
        try:
            desired = copy.deepcopy(dict(self._contract.read_ingress_contract()))
            validate_contract_payload(
                registry=registry, contract_name="IngressContract", payload=desired
            )
        except Exception:
            return self._report("INVALID", {}, [], [], [_REDACTED], [])

        observed: dict[str, Mapping[str, Any]] = {}
        unavailable: list[str] = []
        for name, source in self._sources.items():
            try:
                value = source.observe()
                if not isinstance(value, Mapping):
                    raise ValueError
                observed[name] = copy.deepcopy(dict(value))
            except Exception:
                unavailable.append(name)
        if unavailable:
            warnings = [f"{name}: {_REDACTED}" for name in sorted(unavailable)]
            status = "UNAVAILABLE" if len(unavailable) == len(self._sources) else "DEGRADED"
            return self._report(status, observed, [], [], [], warnings)

        canonical_port = desired["upstream"]["port"]
        source = desired["upstream"]["port_source"]
        caddy, colima, compose = (
            observed["caddy"], observed["colima-commerce"], observed["compose-commerce"]
        )
        normalized = {
            "caddy": f"{caddy.get('host')}:{caddy.get('port')}",
            "colima-commerce": f"{colima.get('host')}:{colima.get('port') or canonical_port}",
            "compose-commerce": f"{compose.get('host')}:{compose.get('port') or canonical_port}",
        }
        definitions = (
            ("public-edge-owner", caddy.get("owner") == desired["public_edge"]["owner"]
             and colima.get("public_edge_owner") == desired["public_edge"]["owner"]),
            ("direct-public-ports-disabled", compose.get("direct_public_ports") is False
             and desired["public_edge"]["direct_public_application_ports"] is False),
            ("caddy-loopback", caddy.get("host") in {"127.0.0.1", "localhost", "::1"}),
            ("caddy-commerce-port", caddy.get("port") == canonical_port),
            ("commerce-compose-port", colima.get("port_source") == source
             and compose.get("port_source") == source
             and (colima.get("port") or canonical_port) == (compose.get("port") or canonical_port)),
            ("wordpress-loopback", compose.get("host") in {"127.0.0.1", "localhost", "::1"}),
            ("mariadb-not-published", compose.get("database_host_published") is False),
            ("mac-runtime-owner", colima.get("runtime_owner") == desired["runtime"]["owner"]),
            ("ubuntu-runtime-prohibited", colima.get("ubuntu_runtime_allowed") is False),
            ("engine-ownership", compose.get("wordpress") is True
             and compose.get("woocommerce") is True
             and {"wordpress", "woocommerce"}.issubset(set(colima.get("allowed_workloads", [])))),
        )
        evidence = sorted({
            item["reference"]
            for value in observed.values()
            for item in value.get("evidence", [])
            if isinstance(item, Mapping) and isinstance(item.get("reference"), str)
        } | {"config/deployment/ingress.json"})
        checks = [{
            "check_id": check_id,
            "status": "PASS" if passed else "FAIL",
            "message": "Desired-state evidence is aligned." if passed else "Desired-state evidence does not match.",
            "evidence_references": evidence,
        } for check_id, passed in sorted(definitions)]
        reasons = sorted(check["check_id"] for check in checks if check["status"] == "FAIL")
        return self._report(
            "READY" if not reasons else "NOT_READY", observed, checks, reasons, [], [],
            normalized=normalized, evidence=evidence
        )

    @staticmethod
    def _report(
        status: str,
        observed: Mapping[str, Any],
        checks: list[dict[str, Any]],
        reasons: list[str],
        errors: list[str],
        warnings: list[str],
        *,
        normalized: Mapping[str, str] | None = None,
        evidence: list[str] | None = None,
    ) -> dict[str, Any]:
        payload = {
            "schema_version": "dpl/v1",
            "read_only": True,
            "overall_status": status,
            "evaluated_components": sorted(set(observed) | {"ingress-contract"}),
            "normalized_endpoint_identities": dict(sorted((normalized or {}).items())),
            "checks": sorted(checks, key=lambda item: item["check_id"]),
            "mismatch_reasons": sorted(reasons),
            "evidence_references": sorted(evidence or ["config/deployment/ingress.json"]),
            "errors": sorted(errors),
            "warnings": sorted(warnings),
            "production_writes": 0,
            "ubuntu_changes": 0,
        }
        validate_contract_payload(
            registry=load_schema_registry(),
            contract_name="IngressReadinessReport",
            payload=payload,
        )
        return payload


__all__ = ("IngressReadinessService",)

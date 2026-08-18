import ast
from dataclasses import fields
from pathlib import Path

import pytest

from core.secrets.mariadb_continuity_auth_plugin import (
    AUTH_PLUGIN_STATE,
    AUTHORITATIVE_EVIDENCE_AVAILABLE,
    PYMYSQL_COMPATIBILITY_ESTABLISHED,
    AuthPluginState,
    CanonicalAuthPluginReadiness,
    ExternalEvidenceClass,
    ExternalEvidenceDescriptor,
    HistoricalAuthPluginEvidenceContract,
    RuntimeAuthPluginEvidence,
    RuntimeEvidenceState,
    canonical_auth_plugin_readiness,
    canonical_historical_auth_plugin_evidence_contract,
)


FILE = Path(__file__).parents[1] / "core/secrets/mariadb_continuity_auth_plugin.py"


def imported_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0].lower() for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0].lower())
    return roots


def test_canonical_plugin_truth_is_closed_and_unresolved():
    assert tuple(AuthPluginState) == (AuthPluginState.UNRESOLVED,)
    assert AUTH_PLUGIN_STATE == "UNRESOLVED"
    assert AUTHORITATIVE_EVIDENCE_AVAILABLE is False
    assert PYMYSQL_COMPATIBILITY_ESTABLISHED is False
    current = canonical_auth_plugin_readiness()
    assert current.auth_plugin_state is AuthPluginState.UNRESOLVED
    assert current.authoritative_evidence_available is False
    assert current.pymysql_compatibility_established is False
    assert current.ready is False


@pytest.mark.parametrize("override", ({"authoritative_evidence_available": True}, {"pymysql_compatibility_established": True}, {"ready": True}, {"auth_plugin_state": "caller-plugin"}))
def test_caller_cannot_forge_canonical_readiness(override):
    with pytest.raises(TypeError):
        CanonicalAuthPluginReadiness(**override)


def test_runtime_evidence_is_noncanonical_and_grants_no_authority():
    evidence = RuntimeAuthPluginEvidence(RuntimeEvidenceState.OBSERVED_COMPATIBLE)
    projection = evidence.to_projection()
    assert projection["canonical"] is False
    assert projection["canonical_readiness_affected"] is False
    assert canonical_auth_plugin_readiness().ready is False
    assert all(projection[key] is False for key in ("authorization_authority", "capability_authority", "execution_authority", "mutation_authority", "retry_authority", "reconnect_authority", "rollback_authority"))
    with pytest.raises(TypeError):
        RuntimeAuthPluginEvidence("OBSERVED_COMPATIBLE")


def test_no_driver_or_network_import_and_no_plugin_name_field():
    tree = ast.parse(FILE.read_text())
    roots = imported_roots(tree)
    assert roots.isdisjoint({"pymysql", "mysqldb", "mysql", "mariadb", "sqlalchemy", "socket", "requests", "urllib", "httpx", "aiohttp", "subprocess", "docker"})
    assert {item.name for item in fields(CanonicalAuthPluginReadiness)}.isdisjoint({"plugin_name", "name", "value"})


def test_external_historical_descriptor_is_value_free_and_cannot_self_activate():
    evidence = canonical_historical_auth_plugin_evidence_contract()
    assert evidence.descriptor is ExternalEvidenceDescriptor.EXTERNAL_VALUE_FREE_REDACTED_HISTORICAL_AUTH_PLUGIN_ATTESTATION_DESCRIPTOR
    assert evidence.acceptable_evidence_classes == tuple(ExternalEvidenceClass)
    assert evidence.authoritative_evidence_available is evidence.ready is False
    assert evidence.production_authority is False
    assert all((evidence.independent_pre_existing_historical_evidence_required,
                evidence.account_binding_required, evidence.provenance_required,
                evidence.timestamp_required, evidence.immutable_integrity_identity_required,
                evidence.trusted_issuer_required, evidence.credential_material_forbidden))
    with pytest.raises(TypeError):
        HistoricalAuthPluginEvidenceContract(authoritative_evidence_available=True)

import ast
import json
from dataclasses import fields
from pathlib import Path

import pytest

from core.secrets.mariadb_continuity_prerequisites import (
    MariaDBContinuityPrerequisites,
    ProductionBoundary,
    canonical_production_boundary_facts,
    canonical_phase_a_prerequisites,
)


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = ROOT / "core/secrets/mariadb_continuity_prerequisites.py"
READINESS = [item.name for item in fields(MariaDBContinuityPrerequisites)]
FORBIDDEN_IMPORTS = {
    "subprocess", "socket", "requests", "urllib", "docker", "pymysql",
    "MySQLdb", "mysql", "mariadb", "sqlalchemy",
}


def test_phase_a_is_value_free_and_not_ready() -> None:
    facts = canonical_phase_a_prerequisites()
    assert facts.production_validation_ready is False
    assert facts.to_projection() == facts.to_projection()
    json.dumps(facts.to_projection())
    assert facts.to_projection() == {
        "schema_version": "1.0", "inspection": "READ_ONLY",
        "authorization_composition_defined": True,
        "credential_source_contract_defined": True,
        "credential_material_available": False,
        "canonical_network_target_defined": False,
        "canonical_network_target_deployed": False,
        "expected_identity_source_defined": True,
        "data_identity_baseline_available": False,
        "data_continuity_baseline_available": False,
        "driver_available": False,
        "production_validation_ready": False,
        "mutation_authority": False, "authorization_authority": False,
        "execution_authority": False, "retry_authority": False,
        "secret_values_read": False, "production_access_performed": False,
        "value_free": True,
    }


def test_package_1_authoritative_facts_are_absent_from_legacy_dto() -> None:
    assert {
        "authoritative_auth_plugin_evidence_available",
        "pymysql_compatibility_established",
        "expected_database_identity_available",
        "expected_account_identity_available",
        "required_grants_profile_available",
        "fixed_sql_text_available",
    }.isdisjoint(READINESS)


def test_readiness_requires_every_exact_true() -> None:
    complete = {name: True for name in READINESS}
    assert MariaDBContinuityPrerequisites(**complete).production_validation_ready
    for missing in READINESS:
        values = complete | {missing: False}
        assert not MariaDBContinuityPrerequisites(**values).production_validation_ready
    for bad in (1, 0, None, "true", [], object()):
        with pytest.raises(TypeError):
            MariaDBContinuityPrerequisites(**(complete | {READINESS[0]: bad}))


def test_projection_has_zero_authority_and_forbidden_fields_are_absent() -> None:
    projection = canonical_phase_a_prerequisites().to_projection()
    forbidden = {
        "credential", "password", "username", "host", "port", "database",
        "dsn", "url", "sql", "path", "environment", "argv", "command",
        "authorization_id", "capability", "capability_id", "mutation_budget",
        "execution_request", "execution_receipt", "baseline_value", "hash",
    }
    assert forbidden.isdisjoint(key.lower() for key in projection)
    assert all(projection[key] is False for key in (
        "mutation_authority", "authorization_authority", "execution_authority",
        "retry_authority", "secret_values_read", "production_access_performed",
    ))


def test_static_architecture_is_inert() -> None:
    source = PRODUCTION.read_text()
    tree = ast.parse(source)
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree) if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    assert imported.isdisjoint(FORBIDDEN_IMPORTS)
    assert not any(term in source.lower() for term in ("select ", "insert ", "update ", "delete "))


def test_production_boundaries_are_factual_and_zero_authority() -> None:
    facts = canonical_production_boundary_facts()
    assert not hasattr(facts, "production_validation_ready")
    assert not hasattr(facts, "ready")
    assert facts.boundaries == tuple(ProductionBoundary)
    assert facts.continuity_validation_mutation_budget == 0
    assert facts.maximum_connection_auth_attempts == 1
    assert facts.production_authorization_reuse_allowed is False
    projection = facts.to_projection()
    assert all(projection[name] is False for name in (
        "authorization_authority", "capability_authority", "execution_authority",
        "mutation_authority", "retry_authority", "reconnect_authority", "rollback_authority",
    ))
    assert "production_validation_ready" not in projection

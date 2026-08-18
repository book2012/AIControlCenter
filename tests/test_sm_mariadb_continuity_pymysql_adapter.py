import ast
import hashlib
import inspect
from pathlib import Path

import pytest

from core.secrets.mariadb_continuity_attempt import AttemptState, MariaDBContinuityAttempt
from core.secrets.mariadb_continuity_observations import MariaDBContinuityRuntimeObservation
from ops.macos.shopping.mariadb_continuity_pymysql_adapter import (
    AUTH_PLUGIN_STATE, DRIVER_FAMILY, DRIVER_MODE, DRIVER_VERSION,
    FixedValidationOperation, InjectedOneShotDriverSeam, PyMySQLDriverReadiness,
    canonical_driver_readiness,
)


ROOT = Path(__file__).parents[1]
PRODUCTION = ROOT / "ops/macos/shopping/mariadb_continuity_pymysql_adapter.py"
PRESERVED = (
    "core/secrets/mariadb_continuity_attempt.py",
    "core/secrets/mariadb_continuity_sources.py",
    "ops/macos/shopping/mariadb_continuity_target.py",
    "core/secrets/mariadb_continuity_prerequisites.py",
    "ops/macos/shopping/mariadb_continuity_validation_composition.py",
    "core/secrets/mariadb_continuity_validation.py",
    "core/secrets/mariadb_continuity_validation_port.py",
    "ops/macos/shopping/mariadb_continuity_validation_adapter.py",
)
SIX_ACTIONS = (
    "SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE", "SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE",
    "SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE",
    "SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE",
    "SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE",
    "SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE",
)


def test_exact_driver_metadata_is_fail_closed_and_unforgeable() -> None:
    readiness = canonical_driver_readiness()
    assert (DRIVER_FAMILY, DRIVER_VERSION, DRIVER_MODE) == ("PYMYSQL", "1.2.0", "SYNCHRONOUS_ONE_SHOT")
    assert AUTH_PLUGIN_STATE == "UNRESOLVED"
    assert readiness.maximum_future_connection_count_per_authorization == 1
    assert readiness.driver_imported is readiness.ready is False
    with pytest.raises(TypeError):
        PyMySQLDriverReadiness(ready=True)


def test_contract_has_one_closed_operation_and_no_forbidden_runtime_surface() -> None:
    assert tuple(FixedValidationOperation) == (FixedValidationOperation.CLOSED_MARIADB_CONTINUITY_VALIDATION,)
    tree = ast.parse(PRODUCTION.read_text())
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module.split(".")[0])
    assert not ({"pymysql", "socket", "requests", "urllib", "httpx", "aiohttp", "mysql", "mariadb", "sqlalchemy"} & imported_modules)
    forbidden_calls = {"connect", "socket", "cursor", "execute", "retry", "reconnect", "pool"}
    functions = {node.name.lower() for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert not (forbidden_calls & functions)
    source = PRODUCTION.read_text().lower()
    assert not any(marker in source for marker in ("select ", "show ", "grant ", "insert ", "update ", "delete "))


def test_import_ast_logic_detects_both_pymysql_forms() -> None:
    def top_level_imports(source: str) -> set[str]:
        modules: set[str] = set()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                modules.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module.split(".")[0])
        return modules

    assert "pymysql" in top_level_imports("import pymysql")
    assert "pymysql" in top_level_imports("from pymysql import connections")


def test_driver_seam_returns_runtime_observation_and_readiness_is_zero_authority() -> None:
    annotation = inspect.signature(InjectedOneShotDriverSeam.observe_once).return_annotation
    assert annotation is MariaDBContinuityRuntimeObservation
    projection = canonical_driver_readiness().to_projection()
    assert projection["value_free"] is True
    for name in (
        "authorization_authority", "capability_authority", "execution_authority",
        "mutation_authority", "retry_authority", "reconnect_authority",
        "rollback_authority",
    ):
        assert projection[name] is False


def test_exact_one_shot_lifecycle_semantics_remain() -> None:
    attempt = MariaDBContinuityAttempt.new()
    for state in (AttemptState.AUTHORIZED, AttemptState.CONSUMED, AttemptState.PRE_ATTEMPT):
        attempt = attempt.transition(state)
    assert attempt.transition(AttemptState.TERMINAL).attempted_count == 0
    initiated = attempt.transition(AttemptState.ATTEMPT_INITIATED)
    assert initiated.transition(AttemptState.TERMINAL).attempted_count == 1
    with pytest.raises(ValueError):
        initiated.transition(AttemptState.ATTEMPT_INITIATED)


def test_frozen_files_and_six_actions_match_head() -> None:
    import subprocess
    for relative in PRESERVED:
        disk = (ROOT / relative).read_bytes()
        head = subprocess.run(["git", "show", f"HEAD:{relative}"], cwd=ROOT, check=True, capture_output=True).stdout
        assert hashlib.sha256(disk).digest() == hashlib.sha256(head).digest()
    for relative in (
        "core/governance/control_plane/application/shopping_provisioning_coordinator.py",
        "ops/macos/shopping/secret_provisioning_adapters.py",
    ):
        source = (ROOT / relative).read_text()
        literals = {
            node.value
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value.startswith("SHOPPING_SECRET_")
            and ":" in node.value
        }
        assert literals == set(SIX_ACTIONS)
        assert 'SHOPPING_SECRET_PROVISIONING = "SHOPPING_SECRET_PROVISIONING"' in source
        assert "SHOPPING_SECRET_PROVISIONING" not in literals

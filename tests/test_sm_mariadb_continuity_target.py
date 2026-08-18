import ast
import hashlib
import re
from dataclasses import fields
from pathlib import Path

import pytest

from ops.macos.shopping.mariadb_continuity_target import (
    TargetProfile,
    TargetResolutionOwner,
    MariaDBContinuityTargetContract,
    canonical_phase_b1_target,
)


ROOT = Path(__file__).parents[1]
PRODUCTION_FILE = ROOT / "ops/macos/shopping/mariadb_continuity_target.py"
PRESERVED = {
    "core/governance/control_plane/application/shopping_provisioning_coordinator.py": "9f88a4981e1b7c1f35c38f52e70ee51ba33ba6bf010e4cab128f68cb466d38b1",
    "ops/macos/shopping/secret_provisioning_adapters.py": "c21e18e6ca2ca4edb56487abfd74a51e1c0a06e46fd556b2d9bcc3481f364455",
}
ACTIONS = {
    "SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE",
    "SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE",
    "SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE",
    "SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE",
    "SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE",
    "SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE",
}


def test_exact_symbolic_target_and_frozen_state():
    target = canonical_phase_b1_target()
    assert tuple(TargetProfile) == (TargetProfile.CLOSED_SYMBOLIC_PRODUCTION_MARIADB_PROFILE,)
    assert target.target_profile.value == "CLOSED_SYMBOLIC_PRODUCTION_MARIADB_PROFILE"
    assert target.target_resolution_owner is TargetResolutionOwner.MAC_CONTROL_PLANE
    assert target.canonical_target_contract_defined is True
    assert target.numeric_loopback_port_assigned is False
    assert target.target_deployed is False
    assert target.production_target_ready is False


@pytest.mark.parametrize(
    "override",
    (
        {"numeric_loopback_port_assigned": True},
        {"target_deployed": True},
        {"production_target_ready": True},
        {"target_profile": TargetProfile.CLOSED_SYMBOLIC_PRODUCTION_MARIADB_PROFILE},
    ),
)
def test_frozen_target_facts_reject_constructor_overrides(override):
    with pytest.raises(TypeError):
        MariaDBContinuityTargetContract(**override)


def test_target_truth_fields_are_not_init_fields_and_readiness_is_derived():
    metadata = {item.name: item.init for item in fields(MariaDBContinuityTargetContract)}
    assert metadata == {
        "target_profile": False,
        "target_resolution_owner": False,
        "canonical_target_contract_defined": False,
        "numeric_loopback_port_assigned": False,
        "target_deployed": False,
    }
    assert "production_target_ready" not in metadata
    target = MariaDBContinuityTargetContract()
    assert target.numeric_loopback_port_assigned is False
    assert target.target_deployed is False
    assert target.production_target_ready is False


def test_caller_surface_has_no_endpoint_fields_or_numeric_port():
    names = {item.name.lower() for item in fields(type(canonical_phase_b1_target()))}
    assert names.isdisjoint({"host", "port", "dsn", "url", "database", "username"})
    source = PRODUCTION_FILE.read_text()
    assert re.search(r"\b(?:3306|[1-9][0-9]{3,4})\b", source) is None


def test_no_filesystem_network_driver_sql_config_or_environment_implementation():
    source = PRODUCTION_FILE.read_text()
    tree = ast.parse(source)
    imports = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
    assert imports.isdisjoint({"subprocess", "socket", "requests", "urllib", "docker", "pymysql", "MySQLdb", "mysql", "mariadb", "sqlalchemy", "pathlib", "os"})
    assert not any(term in source for term in ("getenv", "environ", "Compose", "Colima", "GovernanceAuthorization", "ControlledExecutionPort"))
    assert not any(keyword in source.upper() for keyword in ("SELECT ", "INSERT ", "UPDATE ", "DELETE ", "CREATE ", "ALTER ", "DROP "))


def test_phase_a_files_and_exact_six_actions_are_preserved():
    for relative, expected in PRESERVED.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected
    source = (ROOT / "ops/macos/shopping/secret_provisioning_adapters.py").read_text()
    discovered = set(re.findall(r'"(SHOPPING_SECRET_(?:TOOL|IDENTITY|RECIPIENT):[^"\n]+)"', source))
    assert discovered == ACTIONS
    assert 'SHOPPING_SECRET_PROVISIONING = "SHOPPING_SECRET_PROVISIONING"' in source
    assert "SHOPPING_SECRET_PROVISIONING" not in discovered

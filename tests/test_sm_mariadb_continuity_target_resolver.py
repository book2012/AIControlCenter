import inspect
from pathlib import Path

import pytest

from ops.macos.shopping.mariadb_continuity_target_resolver import (
    MariaDBContinuityTargetResolution,
    ResolutionOwner,
    SymbolicTarget,
    resolve_canonical_target,
)


PRODUCTION = Path(__file__).parents[1] / "ops/macos/shopping/mariadb_continuity_target_resolver.py"


def test_only_symbolic_mac_owned_target_is_resolved() -> None:
    target = resolve_canonical_target()
    assert tuple(SymbolicTarget) == (SymbolicTarget.CLOSED_SYMBOLIC_PRODUCTION_MARIADB_PROFILE,)
    assert target.owner is ResolutionOwner.MAC_CONTROL_PLANE
    assert target.numeric_loopback_port_assigned is False
    assert target.target_deployed is False
    assert target.production_target_ready is False


def test_readiness_and_target_facts_cannot_be_caller_supplied() -> None:
    parameters = inspect.signature(MariaDBContinuityTargetResolution).parameters
    assert not ({"host", "port", "dsn", "url", "database", "username", "production_target_ready"} & set(parameters))
    with pytest.raises(TypeError):
        MariaDBContinuityTargetResolution(production_target_ready=True)


def test_target_projection_is_value_free_and_zero_authority() -> None:
    projection = resolve_canonical_target().to_projection()
    assert projection["value_free"] is True
    assert all(
        projection[name] is False
        for name in (
            "authorization_authority", "capability_authority", "execution_authority",
            "mutation_authority", "retry_authority", "reconnect_authority",
            "rollback_authority",
        )
    )


def test_no_numeric_port_or_runtime_discovery_surface() -> None:
    source = PRODUCTION.read_text()
    assert not any(character.isdigit() for character in source)
    for forbidden in ("environ", "compose", "docker", "colima", "socket", "connect("):
        assert forbidden not in source.lower()

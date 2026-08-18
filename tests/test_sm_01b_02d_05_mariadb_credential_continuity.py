import ast
import json
import subprocess
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path

import pytest

from core.secrets.mariadb_continuity import (
    ContinuityDecision,
    ContinuityObservation,
    ContinuityState,
    ContinuityStrategy,
    NextBoundaryType,
    decide_continuity,
)


MODULE = Path(__file__).parents[1] / "core/secrets/mariadb_continuity.py"
REPOSITORY = MODULE.parents[2]
PROVISIONING_SOURCES = (
    REPOSITORY
    / "core/governance/control_plane/application/shopping_provisioning_coordinator.py",
    REPOSITORY / "ops/macos/shopping/secret_provisioning_adapters.py",
)
SHOPPING_PROVISIONING_ACTIONS = {
    "SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE",
    "SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE",
    "SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE",
    "SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE",
    "SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE",
    "SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE",
}


def projection(**facts: object) -> dict[str, object]:
    return decide_continuity(ContinuityObservation(**facts)).to_projection()


def test_closed_state_and_strategy_enums() -> None:
    assert issubclass(ContinuityState, Enum)
    assert {item.value for item in ContinuityState} == {
        "UNRESOLVED", "STRATEGY_DECLARED", "VALIDATION_REQUIRED", "RESOLVED"
    }
    assert issubclass(ContinuityStrategy, Enum)
    assert {item.value for item in ContinuityStrategy} == {"RECOVER", "ROTATE", "REPLACE"}


def test_records_are_immutable_slotted_dataclasses() -> None:
    assert is_dataclass(ContinuityObservation) and is_dataclass(ContinuityDecision)
    assert "__slots__" in ContinuityObservation.__dict__
    record = ContinuityObservation()
    with pytest.raises((AttributeError, TypeError)):
        record.validation_confirmed = True  # type: ignore[misc]


def test_unresolved_projection_is_value_free_and_read_only() -> None:
    result = projection()
    assert result == {
        "schema_version": "1.0",
        "inspection": "READ_ONLY",
        "owner": "MAC_MINI_M4_AICONTROLCENTER_CONTROL_PLANE",
        "value_free": True,
        "secret_values_read": False,
        "mutation_authority": False,
        "continuity": {
            "state": "UNRESOLVED",
            "strategy": None,
            "recovery_source_declared": False,
            "production_validation_required": False,
            "resolved": False,
            "reason_codes": ["MARIADB_HISTORICAL_CREDENTIAL_CONTINUITY_UNRESOLVED"],
        },
        "next_boundary": {"boundary_type": "HUMAN_DECISION_REQUIRED", "capability_id": None},
    }


@pytest.mark.parametrize("strategy", [ContinuityStrategy.RECOVER, ContinuityStrategy.ROTATE, ContinuityStrategy.REPLACE])
def test_strategy_declaration_grants_no_authority(strategy: ContinuityStrategy) -> None:
    result = projection(strategy=strategy)
    assert result["continuity"]["state"] == "STRATEGY_DECLARED"  # type: ignore[index]
    assert result["continuity"]["strategy"] == strategy.value  # type: ignore[index]
    assert result["mutation_authority"] is False
    assert result["next_boundary"]["capability_id"] is None  # type: ignore[index]


def test_recover_source_requires_validation() -> None:
    result = projection(strategy=ContinuityStrategy.RECOVER, recovery_source_declared=True)
    assert result["continuity"]["state"] == "VALIDATION_REQUIRED"  # type: ignore[index]
    assert result["continuity"]["production_validation_required"] is True  # type: ignore[index]
    assert result["next_boundary"]["boundary_type"] == "RECOVERY_VALIDATION_REQUIRED"  # type: ignore[index]


def test_recover_resolves_only_with_source_and_factual_validation() -> None:
    result = projection(
        strategy=ContinuityStrategy.RECOVER,
        recovery_source_declared=True,
        validation_confirmed=True,
    )
    assert result["continuity"]["state"] == "RESOLVED"  # type: ignore[index]
    assert result["continuity"]["resolved"] is True  # type: ignore[index]
    with pytest.raises(ValueError):
        projection(strategy=ContinuityStrategy.RECOVER, validation_confirmed=True)


@pytest.mark.parametrize("strategy", [ContinuityStrategy.ROTATE, ContinuityStrategy.REPLACE])
def test_non_recovery_factual_validation_may_resolve_without_authority(
    strategy: ContinuityStrategy,
) -> None:
    result = projection(strategy=strategy, validation_confirmed=True)
    assert result["continuity"]["state"] == "RESOLVED"  # type: ignore[index]
    assert result["next_boundary"] == {
        "boundary_type": "CONTINUITY_RESOLVED", "capability_id": None
    }
    assert result["mutation_authority"] is False


@pytest.mark.parametrize(
    "facts",
    [
        {"validation_confirmed": True},
        {"recovery_source_declared": True},
        {"strategy": ContinuityStrategy.ROTATE, "recovery_source_declared": True},
        {"strategy": ContinuityStrategy.REPLACE, "recovery_source_declared": True},
    ],
)
def test_contradictory_facts_fail_closed(facts: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        ContinuityObservation(**facts)


def test_projection_is_deterministic_and_json_safe() -> None:
    observation = ContinuityObservation(strategy=ContinuityStrategy.ROTATE)
    first = decide_continuity(observation).to_projection()
    second = decide_continuity(observation).to_projection()
    assert first == second
    assert json.loads(json.dumps(first, sort_keys=True)) == first


def test_projection_contains_only_json_primitives_and_no_runtime_objects() -> None:
    forbidden_types = (Path, ContinuityDecision, ContinuityObservation, NextBoundaryType)

    def inspect(value: object) -> None:
        assert not isinstance(value, forbidden_types)
        assert not callable(value)
        if isinstance(value, dict):
            for key, item in value.items():
                assert isinstance(key, str)
                inspect(item)
        elif isinstance(value, list):
            for item in value:
                inspect(item)
        else:
            assert value is None or type(value) in (str, bool, int, float)

    inspect(projection(strategy=ContinuityStrategy.REPLACE, validation_confirmed=True))


def test_no_value_bearing_input_field_or_hostile_sentinel_surface() -> None:
    assert {field.name for field in fields(ContinuityObservation)} == {
        "strategy", "recovery_source_declared", "validation_confirmed"
    }
    with pytest.raises(TypeError):
        ContinuityObservation(password="HOSTILE_SENTINEL")  # type: ignore[call-arg]


def test_module_ast_has_no_forbidden_dependencies_or_mutation_api() -> None:
    source = MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint({
        "os", "subprocess", "pathlib", "sqlite3", "socket", "requests", "urllib",
        "docker", "hashlib", "secrets",
    })
    names = {node.name.lower() for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    assert not any(token in name for name in names for token in (
        "retry", "rollback", "compensation", "mutate", "recover_secret", "rotate_secret", "replace_secret"
    ))


def test_module_is_isolated_from_shopping_governance_and_actions() -> None:
    source = MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    imported_modules.update(
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )
    assert not any(
        module.endswith(
            ("shopping_provisioning_coordinator", "secret_provisioning_adapters")
        )
        for module in imported_modules
    )
    assert "ShoppingProvisioningGovernanceCoordinator" not in source
    for action in SHOPPING_PROVISIONING_ACTIONS:
        assert action not in source


@pytest.mark.parametrize("provisioning_source", PROVISIONING_SOURCES)
def test_actual_six_shopping_provisioning_actions_remain_isolated(
    provisioning_source: Path,
) -> None:
    tree = ast.parse(provisioning_source.read_text(encoding="utf-8"))
    declared_actions = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value.startswith("SHOPPING_SECRET_")
        and ":" in node.value
    }
    assert declared_actions == SHOPPING_PROVISIONING_ACTIONS


def test_existing_shopping_provisioning_sources_are_unchanged() -> None:
    result = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "HEAD",
            "--",
            "core/governance/control_plane/application/shopping_provisioning_coordinator.py",
            "ops/macos/shopping/secret_provisioning_adapters.py",
        ],
        cwd=REPOSITORY,
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout == ""


def _decision(**overrides: object) -> ContinuityDecision:
    values: dict[str, object] = {
        "state": ContinuityState.UNRESOLVED,
        "strategy": None,
        "recovery_source_declared": False,
        "validation_confirmed": False,
        "reason_code": "MARIADB_HISTORICAL_CREDENTIAL_CONTINUITY_UNRESOLVED",
        "next_boundary_type": NextBoundaryType.HUMAN_DECISION_REQUIRED,
    }
    values.update(overrides)
    return ContinuityDecision(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "overrides,exception",
    [
        (
            {
                "state": ContinuityState.RESOLVED,
                "strategy": ContinuityStrategy.ROTATE,
                "reason_code": "MARIADB_CONTINUITY_RESOLVED",
                "next_boundary_type": NextBoundaryType.CONTINUITY_RESOLVED,
            },
            ValueError,
        ),
        (
            {
                "state": ContinuityState.RESOLVED,
                "strategy": ContinuityStrategy.RECOVER,
                "validation_confirmed": True,
                "reason_code": "MARIADB_CONTINUITY_RESOLVED",
                "next_boundary_type": NextBoundaryType.CONTINUITY_RESOLVED,
            },
            ValueError,
        ),
        ({"strategy": ContinuityStrategy.RECOVER}, ValueError),
        (
            {
                "state": ContinuityState.VALIDATION_REQUIRED,
                "strategy": ContinuityStrategy.ROTATE,
                "recovery_source_declared": True,
                "reason_code": "MARIADB_RECOVERY_VALIDATION_REQUIRED",
                "next_boundary_type": NextBoundaryType.RECOVERY_VALIDATION_REQUIRED,
            },
            ValueError,
        ),
        (
            {
                "state": ContinuityState.STRATEGY_DECLARED,
                "strategy": ContinuityStrategy.ROTATE,
                "validation_confirmed": True,
                "reason_code": "MARIADB_CONTINUITY_STRATEGY_DECLARED",
                "next_boundary_type": NextBoundaryType.FUTURE_GOVERNED_MUTATION_REQUIRED,
            },
            ValueError,
        ),
        ({"reason_code": "WRONG_REASON"}, ValueError),
        ({"next_boundary_type": NextBoundaryType.CONTINUITY_RESOLVED}, ValueError),
        ({"recovery_source_declared": 0}, TypeError),
        ({"validation_confirmed": 0}, TypeError),
    ],
)
def test_direct_decision_construction_rejects_contradictions(
    overrides: dict[str, object], exception: type[Exception]
) -> None:
    with pytest.raises(exception):
        _decision(**overrides)


@pytest.mark.parametrize(
    "observation",
    [
        ContinuityObservation(),
        ContinuityObservation(strategy=ContinuityStrategy.RECOVER),
        ContinuityObservation(strategy=ContinuityStrategy.ROTATE),
        ContinuityObservation(strategy=ContinuityStrategy.REPLACE),
        ContinuityObservation(
            strategy=ContinuityStrategy.RECOVER, recovery_source_declared=True
        ),
        ContinuityObservation(
            strategy=ContinuityStrategy.RECOVER,
            recovery_source_declared=True,
            validation_confirmed=True,
        ),
        ContinuityObservation(strategy=ContinuityStrategy.ROTATE, validation_confirmed=True),
        ContinuityObservation(strategy=ContinuityStrategy.REPLACE, validation_confirmed=True),
    ],
)
def test_all_valid_decisions_remain_constructible_and_deterministic(
    observation: ContinuityObservation,
) -> None:
    decision = decide_continuity(observation)
    reconstructed = ContinuityDecision(
        state=decision.state,
        strategy=decision.strategy,
        recovery_source_declared=decision.recovery_source_declared,
        validation_confirmed=decision.validation_confirmed,
        reason_code=decision.reason_code,
        next_boundary_type=decision.next_boundary_type,
    )
    assert reconstructed == decision
    assert reconstructed.to_projection() == decide_continuity(observation).to_projection()

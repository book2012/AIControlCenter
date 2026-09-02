from __future__ import annotations

import ast
import inspect
import json
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest

from core.shopping.observability.service_start import (
    COMPONENT_KINDS,
    ComponentKind,
    ObservationCategory,
    ObservationCompleteness,
    ObservationError,
    ServiceStartEvidence,
    ServiceStartState,
    ShoppingComponent,
    aggregate_service_start_state,
    build_service_start_projection,
)
from core.shopping.ports.service_start import ShoppingServiceStartObservationPort
from ops.macos.shopping.repository_service_start import (
    RepositoryFactError,
    ShoppingRepositoryPaths,
    load_shopping_repository_facts,
)


ROOT = Path(__file__).resolve().parents[1]


def evidence_for(
    component: ShoppingComponent = ShoppingComponent.MARIADB,
    *,
    present: bool = True,
    running: bool = True,
    healthy: bool = True,
    conflict: bool = False,
) -> tuple[ServiceStartEvidence, ...]:
    return (
        ServiceStartEvidence(
            component, ObservationCategory.INVENTORY,
            ObservationCompleteness.COMPLETE, present=present,
        ),
        ServiceStartEvidence(
            component, ObservationCategory.LIFECYCLE,
            ObservationCompleteness.COMPLETE, running=running,
        ),
        ServiceStartEvidence(
            component, ObservationCategory.HEALTH,
            ObservationCompleteness.COMPLETE, healthy=healthy,
        ),
        ServiceStartEvidence(
            component, ObservationCategory.BINDING,
            ObservationCompleteness.COMPLETE, conflict=conflict,
        ),
    )


def test_repository_desired_state_facts_are_derived_from_canonical_files() -> None:
    facts = load_shopping_repository_facts(ShoppingRepositoryPaths.canonical(ROOT))
    assert facts == {
        "runtime_owner": "mac",
        "ubuntu_dependency": False,
        "mariadb_host_published_port": False,
        "wordpress_bind_host": "127.0.0.1",
        "wordpress_port": 58082,
        "woocommerce_host_service_id": "shopping-runtime",
        "woocommerce_kind": "wordpress-plugin-commerce-engine",
        "deployment_status": "NOT_DEPLOYED",
    }


@pytest.mark.parametrize(
    ("rows", "expected"),
    [
        (evidence_for(), ServiceStartState.RUNNING),
        (evidence_for(running=False), ServiceStartState.STOPPED),
        (evidence_for(healthy=False), ServiceStartState.UNHEALTHY),
        (evidence_for(conflict=True), ServiceStartState.CONFLICTING),
        ((ServiceStartEvidence(
            ShoppingComponent.MARIADB,
            ObservationCategory.INVENTORY,
            ObservationCompleteness.COMPLETE,
            present=False,
        ),), ServiceStartState.ABSENT),
        ((), ServiceStartState.UNKNOWN),
    ],
)
def test_all_six_states(rows, expected) -> None:
    assert aggregate_service_start_state(ShoppingComponent.MARIADB, rows) is expected


@pytest.mark.parametrize(
    ("completeness", "error"),
    [
        (ObservationCompleteness.INCOMPLETE, ObservationError.NONE),
        (ObservationCompleteness.MALFORMED, ObservationError.MALFORMED_EVIDENCE),
        (ObservationCompleteness.UNAVAILABLE, ObservationError.SOURCE_UNAVAILABLE),
        (ObservationCompleteness.UNSUPPORTED, ObservationError.UNSUPPORTED_EVIDENCE),
    ],
)
def test_incomplete_malformed_or_unavailable_evidence_is_unknown(
    completeness, error,
) -> None:
    rows = list(evidence_for())
    rows[2] = ServiceStartEvidence(
        ShoppingComponent.MARIADB, ObservationCategory.HEALTH,
        completeness, error=error,
    )
    assert aggregate_service_start_state(
        ShoppingComponent.MARIADB, rows,
    ) is ServiceStartState.UNKNOWN


def test_duplicate_identity_evidence_is_conflicting() -> None:
    rows = evidence_for() + (evidence_for()[0],)
    assert aggregate_service_start_state(
        ShoppingComponent.MARIADB, rows,
    ) is ServiceStartState.CONFLICTING


def test_present_and_complete_stopped_lifecycle_needs_no_health_inference() -> None:
    rows = evidence_for()[:2]
    rows = (rows[0], ServiceStartEvidence(
        ShoppingComponent.MARIADB,
        ObservationCategory.LIFECYCLE,
        ObservationCompleteness.COMPLETE,
        running=False,
    ))
    assert aggregate_service_start_state(
        ShoppingComponent.MARIADB, rows,
    ) is ServiceStartState.STOPPED


def test_woocommerce_is_hosted_and_no_component_is_ubuntu_owned() -> None:
    assert COMPONENT_KINDS[ShoppingComponent.WOOCOMMERCE] is ComponentKind.HOSTED_CAPABILITY
    assert set(ShoppingComponent) == {
        ShoppingComponent.MARIADB,
        ShoppingComponent.WORDPRESS,
        ShoppingComponent.WOOCOMMERCE,
        ShoppingComponent.AICONTROLCENTER_SHOPPING,
        ShoppingComponent.DASHBOARD,
        ShoppingComponent.HOMEPAGE,
    }
    assert all("ubuntu" not in item.value for item in ShoppingComponent)


def test_evidence_is_immutable_value_free_and_port_has_only_observe() -> None:
    row = evidence_for()[0]
    with pytest.raises(FrozenInstanceError):
        row.present = False
    names = {field.name for field in fields(ServiceStartEvidence)}
    forbidden = {
        "password", "secret", "credential", "sql", "command", "argv",
        "authorization", "token", "value",
    }
    assert not names & forbidden
    methods = {
        name for name, member in vars(ShoppingServiceStartObservationPort).items()
        if inspect.isfunction(member) and not name.startswith("_")
    }
    assert methods == {"observe"}
    assert inspect.iscoroutinefunction(ShoppingServiceStartObservationPort.observe)


def test_projection_is_deterministic_read_only_and_authority_free() -> None:
    rows = tuple(
        row
        for component in ShoppingComponent
        for row in evidence_for(component)
    )
    facts = load_shopping_repository_facts(ShoppingRepositoryPaths.canonical(ROOT))
    first = build_service_start_projection(rows, facts)
    second = build_service_start_projection(rows, dict(reversed(tuple(facts.items()))))
    assert json.dumps(
        first, sort_keys=True, separators=(",", ":"),
    ) == json.dumps(
        second, sort_keys=True, separators=(",", ":"),
    )
    assert first["overall_status"] == "RUNNING"
    assert first["observation_complete"] is True
    assert first["mode"] == "READ_ONLY"
    assert first["environment"] == "CONTROLLED_NON_PRODUCTION"
    assert first["mutation_performed"] is False
    assert first["automatic_retry"] is False
    assert first["production_access"] is False
    assert first["authorization_consumed"] is False
    assert first["ubuntu_dependency"] is False


def test_projection_with_missing_component_evidence_fails_closed() -> None:
    projection = build_service_start_projection(evidence_for(), {})
    assert projection["overall_status"] == "UNKNOWN"
    assert projection["observation_complete"] is False


def test_repository_loader_fails_closed_for_malformed_fixture(tmp_path: Path) -> None:
    paths = ShoppingRepositoryPaths.canonical(ROOT)
    malformed = tmp_path / "services.json"
    malformed.write_text("not-json", encoding="utf-8")
    with pytest.raises(RepositoryFactError):
        load_shopping_repository_facts(
            ShoppingRepositoryPaths(
                paths.compose, malformed, paths.capabilities,
                paths.environment_example,
            )
        )


def test_contract_and_loader_have_no_live_access_surface(monkeypatch) -> None:
    def blocked(*_args, **_kwargs):
        raise AssertionError("live access attempted")

    import socket
    import subprocess
    import urllib.request

    monkeypatch.setattr(subprocess, "run", blocked)
    monkeypatch.setattr(subprocess, "Popen", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(urllib.request, "urlopen", blocked)
    facts = load_shopping_repository_facts(ShoppingRepositoryPaths.canonical(ROOT))
    assert facts["deployment_status"] == "NOT_DEPLOYED"

    source_paths = [
        ROOT / "core/shopping/observability/service_start.py",
        ROOT / "core/shopping/ports/service_start.py",
        ROOT / "ops/macos/shopping/repository_service_start.py",
    ]
    forbidden_calls = {
        "start", "stop", "restart", "create", "delete", "remove", "pull",
        "build", "up", "down", "write", "mutate", "retry", "rollback",
        "authorize",
    }
    for path in source_paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        functions = {
            node.name.lower()
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        assert not functions & forbidden_calls

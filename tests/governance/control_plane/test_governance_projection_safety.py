import ast
from dataclasses import fields
from datetime import datetime, timezone
from pathlib import Path

import pytest

from core.governance.control_plane.application.api_projection import (
    GovernanceApiReference,
    GovernanceReadModel,
)
from core.governance.control_plane.domain import AuthorizationState, MutationBudgetStatus


SOURCE_FILES = (
    Path("core/governance/control_plane/application/evidence_policy.py"),
    Path("core/governance/control_plane/application/api_projection.py"),
)


def minimal_model(**changes: object) -> GovernanceReadModel:
    values = {
        "lifecycle_id": "lifecycle-a9",
        "authorization_state": AuthorizationState.AUTHORIZED,
        "precondition_status": None,
        "mutation_budget_status": MutationBudgetStatus.AVAILABLE,
        "allowed_invocation_count": 1,
        "actual_invocation_count": 0,
        "completed_count": 0,
        "uncertain_count": 0,
        "execution_status": None,
        "postcondition_decision": None,
        "failure_present": False,
        "manual_action_required": False,
        "data_reference": GovernanceApiReference(
            "GovernanceApiEnvelope", "projection-a9", "sha256:projection"
        ),
        "evidence_manifest_reference": None,
        "evidence_bundle_reference": None,
        "git_documentation_gate_status": None,
        "git_documentation_gate_reference": None,
        "projected_at": datetime(2026, 8, 10, tzinfo=timezone.utc),
    }
    values.update(changes)
    return GovernanceReadModel(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "changes",
    (
        {"allowed_invocation_count": -1},
        {"actual_invocation_count": -1},
        {"completed_count": -1},
        {"uncertain_count": -1},
        {"actual_invocation_count": 2},
        {"completed_count": 1},
        {"uncertain_count": 1},
        {"actual_invocation_count": 1, "completed_count": 1, "uncertain_count": 1},
    ),
)
def test_invalid_counts_fail_closed(changes: dict[str, int]) -> None:
    with pytest.raises(ValueError):
        minimal_model(**changes)


def test_empty_lifecycle_binding_fails_closed() -> None:
    with pytest.raises(ValueError):
        minimal_model(lifecycle_id="")


def test_typed_models_expose_no_generic_or_secret_transport_fields() -> None:
    names = {field.name.lower() for field in fields(GovernanceReadModel)}
    forbidden = {
        "payload", "environment", "headers", "cookies", "credentials", "secrets",
        "password", "authorization", "access_token", "api_key", "private_key",
        "provider_response", "command",
    }
    assert names.isdisjoint(forbidden)


def test_a9_sources_have_only_pure_inward_imports() -> None:
    forbidden_roots = {
        "os", "pathlib", "subprocess", "sqlite3", "socket", "requests", "httpx",
        "fastapi", "flask", "django", "urllib", "boto3",
    }
    for path in SOURCE_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imports.update(
            (node.module or "").split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.level == 0
        )
        assert imports.isdisjoint(forbidden_roots)
        source = path.read_text(encoding="utf-8")
        assert "control_plane.ports" not in source
        assert "control_plane.adapters" not in source


def test_projection_defines_no_mutation_or_authority_surface() -> None:
    tree = ast.parse(SOURCE_FILES[1].read_text(encoding="utf-8"))
    function_names = {
        node.name.lower() for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("__")
    }
    forbidden_fragments = {
        "authorize", "approve", "consume", "execute", "persist", "retry", "rollback",
        "create_post", "create_put", "create_patch", "create_delete",
    }
    assert all(
        fragment not in name
        for name in function_names
        for fragment in forbidden_fragments
    )


def test_projection_has_no_clock_environment_http_or_external_authority_calls() -> None:
    source = SOURCE_FILES[1].read_text(encoding="utf-8")
    forbidden_calls = (
        ".now(", ".utcnow(", "getenv(", "environ", "FastAPI(", "APIRouter(",
        "Shopping", "Ubuntu", "EvidencePersistencePort", "ControlledExecutionPort",
    )
    assert all(value not in source for value in forbidden_calls)

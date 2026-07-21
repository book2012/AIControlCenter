import ast
import json
from datetime import datetime, timezone
from pathlib import Path

import core.api.services.governance_audit_operations as operations_service

API_PATH = Path(
    "core/api/routes/governance_audit.py"
)
DASHBOARD_PATH = Path(
    "core/api/routes/dashboard.py"
)
SERVICE_PATH = Path(
    "core/api/services/"
    "governance_audit_operations.py"
)
SERVICE_MODULE = (
    "core.api.services."
    "governance_audit_operations"
)


def parsed(path: Path) -> ast.Module:
    return ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
    )


def imported_names(
    path: Path,
    module: str,
) -> set[str]:
    names: set[str] = set()

    for node in parsed(path).body:
        if not isinstance(node, ast.ImportFrom):
            continue

        if node.module != module:
            continue

        names.update(
            alias.name
            for alias in node.names
        )

    return names


def imported_modules(path: Path) -> set[str]:
    modules = set()

    for node in ast.walk(parsed(path)):
        if isinstance(node, ast.Import):
            modules.update(
                alias.name
                for alias in node.names
            )
        elif (
            isinstance(node, ast.ImportFrom)
            and node.module
        ):
            modules.add(node.module)

    return modules


def test_dashboard_injects_operations_panel():
    assignments = [
        node
        for node in ast.walk(
            parsed(DASHBOARD_PATH)
        )
        if isinstance(node, ast.Assign)
    ]

    assert any(
        isinstance(node.targets[0], ast.Subscript)
        and isinstance(
            node.targets[0].value,
            ast.Name,
        )
        and node.targets[0].value.id == "payload"
        and isinstance(
            node.targets[0].slice,
            ast.Constant,
        )
        and (
            node.targets[0].slice.value
            == "governance_audit_operations"
        )
        for node in assignments
    )


def test_api_and_dashboard_use_separate_error_policies():
    api_names = imported_names(
        API_PATH,
        SERVICE_MODULE,
    )
    dashboard_names = imported_names(
        DASHBOARD_PATH,
        SERVICE_MODULE,
    )

    assert (
        "build_governance_audit_operations_payload"
        in api_names
    )
    assert (
        "build_governance_audit_operations_dashboard_payload"
        in dashboard_names
    )
    assert (
        "build_governance_audit_operations_dashboard_payload"
        not in api_names
    )


def test_dashboard_has_no_sqlite_dependency():
    modules = imported_modules(DASHBOARD_PATH)

    assert "sqlite3" not in modules
    assert not any(
        "adapters.sqlite" in module
        for module in modules
    )


def test_dashboard_panel_has_no_execution_action():
    source = DASHBOARD_PATH.read_text(
        encoding="utf-8"
    ).lower()

    forbidden = {
        "automatic_retry",
        "copy_model",
        "create_model",
        "delete_model",
        "pull_model",
        "remediate(",
        "restore(",
    }

    assert not any(
        token in source
        for token in forbidden
    )


def test_dashboard_wrapper_fails_soft_without_disclosure(
    monkeypatch,
):
    def fail_strict_builder(*args, **kwargs):
        raise RuntimeError(
            "sensitive-database-error"
        )

    monkeypatch.setattr(
        operations_service,
        "build_governance_audit_operations_payload",
        fail_strict_builder,
    )

    payload = (
        operations_service
        .build_governance_audit_operations_dashboard_payload(
            generated_at=datetime(
                2026,
                7,
                21,
                10,
                tzinfo=timezone.utc,
            )
        )
    )

    assert payload["overall_health"] == "unknown"
    assert payload["read_only"] is True
    assert payload["write_actions"] == []
    assert (
        payload["production_database_migrated"]
        is False
    )
    assert {
        item["unavailable_reason"]
        for item in payload["operations"]
    } == {"presentation-error"}
    assert (
        "sensitive-database-error"
        not in json.dumps(payload)
    )

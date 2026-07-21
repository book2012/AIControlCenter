import ast
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from core.api.services.governance_audit_operations import (
    build_governance_audit_operations_payload,
)

SERVICE_PATH = Path(
    "core/api/services/"
    "governance_audit_operations.py"
)
API_PATH = Path(
    "core/api/routes/governance_audit.py"
)
DASHBOARD_PATH = Path(
    "core/api/routes/dashboard.py"
)


def utc() -> datetime:
    return datetime(
        2026,
        7,
        21,
        10,
        tzinfo=timezone.utc,
    )


def test_presentation_service_never_initializes_schema():
    source = SERVICE_PATH.read_text(
        encoding="utf-8"
    )

    assert "initialize_schema" not in source
    assert "executescript" not in source


def test_missing_operations_table_is_not_created(
    tmp_path,
):
    database = tmp_path / "existing.sqlite3"
    connection = sqlite3.connect(database)
    connection.execute(
        "CREATE TABLE existing_table "
        "(id INTEGER PRIMARY KEY)"
    )
    connection.commit()
    connection.close()

    before = (
        database.stat().st_mtime_ns,
        database.stat().st_size,
    )

    payload = build_governance_audit_operations_payload(
        database,
        generated_at=utc(),
    )

    after = (
        database.stat().st_mtime_ns,
        database.stat().st_size,
    )

    connection = sqlite3.connect(database)

    try:
        table = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = ?
            """,
            (
                "governance_audit_operation_events",
            ),
        ).fetchone()
    finally:
        connection.close()

    assert before == after
    assert table is None
    assert (
        payload["production_database_migrated"]
        is False
    )


def test_service_uses_read_only_schema_probe():
    source = SERVICE_PATH.read_text(
        encoding="utf-8"
    )

    assert "?mode=ro" in source
    assert "PRAGMA query_only = ON" in source
    assert "INSERT INTO" not in source
    assert "UPDATE " not in source
    assert "DELETE FROM" not in source
    assert "CREATE TABLE" not in source


def test_service_has_no_scheduler_or_executor_dependency():
    tree = ast.parse(
        SERVICE_PATH.read_text(
            encoding="utf-8"
        ),
        filename=str(SERVICE_PATH),
    )

    imports = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(
                alias.name
                for alias in node.names
            )
        elif (
            isinstance(node, ast.ImportFrom)
            and node.module
        ):
            imports.add(node.module)

    assert not any(
        "scheduler" in module
        or "executor" in module
        or "ports" in module
        for module in imports
    )


def test_operations_routes_define_no_write_methods():
    for path in (
        API_PATH,
        DASHBOARD_PATH,
    ):
        tree = ast.parse(
            path.read_text(encoding="utf-8"),
            filename=str(path),
        )

        for node in ast.walk(tree):
            if not isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            ):
                continue

            for decorator in node.decorator_list:
                if not isinstance(
                    decorator,
                    ast.Call,
                ):
                    continue

                if not isinstance(
                    decorator.func,
                    ast.Attribute,
                ):
                    continue

                assert (
                    decorator.func.attr.lower()
                    not in {
                        "post",
                        "put",
                        "patch",
                        "delete",
                    }
                )

from __future__ import annotations

import ast
import asyncio
from pathlib import Path

import pytest

from core.shopping.application.snapshot_queries import (
    CAPABILITY_BY_METHOD,
    CONTRACT_BY_METHOD,
    REQUIRED_ARGUMENTS_BY_METHOD,
    SnapshotQueryContractError,
    SnapshotQueryDenied,
    execute_snapshot_query,
    snapshot_query_contract_manifest,
)
from core.shopping.contracts.snapshot_normalization import (
    CANONICAL_SNAPSHOT_CONTRACTS,
    normalize_snapshot,
    snapshot_normalization_contract_manifest,
)


METHOD = sorted(
    CONTRACT_BY_METHOD
)[0]

CONTRACT = sorted(
    CANONICAL_SNAPSHOT_CONTRACTS
)[0]


class FakeRepository:
    def __init__(
        self,
        *,
        payload=None,
        error=None,
    ):
        self.payload = (
            {
                "snapshot_id": "snapshot-1",
                "nested": {
                    "value": 1,
                },
            }
            if payload is None
            else payload
        )
        self.error = error
        self.calls = []

    def __getattr__(
        self,
        name,
    ):
        if name not in CONTRACT_BY_METHOD:
            raise AttributeError(
                name
            )

        async def reader(
            **kwargs,
        ):
            self.calls.append(
                (
                    name,
                    dict(kwargs),
                )
            )

            if self.error is not None:
                raise self.error

            return self.payload

        return reader


def _arguments():
    return {
        name: "test"
        for name
        in REQUIRED_ARGUMENTS_BY_METHOD[
            METHOD
        ]
    }


def test_manifests_keep_snapshot_pipeline_read_only():
    normalization = (
        snapshot_normalization_contract_manifest()
    )

    query = (
        snapshot_query_contract_manifest()
    )

    assert normalization[
        "persistence"
    ] is False
    assert normalization[
        "database_write"
    ] is False
    assert normalization[
        "filesystem_write"
    ] is False
    assert normalization[
        "network"
    ] is False
    assert normalization[
        "snapshot_creation"
    ] is False
    assert normalization[
        "write_methods_allowed"
    ] is False

    assert query[
        "persistence"
    ] is False
    assert query[
        "network"
    ] is False
    assert query[
        "snapshot_creation"
    ] is False
    assert query[
        "vendor_refresh"
    ] is False
    assert query[
        "production_registration"
    ] is False
    assert query[
        "write_methods_allowed"
    ] is False


def test_capability_surface_contains_only_snapshot_reads():
    assert set(
        CAPABILITY_BY_METHOD.values()
    ) == {
        "shopping.snapshot.get",
        "shopping.snapshot.list",
    }

    assert set(
        CAPABILITY_BY_METHOD
    ) == {
        "get_latest_snapshot",
        "list_snapshots",
    }


def test_normalization_is_deeply_isolated_from_source_mutation():
    payload = {
        "snapshot_id": "snapshot-1",
        "nested": {
            "items": [
                {
                    "value": 1,
                }
            ],
        },
    }

    result = normalize_snapshot(
        contract=CONTRACT,
        payload=payload,
    )

    before = result.to_json()

    payload[
        "nested"
    ][
        "items"
    ][0][
        "value"
    ] = 999

    assert result.to_json() == before


def test_query_to_json_returns_detached_data():
    repository = FakeRepository()

    async def allow(
        capability_id,
    ):
        return True

    result = asyncio.run(
        execute_snapshot_query(
            repository=repository,
            authorize=allow,
            method=METHOD,
            arguments=_arguments(),
        )
    )

    assert result is not None

    first = result.to_json()

    first[
        "snapshot"
    ][
        "nested"
    ][
        "value"
    ] = 999

    second = result.to_json()

    assert second[
        "snapshot"
    ][
        "nested"
    ][
        "value"
    ] == 1


def test_denied_authorization_never_reaches_repository():
    repository = FakeRepository()

    async def deny(
        capability_id,
    ):
        return False

    with pytest.raises(
        SnapshotQueryDenied,
        match="shopping.snapshot.authorization_denied",
    ):
        asyncio.run(
            execute_snapshot_query(
                repository=repository,
                authorize=deny,
                method=METHOD,
                arguments=_arguments(),
            )
        )

    assert repository.calls == []


def test_authorization_exception_is_fail_closed_and_sanitized():
    repository = FakeRepository()

    async def broken(
        capability_id,
    ):
        raise RuntimeError(
            "Authorization: Bearer policy-secret"
        )

    with pytest.raises(
        SnapshotQueryDenied,
    ) as captured:
        asyncio.run(
            execute_snapshot_query(
                repository=repository,
                authorize=broken,
                method=METHOD,
                arguments=_arguments(),
            )
        )

    assert str(
        captured.value
    ) == "shopping.snapshot.authorization_error"

    assert repository.calls == []


def test_repository_exception_is_sanitized():
    repository = FakeRepository(
        error=RuntimeError(
            "Authorization: Bearer vendor-secret"
        )
    )

    async def allow(
        capability_id,
    ):
        return True

    with pytest.raises(
        SnapshotQueryContractError,
    ) as captured:
        asyncio.run(
            execute_snapshot_query(
                repository=repository,
                authorize=allow,
                method=METHOD,
                arguments=_arguments(),
            )
        )

    assert str(
        captured.value
    ) == "shopping.snapshot.query.repository_error"


def test_write_like_method_is_rejected_before_authorization():
    repository = FakeRepository()
    authorization_calls = []

    async def allow(
        capability_id,
    ):
        authorization_calls.append(
            capability_id
        )
        return True

    with pytest.raises(
        SnapshotQueryContractError,
        match="shopping.snapshot.query.unknown_method",
    ):
        asyncio.run(
            execute_snapshot_query(
                repository=repository,
                authorize=allow,
                method="save_snapshot",
                arguments={},
            )
        )

    assert authorization_calls == []
    assert repository.calls == []


def test_snapshot_modules_have_no_forbidden_infrastructure_imports_or_writes():
    paths = (
        Path(
            "core/shopping/contracts/snapshot_normalization.py"
        ),
        Path(
            "core/shopping/application/snapshot_queries.py"
        ),
    )

    forbidden_imports = {
        "aiohttp",
        "httpx",
        "os",
        "redis",
        "requests",
        "shelve",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "subprocess",
        "urllib",
    }

    forbidden_calls = {
        "mkdir",
        "rename",
        "replace",
        "unlink",
        "write_bytes",
        "write_text",
    }

    for path in paths:
        tree = ast.parse(
            path.read_text(
                encoding="utf-8"
            )
        )

        imported = set()
        called = set()

        for node in ast.walk(
            tree
        ):
            if isinstance(
                node,
                ast.Import,
            ):
                for item in node.names:
                    imported.add(
                        item.name.split(
                            "."
                        )[0]
                    )

            elif (
                isinstance(
                    node,
                    ast.ImportFrom,
                )
                and node.module
            ):
                imported.add(
                    node.module.split(
                        "."
                    )[0]
                )

            elif isinstance(
                node,
                ast.Call,
            ):
                if isinstance(
                    node.func,
                    ast.Name,
                ):
                    called.add(
                        node.func.id
                    )

                elif isinstance(
                    node.func,
                    ast.Attribute,
                ):
                    called.add(
                        node.func.attr
                    )

        assert not (
            imported
            & forbidden_imports
        )

        assert not (
            called
            & forbidden_calls
        )


def test_query_module_does_not_own_governance_or_policy():
    path = Path(
        "core/shopping/application/snapshot_queries.py"
    )

    tree = ast.parse(
        path.read_text(
            encoding="utf-8"
        )
    )

    imported_modules = []

    for node in ast.walk(
        tree
    ):
        if (
            isinstance(
                node,
                ast.ImportFrom,
            )
            and node.module
        ):
            imported_modules.append(
                node.module
            )

        elif isinstance(
            node,
            ast.Import,
        ):
            imported_modules.extend(
                item.name
                for item
                in node.names
            )

    forbidden_fragments = (
        ".governance",
        "policy",
    )

    assert not any(
        fragment
        in module.lower()
        for module
        in imported_modules
        for fragment
        in forbidden_fragments
    )

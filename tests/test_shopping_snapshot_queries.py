from __future__ import annotations

import ast
import asyncio
from pathlib import Path

import pytest

from core.shopping.application.snapshot_queries import (
    ALLOWS_NONE_BY_METHOD,
    ARGUMENTS_BY_METHOD,
    CAPABILITY_BY_METHOD,
    CONTRACT_BY_METHOD,
    REQUIRED_ARGUMENTS_BY_METHOD,
    SnapshotQueryContractError,
    SnapshotQueryDenied,
    execute_snapshot_query,
    snapshot_query_contract_manifest,
)


FIRST_METHOD = "get_latest_snapshot"
SECOND_METHOD = "list_snapshots"


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
                "value": 1,
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
            raise AttributeError(name)

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


def _arguments(method):
    return {
        name: "test"
        for name
        in REQUIRED_ARGUMENTS_BY_METHOD[
            method
        ]
    }


def test_manifest_is_read_only_and_authorization_first():
    manifest = snapshot_query_contract_manifest()

    assert manifest["authorization_before_repository"] is True
    assert manifest["duplicate_authorization_framework"] is False
    assert manifest["repository_injected"] is True
    assert manifest["repository_owns_authorization"] is False
    assert manifest["persistence"] is False
    assert manifest["network"] is False
    assert manifest["snapshot_creation"] is False
    assert manifest["vendor_refresh"] is False
    assert manifest["write_methods_allowed"] is False


def test_manifest_preserves_authoritative_contract_maps():
    manifest = snapshot_query_contract_manifest()

    assert manifest["capability_by_method"] == dict(
        CAPABILITY_BY_METHOD
    )

    assert manifest["contract_by_method"] == dict(
        CONTRACT_BY_METHOD
    )

    assert manifest["allows_none_by_method"] == dict(
        ALLOWS_NONE_BY_METHOD
    )


def test_denied_query_never_calls_repository():
    repository = FakeRepository()

    async def deny(capability_id):
        return False

    with pytest.raises(
        SnapshotQueryDenied,
        match="shopping.snapshot.authorization_denied",
    ):
        asyncio.run(
            execute_snapshot_query(
                repository=repository,
                authorize=deny,
                method=FIRST_METHOD,
                arguments=_arguments(
                    FIRST_METHOD
                ),
            )
        )

    assert repository.calls == []


def test_authorization_error_fails_closed_before_repository():
    repository = FakeRepository()

    async def broken(capability_id):
        raise RuntimeError(
            "raw policy secret"
        )

    with pytest.raises(
        SnapshotQueryDenied,
        match="shopping.snapshot.authorization_error",
    ):
        asyncio.run(
            execute_snapshot_query(
                repository=repository,
                authorize=broken,
                method=FIRST_METHOD,
                arguments=_arguments(
                    FIRST_METHOD
                ),
            )
        )

    assert repository.calls == []


def test_allowed_first_method_calls_repository_once():
    repository = FakeRepository()

    async def allow(capability_id):
        return True

    result = asyncio.run(
        execute_snapshot_query(
            repository=repository,
            authorize=allow,
            method=FIRST_METHOD,
            arguments=_arguments(
                FIRST_METHOD
            ),
        )
    )

    assert len(
        repository.calls
    ) == 1

    assert (
        result is None
        or result.method
        == FIRST_METHOD
    )


def test_allowed_second_method_uses_repository_once():
    repository = FakeRepository()

    async def allow(capability_id):
        return True

    asyncio.run(
        execute_snapshot_query(
            repository=repository,
            authorize=allow,
            method=SECOND_METHOD,
            arguments=_arguments(
                SECOND_METHOD
            ),
        )
    )

    assert len(
        repository.calls
    ) == 1


def test_unknown_method_is_rejected_before_authorization():
    repository = FakeRepository()
    calls = []

    async def allow(capability_id):
        calls.append(
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

    assert calls == []
    assert repository.calls == []


def test_unknown_argument_is_rejected_before_authorization():
    repository = FakeRepository()
    calls = []

    async def allow(capability_id):
        calls.append(
            capability_id
        )
        return True

    arguments = _arguments(
        FIRST_METHOD
    )

    arguments[
        "vendor_private_option"
    ] = True

    with pytest.raises(
        SnapshotQueryContractError,
        match="shopping.snapshot.query.unknown_argument",
    ):
        asyncio.run(
            execute_snapshot_query(
                repository=repository,
                authorize=allow,
                method=FIRST_METHOD,
                arguments=arguments,
            )
        )

    assert calls == []
    assert repository.calls == []


def test_required_argument_contract_is_enforced_or_empty():
    required = sorted(
        REQUIRED_ARGUMENTS_BY_METHOD[
            FIRST_METHOD
        ]
    )

    if not required:
        assert REQUIRED_ARGUMENTS_BY_METHOD[
            FIRST_METHOD
        ] == frozenset()
        return

    repository = FakeRepository()
    calls = []

    async def allow(capability_id):
        calls.append(
            capability_id
        )
        return True

    arguments = _arguments(
        FIRST_METHOD
    )

    arguments.pop(
        required[0]
    )

    with pytest.raises(
        SnapshotQueryContractError,
        match="shopping.snapshot.query.required_argument_missing",
    ):
        asyncio.run(
            execute_snapshot_query(
                repository=repository,
                authorize=allow,
                method=FIRST_METHOD,
                arguments=arguments,
            )
        )

    assert calls == []
    assert repository.calls == []


def test_repository_error_is_sanitized():
    repository = FakeRepository(
        error=RuntimeError(
            "Authorization: Bearer vendor-secret"
        )
    )

    async def allow(capability_id):
        return True

    with pytest.raises(
        SnapshotQueryContractError,
        match="shopping.snapshot.query.repository_error",
    ):
        asyncio.run(
            execute_snapshot_query(
                repository=repository,
                authorize=allow,
                method=FIRST_METHOD,
                arguments=_arguments(
                    FIRST_METHOD
                ),
            )
        )


def test_non_mapping_repository_payload_is_rejected():
    repository = FakeRepository(
        payload=[
            {
                "snapshot_id": "unsafe",
            }
        ]
    )

    async def allow(capability_id):
        return True

    with pytest.raises(
        SnapshotQueryContractError,
        match="shopping.snapshot.query.canonical_object_required",
    ):
        asyncio.run(
            execute_snapshot_query(
                repository=repository,
                authorize=allow,
                method=FIRST_METHOD,
                arguments=_arguments(
                    FIRST_METHOD
                ),
            )
        )


def test_result_isolated_from_repository_payload_mutation():
    payload = {
        "snapshot_id": "snapshot-1",
        "nested": {
            "value": 1,
        },
    }

    repository = FakeRepository(
        payload=payload
    )

    async def allow(capability_id):
        return True

    result = asyncio.run(
        execute_snapshot_query(
            repository=repository,
            authorize=allow,
            method=FIRST_METHOD,
            arguments=_arguments(
                FIRST_METHOD
            ),
        )
    )

    assert result is not None

    before = result.to_json()

    payload[
        "nested"
    ][
        "value"
    ] = 999

    assert result.to_json() == before


def test_module_has_no_network_persistence_or_write_imports():
    path = Path(
        "core/shopping/application/snapshot_queries.py"
    )

    tree = ast.parse(
        path.read_text(
            encoding="utf-8"
        )
    )

    forbidden = {
        "aiohttp",
        "httpx",
        "os",
        "pathlib",
        "redis",
        "requests",
        "shelve",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "subprocess",
        "urllib",
    }

    imported = set()

    for node in ast.walk(tree):
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

    assert not (
        imported
        & forbidden
    )

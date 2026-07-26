from __future__ import annotations

import ast
import asyncio
import json
import math
from copy import deepcopy
from pathlib import Path

import core.shopping.application.schema_drift_monitor as monitor_module
import core.shopping.contracts.schema_drift as drift_module
import core.shopping.contracts.schema_validation as validation_module

from core.shopping.application.schema_drift_monitor import (
    SchemaDriftMonitorStatus,
    monitor_schema_drift,
)
from core.shopping.contracts.schema_drift import (
    DriftStatus,
    classify_schema_drift,
)
from core.shopping.contracts.schema_validation import (
    SchemaCatalog,
    ValidationStatus,
    validate_instance,
)


DRAFT = (
    "https://json-schema.org/draft/2020-12/schema"
)

SCHEMA_ID = "urn:test:hardening"
ADAPTER_NAME = "hardening-adapter"

BASE = {
    "$id": SCHEMA_ID,
    "$schema": DRAFT,
    "additionalProperties": False,
    "properties": {
        "age": {
            "type": "integer",
        },
        "name": {
            "type": "string",
        },
    },
    "required": [
        "name",
    ],
    "type": "object",
}


def _catalog():
    return SchemaCatalog.from_documents(
        documents={
            SCHEMA_ID: deepcopy(
                BASE
            ),
        }
    )


def _run(
    coroutine,
):
    return asyncio.run(
        coroutine
    )


class DenyAuthorization:
    def __init__(
        self,
    ):
        self.calls = 0

    async def __call__(
        self,
        **kwargs,
    ):
        self.calls += 1
        return False


class ExplodingAuthorization:
    async def __call__(
        self,
        **kwargs,
    ):
        raise RuntimeError(
            "raw authorization secret"
        )


class Discovery:
    def __init__(
        self,
        *,
        value=None,
        error=False,
    ):
        self.value = value
        self.error = error
        self.calls = 0

    async def discover_schema(
        self,
        *,
        context,
        adapter_name,
    ):
        self.calls += 1

        if self.error:
            raise RuntimeError(
                "raw vendor token"
            )

        return self.value


def test_schema_catalog_defensively_copies_source_documents():
    source = deepcopy(
        BASE
    )

    catalog = SchemaCatalog.from_documents(
        documents={
            SCHEMA_ID: source,
        }
    )

    source[
        "required"
    ].append(
        "age"
    )

    loaded = catalog.get_schema(
        SCHEMA_ID
    )

    assert loaded[
        "required"
    ] == [
        "name",
    ]


def test_unknown_schema_validation_is_fail_closed_and_sanitized():
    result = validate_instance(
        catalog=_catalog(),
        schema_id="urn:test:missing",
        instance={
            "name": "safe",
        },
    )

    assert result.status is (
        ValidationStatus.ERROR
    )

    assert result.accepted is False

    encoded = json.dumps(
        result.to_json(),
        sort_keys=True,
    )

    assert "Traceback" not in encoded
    assert "secret" not in encoded.lower()


def test_non_json_candidate_drift_is_unknown_and_never_adopts():
    candidate = deepcopy(
        BASE
    )

    candidate[
        "x-non-json"
    ] = math.nan

    result = classify_schema_drift(
        canonical_schema=BASE,
        candidate_schema=candidate,
    )

    assert result.status is (
        DriftStatus.UNKNOWN_DRIFT
    )

    assert result.auto_adopt is False


def test_unsupported_schema_keyword_change_is_unknown():
    candidate = deepcopy(
        BASE
    )

    candidate[
        "x-vendor-extension"
    ] = {
        "mode": "unexpected",
    }

    result = classify_schema_drift(
        canonical_schema=BASE,
        candidate_schema=candidate,
    )

    assert result.status is (
        DriftStatus.UNKNOWN_DRIFT
    )

    assert result.auto_adopt is False


def test_consumer_safety_direction_distinguishes_narrowing_and_widening():
    narrowing = deepcopy(
        BASE
    )

    narrowing[
        "required"
    ].append(
        "age"
    )

    widening = deepcopy(
        BASE
    )

    widening[
        "required"
    ] = []

    narrowed = classify_schema_drift(
        canonical_schema=BASE,
        candidate_schema=narrowing,
    )

    widened = classify_schema_drift(
        canonical_schema=BASE,
        candidate_schema=widening,
    )

    assert narrowed.status is (
        DriftStatus.COMPATIBLE_DRIFT
    )

    assert widened.status is (
        DriftStatus.BREAKING_DRIFT
    )

    assert narrowed.auto_adopt is False
    assert widened.auto_adopt is False


def test_authorization_denial_prevents_schema_discovery():
    authorization = (
        DenyAuthorization()
    )

    discovery = Discovery(
        value=deepcopy(
            BASE
        )
    )

    result = _run(
        monitor_schema_drift(
            authorize=authorization,
            discovery_port=discovery,
            schema_id=SCHEMA_ID,
            adapter_name=ADAPTER_NAME,
            catalog=_catalog(),
        )
    )

    assert result.status is (
        SchemaDriftMonitorStatus.DENIED
    )

    assert authorization.calls == 1
    assert discovery.calls == 0


def test_authorization_exception_is_sanitized_and_prevents_discovery():
    discovery = Discovery(
        value=deepcopy(
            BASE
        )
    )

    result = _run(
        monitor_schema_drift(
            authorize=(
                ExplodingAuthorization()
            ),
            discovery_port=discovery,
            schema_id=SCHEMA_ID,
            adapter_name=ADAPTER_NAME,
            catalog=_catalog(),
        )
    )

    assert result.status is (
        SchemaDriftMonitorStatus.ERROR
    )

    assert result.error_code == (
        "shopping.schema.drift_monitor.authorization_error"
    )

    assert discovery.calls == 0

    encoded = json.dumps(
        result.to_json(),
        sort_keys=True,
    )

    assert "raw authorization secret" not in encoded


def test_discovery_exception_is_sanitized():
    discovery = Discovery(
        error=True
    )

    result = _run(
        monitor_schema_drift(
            authorize=lambda **kwargs: True,
            discovery_port=discovery,
            schema_id=SCHEMA_ID,
            adapter_name=ADAPTER_NAME,
            catalog=_catalog(),
        )
    )

    assert result.status is (
        SchemaDriftMonitorStatus.ERROR
    )

    assert result.error_code == (
        "shopping.schema.drift_monitor.discovery_error"
    )

    encoded = json.dumps(
        result.to_json(),
        sort_keys=True,
    )

    assert "raw vendor token" not in encoded


def test_spf009_source_modules_preserve_read_only_isolation():
    repo = Path(
        __file__
    ).resolve().parents[
        1
    ]

    sources = (
        repo
        / "core/shopping/contracts/schema_validation.py",
        repo
        / "core/shopping/contracts/schema_drift.py",
        repo
        / "core/shopping/application/schema_drift_monitor.py",
    )

    forbidden_import_roots = {
        "aiohttp",
        "boto3",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }

    forbidden_call_attributes = {
        "mkdir",
        "rename",
        "replace",
        "rmdir",
        "unlink",
        "write_bytes",
        "write_text",
    }

    problems = []

    for source_path in sources:
        tree = ast.parse(
            source_path.read_text(
                encoding="utf-8"
            ),
            filename=str(
                source_path
            ),
        )

        for node in ast.walk(
            tree
        ):
            if isinstance(
                node,
                ast.Import,
            ):
                for item in node.names:
                    root = item.name.split(
                        "."
                    )[
                        0
                    ]

                    if root in forbidden_import_roots:
                        problems.append(
                            item.name
                        )

            elif (
                isinstance(
                    node,
                    ast.ImportFrom,
                )
                and node.module
            ):
                root = node.module.split(
                    "."
                )[
                    0
                ]

                if root in forbidden_import_roots:
                    problems.append(
                        node.module
                    )

                if node.module.startswith(
                    "core.shopping.governance"
                ):
                    problems.append(
                        node.module
                    )

            elif (
                isinstance(
                    node,
                    ast.Call,
                )
                and isinstance(
                    node.func,
                    ast.Attribute,
                )
                and node.func.attr
                in forbidden_call_attributes
            ):
                problems.append(
                    node.func.attr
                )

    public_names = set()

    for module in (
        validation_module,
        drift_module,
        monitor_module,
    ):
        public_names.update(
            getattr(
                module,
                "__all__",
                (),
            )
        )

    forbidden_public_tokens = (
        "adopt",
        "apply",
        "create_snapshot",
        "delete",
        "migrate",
        "save",
        "update",
        "write",
    )

    assert problems == []

    assert not any(
        token in name.lower()
        for name
        in public_names
        for token
        in forbidden_public_tokens
    )


def test_schema_discovery_port_contract_remains_keyword_only_context_adapter_name():
    repo = Path(
        __file__
    ).resolve().parents[
        1
    ]

    matches = []

    for path in sorted(
        (
            repo
            / "core/shopping/ports"
        ).rglob(
            "*.py"
        )
    ):
        tree = ast.parse(
            path.read_text(
                encoding="utf-8"
            ),
            filename=str(
                path
            ),
        )

        for node in tree.body:
            if (
                isinstance(
                    node,
                    ast.ClassDef,
                )
                and node.name
                == "SchemaDiscoveryPort"
            ):
                for child in node.body:
                    if (
                        isinstance(
                            child,
                            ast.AsyncFunctionDef,
                        )
                        and child.name
                        == "discover_schema"
                    ):
                        matches.append(
                            child
                        )

    assert len(
        matches
    ) == 1

    method = matches[
        0
    ]

    positional = (
        list(
            method.args.posonlyargs
        )
        + list(
            method.args.args
        )
    )

    assert [
        item.arg
        for item
        in positional
    ] == [
        "self",
    ]

    assert [
        item.arg
        for item
        in method.args.kwonlyargs
    ] == [
        "context",
        "adapter_name",
    ]

    assert all(
        value is None
        for value
        in method.args.kw_defaults
    )

    assert method.returns is not None

    assert ast.unparse(
        method.returns
    ) == "SchemaDiscoveryResult"

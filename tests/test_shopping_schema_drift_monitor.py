from __future__ import annotations

import asyncio
import json
from copy import deepcopy
from dataclasses import dataclass

from core.shopping.application.schema_drift_monitor import (
    AUTHORIZATION_KEYWORDS,
    DISCOVERY_REQUIRED_KEYWORDS,
    SCHEMA_DISCOVERY_CAPABILITY,
    SchemaDriftMonitorStatus,
    monitor_schema_drift,
    schema_drift_monitor_contract_manifest,
)
from core.shopping.contracts.schema_drift import (
    DriftStatus,
)
from core.shopping.contracts.schema_validation import (
    SchemaCatalog,
)


DRAFT = (
    "https://json-schema.org/draft/2020-12/schema"
)

SCHEMA_ID = "urn:test:monitor"
ADAPTER_NAME = "commerce-test"

BASE = {
    "$id": SCHEMA_ID,
    "$schema": DRAFT,
    "additionalProperties": False,
    "properties": {
        "name": {
            "type": "string",
        },
    },
    "required": [
        "name",
    ],
    "type": "object",
}


def _run(
    coroutine,
):
    return asyncio.run(
        coroutine
    )


def _catalog():
    return SchemaCatalog.from_documents(
        documents={
            SCHEMA_ID: BASE,
        }
    )


class Authorize:
    def __init__(
        self,
        *,
        value=True,
        error=False,
        events=None,
    ):
        self.value = value
        self.error = error
        self.calls = []
        self.events = events

    async def __call__(
        self,
        **kwargs,
    ):
        self.calls.append(
            dict(
                kwargs
            )
        )

        if self.events is not None:
            self.events.append(
                "authorize"
            )

        if self.error:
            raise RuntimeError(
                "sensitive authorization failure"
            )

        return self.value


class Discovery:
    def __init__(
        self,
        *,
        value,
        error=False,
        events=None,
    ):
        self.value = value
        self.error = error
        self.calls = []
        self.events = events

    async def discover_schema(
        self,
        *,
        context,
        adapter_name,
    ):
        self.calls.append(
            {
                "adapter_name": adapter_name,
                "context": context,
            }
        )

        if self.events is not None:
            self.events.append(
                "discover"
            )

        if self.error:
            raise RuntimeError(
                "sensitive vendor failure"
            )

        return self.value


@dataclass(
    frozen=True,
)
class SchemaDiscoveryEnvelope:
    adapter_name: str
    payload: object


def test_manifest_preserves_read_only_boundary():
    manifest = (
        schema_drift_monitor_contract_manifest()
    )

    assert manifest[
        "adapter_name_required"
    ] is True

    assert manifest[
        "authorization_before_discovery"
    ] is True

    assert manifest[
        "authorization_capability"
    ] == SCHEMA_DISCOVERY_CAPABILITY

    assert manifest[
        "discovery_keyword_contract"
    ] == [
        "context",
        "adapter_name",
    ]

    assert manifest[
        "schema_id_and_adapter_name_separated"
    ] is True

    assert manifest[
        "automatic_adoption"
    ] is False

    assert manifest[
        "schema_mutation"
    ] is False

    assert manifest[
        "persistence"
    ] is False

    assert manifest[
        "database_write"
    ] is False

    assert manifest[
        "production_registration"
    ] is False

    assert manifest[
        "write_methods_allowed"
    ] is False


def test_adapter_name_is_required_before_authorization():
    authorization = Authorize()

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
            adapter_name="",
            catalog=_catalog(),
        )
    )

    assert result.status is (
        SchemaDriftMonitorStatus.ERROR
    )

    assert result.error_code == (
        "shopping.schema.drift_monitor.adapter_name_required"
    )

    assert len(
        authorization.calls
    ) == 0

    assert len(
        discovery.calls
    ) == 0


def test_authorization_happens_before_discovery_and_no_drift():
    events = []

    authorization = Authorize(
        events=events
    )

    discovery = Discovery(
        value=deepcopy(
            BASE
        ),
        events=events,
    )

    result = _run(
        monitor_schema_drift(
            authorize=authorization,
            discovery_port=discovery,
            schema_id=SCHEMA_ID,
            adapter_name=ADAPTER_NAME,
            context={
                "actor": "test",
            },
            catalog=_catalog(),
        )
    )

    assert events == [
        "authorize",
        "discover",
    ]

    assert result.status is (
        SchemaDriftMonitorStatus.OK
    )

    assert result.drift is not None

    assert result.drift.status is (
        DriftStatus.NO_DRIFT
    )


def test_authorization_denial_prevents_discovery():
    authorization = Authorize(
        value=False
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

    assert len(
        discovery.calls
    ) == 0


def test_authorization_exception_fails_closed_and_is_sanitized():
    authorization = Authorize(
        error=True
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
        SchemaDriftMonitorStatus.ERROR
    )

    assert result.error_code == (
        "shopping.schema.drift_monitor.authorization_error"
    )

    assert len(
        discovery.calls
    ) == 0

    assert "sensitive" not in json.dumps(
        result.to_json()
    )


def test_unknown_authorization_shape_fails_closed():
    authorization = Authorize(
        value={
            "unexpected": "value",
        }
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

    assert len(
        discovery.calls
    ) == 0


def test_discovery_receives_exact_context_and_adapter_name():
    authorization = Authorize()

    discovery = Discovery(
        value=deepcopy(
            BASE
        )
    )

    context = {
        "request": "test",
    }

    _run(
        monitor_schema_drift(
            authorize=authorization,
            discovery_port=discovery,
            schema_id=SCHEMA_ID,
            adapter_name=ADAPTER_NAME,
            context=context,
            catalog=_catalog(),
        )
    )

    assert len(
        discovery.calls
    ) == 1

    assert set(
        discovery.calls[
            0
        ]
    ) == {
        "context",
        "adapter_name",
    }

    assert discovery.calls[
        0
    ][
        "context"
    ] is context

    assert discovery.calls[
        0
    ][
        "adapter_name"
    ] == ADAPTER_NAME

    assert DISCOVERY_REQUIRED_KEYWORDS == (
        "context",
        "adapter_name",
    )

    assert set(
        authorization.calls[
            0
        ]
    ) == set(
        AUTHORIZATION_KEYWORDS
    )


def test_discovery_exception_is_sanitized():
    result = _run(
        monitor_schema_drift(
            authorize=Authorize(),
            discovery_port=Discovery(
                value=None,
                error=True,
            ),
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

    assert "sensitive" not in json.dumps(
        result.to_json()
    )


def test_invalid_discovery_payload_is_rejected():
    result = _run(
        monitor_schema_drift(
            authorize=Authorize(),
            discovery_port=Discovery(
                value=[
                    "not",
                    "schema",
                ]
            ),
            schema_id=SCHEMA_ID,
            adapter_name=ADAPTER_NAME,
            catalog=_catalog(),
        )
    )

    assert result.status is (
        SchemaDriftMonitorStatus.ERROR
    )

    assert result.error_code == (
        "shopping.schema.drift_monitor.invalid_payload"
    )


def test_schema_discovery_result_style_dataclass_payload_is_supported():
    envelope = SchemaDiscoveryEnvelope(
        adapter_name=ADAPTER_NAME,
        payload={
            "schema": deepcopy(
                BASE
            ),
        },
    )

    result = _run(
        monitor_schema_drift(
            authorize=Authorize(),
            discovery_port=Discovery(
                value=envelope
            ),
            schema_id=SCHEMA_ID,
            adapter_name=ADAPTER_NAME,
            catalog=_catalog(),
        )
    )

    assert result.status is (
        SchemaDriftMonitorStatus.OK
    )

    assert result.drift is not None

    assert result.drift.status is (
        DriftStatus.NO_DRIFT
    )


def test_unknown_canonical_schema_fails_before_discovery():
    discovery = Discovery(
        value=deepcopy(
            BASE
        )
    )

    result = _run(
        monitor_schema_drift(
            authorize=Authorize(),
            discovery_port=discovery,
            schema_id="urn:test:missing",
            adapter_name=ADAPTER_NAME,
            catalog=_catalog(),
        )
    )

    assert result.status is (
        SchemaDriftMonitorStatus.ERROR
    )

    assert result.error_code == (
        "shopping.schema.drift_monitor.unknown_schema"
    )

    assert len(
        discovery.calls
    ) == 0


def test_compatible_drift_is_reported_without_adoption():
    candidate = deepcopy(
        BASE
    )

    candidate[
        "description"
    ] = "metadata"

    result = _run(
        monitor_schema_drift(
            authorize=Authorize(),
            discovery_port=Discovery(
                value=candidate
            ),
            schema_id=SCHEMA_ID,
            adapter_name=ADAPTER_NAME,
            catalog=_catalog(),
        )
    )

    assert result.drift is not None

    assert result.drift.status is (
        DriftStatus.COMPATIBLE_DRIFT
    )

    assert result.auto_adopt is False


def test_breaking_drift_is_reported_without_adoption():
    candidate = deepcopy(
        BASE
    )

    candidate[
        "additionalProperties"
    ] = True

    result = _run(
        monitor_schema_drift(
            authorize=Authorize(),
            discovery_port=Discovery(
                value=candidate
            ),
            schema_id=SCHEMA_ID,
            adapter_name=ADAPTER_NAME,
            catalog=_catalog(),
        )
    )

    assert result.drift is not None

    assert result.drift.status is (
        DriftStatus.BREAKING_DRIFT
    )

    assert result.auto_adopt is False


def test_unknown_drift_is_fail_closed_for_adoption():
    candidate = deepcopy(
        BASE
    )

    candidate[
        "$id"
    ] = "urn:test:other"

    result = _run(
        monitor_schema_drift(
            authorize=Authorize(),
            discovery_port=Discovery(
                value=candidate
            ),
            schema_id=SCHEMA_ID,
            adapter_name=ADAPTER_NAME,
            catalog=_catalog(),
        )
    )

    assert result.drift is not None

    assert result.drift.status is (
        DriftStatus.UNKNOWN_DRIFT
    )

    assert result.to_json()[
        "auto_adopt"
    ] is False


def test_result_json_is_deterministic_and_sanitized():
    candidate = deepcopy(
        BASE
    )

    candidate[
        "description"
    ] = "changed"

    first = _run(
        monitor_schema_drift(
            authorize=Authorize(),
            discovery_port=Discovery(
                value=candidate
            ),
            schema_id=SCHEMA_ID,
            adapter_name=ADAPTER_NAME,
            catalog=_catalog(),
        )
    )

    second = _run(
        monitor_schema_drift(
            authorize=Authorize(),
            discovery_port=Discovery(
                value=candidate
            ),
            schema_id=SCHEMA_ID,
            adapter_name=ADAPTER_NAME,
            catalog=_catalog(),
        )
    )

    assert first.to_json() == (
        second.to_json()
    )

    encoded = json.dumps(
        first.to_json(),
        sort_keys=True,
    )

    assert "Traceback" not in encoded
    assert "sensitive vendor" not in encoded

from __future__ import annotations

import json
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from core.governance.operations.scheduler import _normalize


@dataclass(frozen=True, slots=True)
class ImmutableSnapshot:
    operation: str
    metadata: Mapping[str, Any]


def test_mappingproxy_dataclass_is_normalized() -> None:
    snapshot = ImmutableSnapshot(
        operation="governance_audit_snapshot",
        metadata=MappingProxyType(
            {
                "policy": MappingProxyType(
                    {
                        "automatic_retry": False,
                        "automatic_restore": False,
                    }
                )
            }
        ),
    )

    assert _normalize(snapshot) == {
        "operation": "governance_audit_snapshot",
        "metadata": {
            "policy": {
                "automatic_retry": False,
                "automatic_restore": False,
            }
        },
    }


def test_mappingproxy_snapshot_is_json_serializable() -> None:
    metadata = MappingProxyType(
        {
            "result": "PASS",
            "details": MappingProxyType(
                {"event_count": 3}
            ),
        }
    )
    snapshot = ImmutableSnapshot(
        operation="governance_audit_snapshot",
        metadata=metadata,
    )

    normalized = _normalize(snapshot)
    encoded = json.dumps(
        normalized,
        sort_keys=True,
    )

    assert normalized["metadata"] == {
        "result": "PASS",
        "details": {
            "event_count": 3,
        },
    }
    assert '"event_count": 3' in encoded
    assert metadata["details"]["event_count"] == 3


def test_direct_mappingproxy_is_normalized() -> None:
    value = MappingProxyType(
        {
            "outer": MappingProxyType(
                {"inner": "value"}
            )
        }
    )

    assert _normalize(value) == {
        "outer": {
            "inner": "value",
        }
    }

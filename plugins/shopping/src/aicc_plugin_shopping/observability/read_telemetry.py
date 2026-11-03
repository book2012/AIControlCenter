"""Bounded, instance-local observations of completed canonical catalog reads."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import json
from threading import Lock
from time import monotonic_ns
from typing import Any

from .health_monitor import HealthMonitorSnapshot, aggregate_health
from .health_probe import (
    DEFAULT_STATE_BY_FAILURE,
    HealthFailureCode,
    HealthProbeResult,
    normalize_adapter_health,
)


class CatalogReadOperation(str, Enum):
    LIST = "list_products"
    DETAIL = "get_product"
    HEALTH = "read_path_health"


class CatalogReadOutcome(str, Enum):
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    INVALID_QUERY = "invalid_query"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class CatalogReadTelemetrySnapshot:
    total: int
    health: HealthMonitorSnapshot
    _operation_json: tuple[tuple[str, str], ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "scope": "service_instance",
            "observation_basis": "last_completed_read_per_operation",
            "total": self.total,
            "operations": {key: json.loads(value) for key, value in self._operation_json},
            "health": self.health.to_json(),
        }


class CatalogReadTelemetry:
    """Three fixed slots; no event history, product data, I/O, or registration.

    Counts describe service invocations, not HTTP attempts. Query rejections
    carry no adapter-health evidence. Locks cover publication/snapshot only.
    """

    def __init__(
        self,
        *,
        clock_ns: Callable[[], int] = monotonic_ns,
        utc_now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self._clock_ns = clock_ns
        self._utc_now = utc_now
        self._lock = Lock()
        self._operations = {
            operation: {
                "total": 0,
                "outcomes": {outcome.value: 0 for outcome in CatalogReadOutcome},
                "failures": {code.value: 0 for code in HealthFailureCode
                             if code not in (HealthFailureCode.NONE, HealthFailureCode.LATENCY)},
                "last": None,
            }
            for operation in CatalogReadOperation
        }
        self._health: dict[str, HealthProbeResult] = {}

    def start(self) -> int | None:
        try:
            value = self._clock_ns()
            return value if type(value) is int and value >= 0 else None
        except Exception:
            return None

    def record(
        self,
        operation: CatalogReadOperation,
        outcome: CatalogReadOutcome,
        failure: HealthFailureCode | None,
        started_ns: int | None,
    ) -> None:
        if outcome is CatalogReadOutcome.UNAVAILABLE and failure is None:
            failure = HealthFailureCode.UNKNOWN
        finished_ns = self.start()
        latency_ms = (
            (finished_ns - started_ns) // 1_000_000
            if started_ns is not None and finished_ns is not None and finished_ns >= started_ns
            else None
        )
        probe = None
        if failure is not None:
            checked_at = self._utc_now()
            if checked_at.tzinfo is None or checked_at.utcoffset() is None:
                raise ValueError("shopping.telemetry.utc_clock_required")
            probe = normalize_adapter_health(
                base={
                    "adapter": "catalog",
                    "checked_at": checked_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "latency_ms": latency_ms,
                    "message": None,
                },
                state=DEFAULT_STATE_BY_FAILURE[failure],
                failure_code=failure,
                latency_ms=latency_ms,
                detail_code=f"shopping.catalog.read.{outcome.value}",
            )

        with self._lock:
            entry = self._operations[operation]
            entry["total"] += 1
            entry["outcomes"][outcome.value] += 1
            if outcome is CatalogReadOutcome.UNAVAILABLE:
                entry["failures"][failure.value] += 1
            entry["last"] = {"outcome": outcome.value, "probe": probe.to_json() if probe else None}
            # A rejected query is not new dependency evidence and cannot erase
            # the last observed failure (or success).
            if probe is not None:
                self._health[operation.value] = probe

    def snapshot(self) -> CatalogReadTelemetrySnapshot:
        with self._lock:
            return CatalogReadTelemetrySnapshot(
                total=sum(entry["total"] for entry in self._operations.values()),
                health=aggregate_health(adapters=self._health),
                _operation_json=tuple(
                    (operation.value, json.dumps(entry, sort_keys=True, ensure_ascii=False,
                                                 allow_nan=False, separators=(",", ":")))
                    for operation, entry in sorted(self._operations.items())
                ),
            )

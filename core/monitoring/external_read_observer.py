from __future__ import annotations

import inspect
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Mapping


JsonMapping = Mapping[str, Any]
StageCallable = Callable[..., JsonMapping | Awaitable[JsonMapping]]

_SECRET_KEY_FRAGMENTS = (
    "password",
    "secret",
    "token",
    "authorization",
    "consumer_key",
    "consumer_secret",
    "api_key",
)


class ObservationContractError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ObservationStage:
    name: str
    ok: bool
    payload: dict[str, Any]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "ok": self.ok,
            "payload": self.payload,
        }


@dataclass(frozen=True, slots=True)
class ExternalReadObservation:
    source: str
    observed_at: str
    stages: tuple[ObservationStage, ...]

    @property
    def ok(self) -> bool:
        return all(stage.ok for stage in self.stages)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "observed_at": self.observed_at,
            "result": "PASS" if self.ok else "FAIL",
            "stages": [stage.to_json_dict() for stage in self.stages],
        }


def _assert_secret_free(value: Any, path: str = "root") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key).lower()
            if any(fragment in key_text for fragment in _SECRET_KEY_FRAGMENTS):
                raise ObservationContractError("secret-like evidence key denied at " + path + "." + str(key))
            _assert_secret_free(nested, path + "." + str(key))
        return

    if isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            _assert_secret_free(nested, path + "[" + str(index) + "]")
        return

    if value is None or isinstance(value, (str, int, float, bool)):
        return

    raise ObservationContractError("evidence value is not JSON-safe at " + path)


async def _resolve(callback: StageCallable, *args: Any) -> Mapping[str, Any]:
    value = callback(*args)
    if inspect.isawaitable(value):
        value = await value
    if not isinstance(value, Mapping):
        raise ObservationContractError("observation stage must return a mapping")
    return value


def _normalize_stage(name: str, value: Mapping[str, Any]) -> ObservationStage:
    payload = dict(value)
    ok = payload.get("ok")
    if not isinstance(ok, bool):
        raise ObservationContractError(name + " stage requires boolean ok")
    _assert_secret_free(payload)
    return ObservationStage(name=name, ok=ok, payload=payload)


class ExternalReadObserver:
    def __init__(
        self,
        *,
        health_probe: StageCallable,
        schema_probe: StageCallable,
        snapshot_reader: StageCallable,
        drift_detector: StageCallable,
    ) -> None:
        self._health_probe = health_probe
        self._schema_probe = schema_probe
        self._snapshot_reader = snapshot_reader
        self._drift_detector = drift_detector

    async def observe(self, *, source: str) -> ExternalReadObservation:
        if not source:
            raise ObservationContractError("source is required")

        stages: list[ObservationStage] = []

        health = await _resolve(self._health_probe)
        stages.append(_normalize_stage("health", health))

        schema = await _resolve(self._schema_probe)
        stages.append(_normalize_stage("schema", schema))

        snapshot = await _resolve(self._snapshot_reader)
        stages.append(_normalize_stage("snapshot", snapshot))

        drift = await _resolve(self._drift_detector, snapshot)
        stages.append(_normalize_stage("drift", drift))

        observation = ExternalReadObservation(
            source=source,
            observed_at=datetime.now(timezone.utc).isoformat(),
            stages=tuple(stages),
        )

        _assert_secret_free(observation.to_json_dict())
        return observation

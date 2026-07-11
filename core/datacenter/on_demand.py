from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class DatacenterPowerState(str, Enum):
    READY = "READY"
    ONLINE = "ONLINE"
    BUSY = "BUSY"
    WAKING = "WAKING"
    SHUTTING_DOWN = "SHUTTING_DOWN"
    OFFLINE_EXPECTED = "OFFLINE_EXPECTED"
    OFFLINE_UNEXPECTED = "OFFLINE_UNEXPECTED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class OnDemandContext:
    expected_online: bool = False
    waking: bool = False
    shutting_down: bool = False
    running_tasks: int = 0


class OnDemandStateService:
    ONLINE_STATES = {
        "READY",
        "ONLINE",
        "WARNING",
        "RECOVERY",
    }

    OFFLINE_STATES = {
        "OFFLINE",
        "UNAVAILABLE",
    }

    def evaluate(
        self,
        worker: dict[str, Any],
        context: OnDemandContext | None = None,
    ) -> dict[str, Any]:
        context = context or OnDemandContext()

        raw_status = str(
            worker.get("status", "UNKNOWN")
        ).upper()

        if context.shutting_down:
            state = DatacenterPowerState.SHUTTING_DOWN

        elif context.waking:
            state = DatacenterPowerState.WAKING

        elif raw_status in self.ONLINE_STATES:
            if context.running_tasks > 0:
                state = DatacenterPowerState.BUSY
            elif raw_status == "READY":
                state = DatacenterPowerState.READY
            else:
                state = DatacenterPowerState.ONLINE

        elif raw_status in self.OFFLINE_STATES:
            state = (
                DatacenterPowerState.OFFLINE_UNEXPECTED
                if context.expected_online
                else DatacenterPowerState.OFFLINE_EXPECTED
            )

        else:
            state = DatacenterPowerState.UNKNOWN

        return {
            "state": state.value,
            "raw_worker_status": raw_status,
            "expected_online": context.expected_online,
            "running_tasks": context.running_tasks,
            "waking": context.waking,
            "shutting_down": context.shutting_down,
            "is_available": state in {
                DatacenterPowerState.READY,
                DatacenterPowerState.ONLINE,
                DatacenterPowerState.BUSY,
            },
            "requires_attention": state in {
                DatacenterPowerState.OFFLINE_UNEXPECTED,
                DatacenterPowerState.UNKNOWN,
            },
        }

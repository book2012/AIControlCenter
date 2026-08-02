"""Deterministic, isolated fake Commerce write adapter."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..serialization import sha256_digest
from ..values import require_utc
from .models import ControlledWritePlan, WriteMode
from .write_port import CommerceWriteResult


@dataclass(frozen=True, slots=True)
class FakeCallSummary:
    plan_digest: str
    completed_at: datetime


class FakeCommerceProductWriteAdapter:
    def __init__(self, *, mode: WriteMode = WriteMode.FAKE,
                 adapter_identifier: str = "FAKE_COMMERCE_PRODUCT_WRITE_V1") -> None:
        if mode not in (WriteMode.FAKE, WriteMode.DRY_RUN):
            raise ValueError("fake adapter mode must be FAKE or DRY_RUN")
        self._mode = mode
        self._identifier = adapter_identifier
        self._calls: list[FakeCallSummary] = []

    @property
    def calls(self) -> tuple[FakeCallSummary, ...]:
        return tuple(self._calls)

    def apply(self, plan: ControlledWritePlan, *, completed_at: datetime) -> CommerceWriteResult:
        if not isinstance(plan, ControlledWritePlan):
            raise TypeError("plan must be a ControlledWritePlan")
        require_utc(completed_at, "completed_at")
        self._calls.append(FakeCallSummary(plan.plan_digest, completed_at))
        digest = sha256_digest({"adapter_identifier": self._identifier,
                                "mode": self._mode.value,
                                "plan_digest": plan.plan_digest})
        return CommerceWriteResult(self._mode, self._identifier, plan.plan_digest,
                                   digest, completed_at, False)

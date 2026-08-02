"""Commerce write port accepting controlled plans only."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from ..values import require_digest, require_text, require_utc
from .models import ControlledWritePlan, WriteMode


@dataclass(frozen=True, slots=True)
class CommerceWriteResult:
    mode: WriteMode
    adapter_identifier: str
    plan_digest: str
    result_digest: str
    completed_at: datetime
    live_write_performed: bool = False

    def __post_init__(self) -> None:
        require_text(self.adapter_identifier, "adapter_identifier")
        require_digest(self.plan_digest, "plan_digest")
        require_digest(self.result_digest, "result_digest")
        require_utc(self.completed_at, "completed_at")
        if self.live_write_performed:
            raise ValueError("controlled fake result cannot claim a live write")


class CommerceProductWritePort(Protocol):
    def apply(self, plan: ControlledWritePlan, *, completed_at: datetime) -> CommerceWriteResult: ...

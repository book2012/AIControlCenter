"""Pure deny-only DPL-04A executor-port composition."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any

from core.deployment.executor_contracts import create_executor_result


class DenyOnlyNonProductionExecutor:
    """A non-adapter that deterministically denies and never executes."""

    def __init__(self, capability: Mapping[str, Any]) -> None:
        self._capability = copy.deepcopy(dict(capability))

    def execute(
        self, request: Mapping[str, Any], *, result_timestamp: str
    ) -> Mapping[str, Any]:
        return create_executor_result(
            request=copy.deepcopy(dict(request)),
            capability=self._capability,
            status="DENIED",
            reason_codes=("DEFAULT_DENY_NO_EXECUTOR",),
            result_timestamp=result_timestamp,
        )

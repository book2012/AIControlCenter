from __future__ import annotations

from collections.abc import Mapping

from core.shopping.contracts.provisional import (
    PolicyDecision,
    ReadPolicyRequest,
)
from core.shopping.governance.capabilities import (
    DEFAULT_CAPABILITY_REGISTRY,
    RESERVED_WRITE_CAPABILITY_IDS,
    CapabilityRegistry,
    OperationClass,
)
from core.shopping.ports.policy import (
    PolicyDecisionPort,
)


class ReadAuthorizationDenied(
    PermissionError
):
    def __init__(
        self,
        *,
        code: str,
        capability_id: str,
    ) -> None:
        self.code = code
        self.capability_id = (
            capability_id
        )

        super().__init__(
            code
        )


def _deny(
    *,
    code: str,
    capability_id: str,
) -> None:
    raise ReadAuthorizationDenied(
        code=code,
        capability_id=capability_id,
    )


async def authorize_read(
    *,
    capability_id: str,
    request: ReadPolicyRequest,
    policy: PolicyDecisionPort,
    registry: CapabilityRegistry = (
        DEFAULT_CAPABILITY_REGISTRY
    ),
) -> PolicyDecision:
    if (
        capability_id
        in RESERVED_WRITE_CAPABILITY_IDS
    ):
        _deny(
            code=(
                "shopping.capability.write_denied"
            ),
            capability_id=capability_id,
        )

    definition = registry.get(
        capability_id
    )

    if definition is None:
        _deny(
            code=(
                "shopping.capability.unknown"
            ),
            capability_id=capability_id,
        )

    if (
        definition.operation_class
        is not OperationClass.READ
    ):
        _deny(
            code=(
                "shopping.capability.not_read"
            ),
            capability_id=capability_id,
        )

    if not isinstance(
        request,
        Mapping,
    ):
        _deny(
            code=(
                "shopping.policy.invalid_request"
            ),
            capability_id=capability_id,
        )

    request_capability = (
        request.get(
            "capability"
        )
    )

    if (
        request_capability
        != capability_id
    ):
        _deny(
            code=(
                "shopping.policy.request_capability_mismatch"
            ),
            capability_id=capability_id,
        )

    try:
        decision = await (
            policy.evaluate_read(
                request=request
            )
        )
    except Exception:
        _deny(
            code=(
                "shopping.policy.evaluation_error"
            ),
            capability_id=capability_id,
        )

    if not isinstance(
        decision,
        Mapping,
    ):
        _deny(
            code=(
                "shopping.policy.invalid_decision"
            ),
            capability_id=capability_id,
        )

    decision_capability = (
        decision.get(
            "capability"
        )
    )

    allowed = decision.get(
        "allowed"
    )

    if (
        decision_capability
        != capability_id
    ):
        _deny(
            code=(
                "shopping.policy.decision_capability_mismatch"
            ),
            capability_id=capability_id,
        )

    if not isinstance(
        allowed,
        bool,
    ):
        _deny(
            code=(
                "shopping.policy.invalid_decision"
            ),
            capability_id=capability_id,
        )

    if allowed is not True:
        _deny(
            code=(
                "shopping.policy.denied"
            ),
            capability_id=capability_id,
        )

    return decision


__all__ = (
    "ReadAuthorizationDenied",
    "authorize_read",
)

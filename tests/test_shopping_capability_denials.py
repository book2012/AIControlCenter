from __future__ import annotations

import asyncio

import pytest

from core.shopping.application.read_authorization import (
    ReadAuthorizationDenied,
    authorize_read,
)
from core.shopping.governance.capabilities import (
    READ_CAPABILITY_IDS,
    RESERVED_WRITE_CAPABILITY_IDS,
)


CAPABILITY = "shopping.product.get"


def _request(
    capability: str = CAPABILITY,
):
    return {
        "action": "read",
        "capability": capability,
        "context": {},
        "requested_fields": [],
        "resource_id": "resource-1",
        "resource_type": "product",
    }


class Policy:
    def __init__(
        self,
        *,
        decision=None,
        error=None,
    ):
        self.decision = decision
        self.error = error
        self.calls = 0

    async def evaluate_read(
        self,
        *,
        request,
    ):
        self.calls += 1

        if self.error is not None:
            raise self.error

        return self.decision


def _run(
    *,
    capability_id,
    request,
    policy,
):
    return asyncio.run(
        authorize_read(
            capability_id=capability_id,
            request=request,
            policy=policy,
        )
    )


def test_policy_exception_fails_closed_without_message_leak():
    secret = "vendor-secret-message"

    policy = Policy(
        error=RuntimeError(
            secret
        )
    )

    with pytest.raises(
        ReadAuthorizationDenied
    ) as error_info:
        _run(
            capability_id=CAPABILITY,
            request=_request(),
            policy=policy,
        )

    assert (
        error_info.value.code
        == "shopping.policy.evaluation_error"
    )

    assert secret not in str(
        error_info.value
    )

    assert policy.calls == 1


def test_non_mapping_request_denies_before_policy():
    policy = Policy(
        decision={
            "allowed": True,
            "capability": CAPABILITY,
        }
    )

    with pytest.raises(
        ReadAuthorizationDenied
    ) as error_info:
        _run(
            capability_id=CAPABILITY,
            request=None,
            policy=policy,
        )

    assert (
        error_info.value.code
        == "shopping.policy.invalid_request"
    )

    assert policy.calls == 0


def test_missing_request_capability_denies_before_policy():
    policy = Policy(
        decision={
            "allowed": True,
            "capability": CAPABILITY,
        }
    )

    with pytest.raises(
        ReadAuthorizationDenied
    ) as error_info:
        _run(
            capability_id=CAPABILITY,
            request={},
            policy=policy,
        )

    assert (
        error_info.value.code
        == (
            "shopping.policy."
            "request_capability_mismatch"
        )
    )

    assert policy.calls == 0


def test_non_boolean_allowed_is_invalid_decision():
    policy = Policy(
        decision={
            "allowed": 1,
            "capability": CAPABILITY,
        }
    )

    with pytest.raises(
        ReadAuthorizationDenied
    ) as error_info:
        _run(
            capability_id=CAPABILITY,
            request=_request(),
            policy=policy,
        )

    assert (
        error_info.value.code
        == "shopping.policy.invalid_decision"
    )

    assert policy.calls == 1


def test_all_reserved_write_capabilities_deny_before_policy():
    assert len(
        RESERVED_WRITE_CAPABILITY_IDS
    ) == 9

    for capability_id in (
        RESERVED_WRITE_CAPABILITY_IDS
    ):
        policy = Policy(
            decision={
                "allowed": True,
                "capability": capability_id,
            }
        )

        with pytest.raises(
            ReadAuthorizationDenied
        ) as error_info:
            _run(
                capability_id=capability_id,
                request=_request(
                    capability_id
                ),
                policy=policy,
            )

        assert (
            error_info.value.code
            == "shopping.capability.write_denied"
        )

        assert policy.calls == 0


def test_all_registered_read_capabilities_reach_policy_once():
    assert len(
        READ_CAPABILITY_IDS
    ) == 11

    for capability_id in (
        READ_CAPABILITY_IDS
    ):
        decision = {
            "allowed": True,
            "capability": capability_id,
        }

        policy = Policy(
            decision=decision
        )

        result = _run(
            capability_id=capability_id,
            request=_request(
                capability_id
            ),
            policy=policy,
        )

        assert result is decision
        assert policy.calls == 1

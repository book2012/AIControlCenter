from __future__ import annotations

import asyncio

import pytest

from core.shopping.application.read_authorization import (
    ReadAuthorizationDenied,
    authorize_read,
)
from core.shopping.governance.capabilities import (
    CapabilityDefinition,
    CapabilityRegistry,
    OperationClass,
)


CAPABILITY = (
    "shopping.product.get"
)


def _request(
    capability: str = CAPABILITY,
):
    return {
        "action": "read",
        "capability": capability,
        "context": {
            "actor_id": "admin-1",
            "correlation_id": (
                "correlation-1"
            ),
            "locale": "ko-KR",
            "requested_at": (
                "2026-07-23T00:00:00Z"
            ),
            "source": "test",
        },
        "requested_fields": [
            "name",
            "price",
        ],
        "resource_id": "product-1",
        "resource_type": "product",
    }


def _decision(
    *,
    capability: str = CAPABILITY,
    allowed: bool = True,
):
    return {
        "allowed": allowed,
        "capability": capability,
        "correlation_id": (
            "correlation-1"
        ),
        "decision_id": "decision-1",
        "evaluated_at": (
            "2026-07-23T00:00:00Z"
        ),
        "reason_code": (
            "shopping.policy.allowed"
            if allowed
            else "shopping.policy.denied"
        ),
        "reason_message": None,
    }


class FakePolicy:
    def __init__(
        self,
        decision,
    ):
        self.decision = decision
        self.calls = 0
        self.requests = []

    async def evaluate_read(
        self,
        *,
        request,
    ):
        self.calls += 1
        self.requests.append(
            request
        )

        return self.decision


def _run(
    *,
    capability_id,
    request,
    policy,
    registry=None,
):
    kwargs = {
        "capability_id": (
            capability_id
        ),
        "request": request,
        "policy": policy,
    }

    if registry is not None:
        kwargs[
            "registry"
        ] = registry

    return asyncio.run(
        authorize_read(
            **kwargs
        )
    )


def test_known_read_policy_allow_returns_decision():
    decision = _decision()

    policy = FakePolicy(
        decision
    )

    result = _run(
        capability_id=CAPABILITY,
        request=_request(),
        policy=policy,
    )

    assert result is decision
    assert policy.calls == 1
    assert policy.requests == [
        _request()
    ]


def test_unknown_capability_denies_before_policy():
    policy = FakePolicy(
        _decision()
    )

    with pytest.raises(
        ReadAuthorizationDenied
    ) as error_info:
        _run(
            capability_id=(
                "shopping.unknown.operation"
            ),
            request=_request(
                "shopping.unknown.operation"
            ),
            policy=policy,
        )

    assert (
        error_info.value.code
        == "shopping.capability.unknown"
    )

    assert policy.calls == 0


def test_reserved_write_denies_before_policy():
    capability = (
        "shopping.product.update"
    )

    policy = FakePolicy(
        _decision(
            capability=capability
        )
    )

    with pytest.raises(
        ReadAuthorizationDenied
    ) as error_info:
        _run(
            capability_id=capability,
            request=_request(
                capability
            ),
            policy=policy,
        )

    assert (
        error_info.value.code
        == "shopping.capability.write_denied"
    )

    assert policy.calls == 0


def test_non_read_registry_entry_denies_before_policy():
    capability = (
        "shopping.test.execute"
    )

    registry = CapabilityRegistry(
        (
            CapabilityDefinition(
                capability_id=capability,
                operation_class=(
                    OperationClass.WRITE
                ),
                resource_type="test",
                port="TestPort",
                method="execute",
            ),
        )
    )

    policy = FakePolicy(
        _decision(
            capability=capability
        )
    )

    with pytest.raises(
        ReadAuthorizationDenied
    ) as error_info:
        _run(
            capability_id=capability,
            request=_request(
                capability
            ),
            policy=policy,
            registry=registry,
        )

    assert (
        error_info.value.code
        == "shopping.capability.not_read"
    )

    assert policy.calls == 0


def test_request_capability_mismatch_denies_before_policy():
    policy = FakePolicy(
        _decision()
    )

    with pytest.raises(
        ReadAuthorizationDenied
    ) as error_info:
        _run(
            capability_id=CAPABILITY,
            request=_request(
                "shopping.product.list"
            ),
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


def test_policy_denial_is_denied():
    policy = FakePolicy(
        _decision(
            allowed=False
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
        == "shopping.policy.denied"
    )

    assert policy.calls == 1


def test_policy_capability_mismatch_is_denied():
    policy = FakePolicy(
        _decision(
            capability=(
                "shopping.product.list"
            )
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
        == (
            "shopping.policy."
            "decision_capability_mismatch"
        )
    )

    assert policy.calls == 1


def test_malformed_policy_decision_is_denied():
    malformed_decisions = (
        None,
        [],
        {
            "capability": CAPABILITY,
        },
        {
            "allowed": "yes",
            "capability": CAPABILITY,
        },
    )

    for decision in malformed_decisions:
        policy = FakePolicy(
            decision
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

from core.datacenter.on_demand import (
    DatacenterPowerState,
    OnDemandContext,
    OnDemandStateService,
)


def test_offline_is_expected_when_server_is_not_required() -> None:
    result = OnDemandStateService().evaluate(
        {"status": "OFFLINE"},
        OnDemandContext(expected_online=False),
    )

    assert result["state"] == (
        DatacenterPowerState.OFFLINE_EXPECTED.value
    )
    assert result["requires_attention"] is False
    assert result["is_available"] is False


def test_offline_is_unexpected_during_required_window() -> None:
    result = OnDemandStateService().evaluate(
        {"status": "OFFLINE"},
        OnDemandContext(expected_online=True),
    )

    assert result["state"] == (
        DatacenterPowerState.OFFLINE_UNEXPECTED.value
    )
    assert result["requires_attention"] is True


def test_ready_worker_is_ready() -> None:
    result = OnDemandStateService().evaluate(
        {"status": "READY"},
        OnDemandContext(expected_online=True),
    )

    assert result["state"] == DatacenterPowerState.READY.value
    assert result["is_available"] is True


def test_online_worker_with_tasks_is_busy() -> None:
    result = OnDemandStateService().evaluate(
        {"status": "ONLINE"},
        OnDemandContext(
            expected_online=True,
            running_tasks=2,
        ),
    )

    assert result["state"] == DatacenterPowerState.BUSY.value
    assert result["running_tasks"] == 2


def test_waking_overrides_offline_worker_status() -> None:
    result = OnDemandStateService().evaluate(
        {"status": "OFFLINE"},
        OnDemandContext(
            expected_online=True,
            waking=True,
        ),
    )

    assert result["state"] == DatacenterPowerState.WAKING.value
    assert result["requires_attention"] is False


def test_shutdown_transition_has_priority() -> None:
    result = OnDemandStateService().evaluate(
        {"status": "ONLINE"},
        OnDemandContext(
            expected_online=False,
            shutting_down=True,
        ),
    )

    assert result["state"] == (
        DatacenterPowerState.SHUTTING_DOWN.value
    )


def test_unknown_worker_status_requires_attention() -> None:
    result = OnDemandStateService().evaluate(
        {"status": "SOMETHING_NEW"},
    )

    assert result["state"] == DatacenterPowerState.UNKNOWN.value
    assert result["requires_attention"] is True

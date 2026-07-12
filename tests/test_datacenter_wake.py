from unittest.mock import MagicMock, patch

import pytest

from core.power.wake import (
    DatacenterWakeService,
    WakeConfig,
    WakeOnLanSender,
)


class ReadyWorker:
    def ready(self):
        return {
            "ready": True,
            "status": "READY",
        }


class DelayedWorker:
    def __init__(self):
        self.calls = 0

    def ready(self):
        self.calls += 1

        if self.calls < 3:
            raise ConnectionError("worker not available")

        return {
            "ready": True,
            "status": "READY",
        }


def test_magic_packet_is_sent() -> None:
    sender = WakeOnLanSender()
    config = WakeConfig(
        mac_address="AA:BB:CC:DD:EE:FF",
        broadcast_address="192.168.1.255",
    )

    fake_socket = MagicMock()
    fake_socket.__enter__.return_value = fake_socket
    fake_socket.sendto.return_value = 102

    with patch(
        "core.power.wake.socket.socket",
        return_value=fake_socket,
    ):
        result = sender.send(config)

    assert result["sent"] is True
    assert result["bytes_sent"] == 102

    packet, target = fake_socket.sendto.call_args.args

    assert len(packet) == 102
    assert packet[:6] == bytes.fromhex("FF" * 6)
    assert target == ("192.168.1.255", 9)


@pytest.mark.parametrize(
    "mac_address",
    [
        "",
        "invalid",
        "AA:BB:CC:DD:EE",
        "ZZ:BB:CC:DD:EE:FF",
    ],
)
def test_invalid_mac_address_is_rejected(mac_address: str) -> None:
    with pytest.raises(ValueError):
        WakeOnLanSender().send(
            WakeConfig(mac_address=mac_address)
        )


def test_wait_until_ready_returns_success() -> None:
    service = DatacenterWakeService(ReadyWorker())

    result = service.wait_until_ready(
        timeout_seconds=1,
        poll_interval_seconds=0,
    )

    assert result["ready"] is True
    assert result["attempts"] == 1


def test_wait_until_ready_retries() -> None:
    service = DatacenterWakeService(DelayedWorker())

    result = service.wait_until_ready(
        timeout_seconds=1,
        poll_interval_seconds=0,
    )

    assert result["ready"] is True
    assert result["attempts"] == 3


def test_wake_and_wait_combines_results() -> None:
    sender = MagicMock()
    sender.send.return_value = {
        "sent": True,
        "bytes_sent": 102,
    }

    service = DatacenterWakeService(
        ReadyWorker(),
        sender=sender,
    )

    result = service.wake_and_wait(
        WakeConfig(
            mac_address="AA:BB:CC:DD:EE:FF",
            timeout_seconds=1,
            poll_interval_seconds=0,
        )
    )

    assert result["wake"]["sent"] is True
    assert result["readiness"]["ready"] is True
    assert result["completed"] is True

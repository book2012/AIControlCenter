from __future__ import annotations

import socket
import time
from dataclasses import dataclass
from typing import Any

from core.worker.worker_client import WorkerClient


@dataclass(frozen=True)
class WakeConfig:
    mac_address: str
    broadcast_address: str = "255.255.255.255"
    port: int = 9
    timeout_seconds: float = 180.0
    poll_interval_seconds: float = 5.0


class WakeOnLanSender:
    @staticmethod
    def _normalize_mac(mac_address: str) -> str:
        normalized = (
            mac_address
            .replace(":", "")
            .replace("-", "")
            .replace(".", "")
            .strip()
        )

        if len(normalized) != 12:
            raise ValueError("MAC address must contain 12 hexadecimal digits")

        try:
            int(normalized, 16)
        except ValueError as error:
            raise ValueError("MAC address contains invalid characters") from error

        return normalized.upper()

    def send(self, config: WakeConfig) -> dict[str, Any]:
        normalized = self._normalize_mac(config.mac_address)
        mac_bytes = bytes.fromhex(normalized)
        packet = bytes.fromhex("FF" * 6) + mac_bytes * 16

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sent = sock.sendto(
                packet,
                (config.broadcast_address, config.port),
            )

        return {
            "sent": sent == len(packet),
            "bytes_sent": sent,
            "broadcast_address": config.broadcast_address,
            "port": config.port,
        }


class DatacenterWakeService:
    READY_STATUSES = {
        "READY",
        "ONLINE",
        "WARNING",
        "RECOVERY",
    }

    def __init__(
        self,
        worker: WorkerClient,
        sender: WakeOnLanSender | None = None,
    ):
        self.worker = worker
        self.sender = sender or WakeOnLanSender()

    def wake(self, config: WakeConfig) -> dict[str, Any]:
        return self.sender.send(config)

    def wait_until_ready(
        self,
        *,
        timeout_seconds: float = 180.0,
        poll_interval_seconds: float = 5.0,
    ) -> dict[str, Any]:
        started = time.monotonic()
        attempts = 0
        last_result: dict[str, Any] | None = None
        last_error: dict[str, str] | None = None

        while time.monotonic() - started < timeout_seconds:
            attempts += 1

            try:
                result = self.worker.ready()
                last_result = result

                status = str(
                    result.get(
                        "status",
                        "READY" if result.get("ready") is True else "UNKNOWN",
                    )
                ).upper()

                if result.get("ready") is True or status in self.READY_STATUSES:
                    return {
                        "ready": True,
                        "attempts": attempts,
                        "elapsed_seconds": round(
                            time.monotonic() - started,
                            3,
                        ),
                        "worker": result,
                    }

            except Exception as error:
                last_error = {
                    "type": type(error).__name__,
                    "message": str(error),
                }

            time.sleep(poll_interval_seconds)

        return {
            "ready": False,
            "attempts": attempts,
            "elapsed_seconds": round(
                time.monotonic() - started,
                3,
            ),
            "worker": last_result,
            "last_error": last_error,
            "timed_out": True,
        }

    def wake_and_wait(self, config: WakeConfig) -> dict[str, Any]:
        wake_result = self.wake(config)

        readiness = self.wait_until_ready(
            timeout_seconds=config.timeout_seconds,
            poll_interval_seconds=config.poll_interval_seconds,
        )

        return {
            "wake": wake_result,
            "readiness": readiness,
            "completed": readiness["ready"],
        }

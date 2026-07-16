from __future__ import annotations

import os

class ControlPlaneStatus:
    def __init__(
        self,
        service: str | None = None,
        mode: str | None = None,
        listener: str | None = None,
        read_only: bool = True,
    ) -> None:
        self.service = service or os.getenv(
            "AICONTROLCENTER_SERVICE_NAME",
            "AIControlCenter",
        )
        self.mode = mode or os.getenv(
            "AICONTROLCENTER_RUNTIME_MODE",
            "shadow",
        )
        self.listener = listener or os.getenv(
            "AICONTROLCENTER_LISTENER",
            "127.0.0.1:18100",
        )
        self.read_only = read_only

    def status(self) -> dict:
        return {
            "service": self.service,
            "mode": self.mode,
            "read_only": self.read_only,
            "health": "ONLINE",
            "listener": self.listener,
        }

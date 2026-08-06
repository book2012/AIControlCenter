from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Protocol


@dataclass(frozen=True, slots=True)
class CommandRequest:
    argv: tuple[str, ...]
    timeout_seconds: float = 3.0
    max_output_bytes: int = 262_144
    cwd: str | None = None
    env: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        argv = tuple(self.argv)

        if not argv:
            raise ValueError("Command argv is empty")

        if not Path(argv[0]).is_absolute():
            raise ValueError(
                "Command executable must be absolute"
            )

        for argument in argv:
            if (
                not isinstance(argument, str)
                or not argument
                or "\x00" in argument
                or "\n" in argument
                or "\r" in argument
            ):
                raise ValueError(
                    "Invalid command argument"
                )

        if not 0.05 <= self.timeout_seconds <= 30:
            raise ValueError(
                "Command timeout is outside bounds"
            )

        if not 1 <= self.max_output_bytes <= 1_048_576:
            raise ValueError(
                "Command output bound is invalid"
            )

        if (
            self.cwd is not None
            and not Path(self.cwd).is_absolute()
        ):
            raise ValueError(
                "Command cwd must be absolute"
            )

        supplied_env = dict(self.env or {})

        for key, value in supplied_env.items():
            if (
                not key
                or not isinstance(value, str)
                or "\x00" in key
                or "\x00" in value
            ):
                raise ValueError(
                    "Invalid command environment"
                )

            if key.upper() == "PYTHONPATH":
                raise ValueError(
                    "PYTHONPATH is prohibited"
                )

        object.__setattr__(self, "argv", argv)
        object.__setattr__(
            self,
            "env",
            MappingProxyType(supplied_env),
        )


@dataclass(frozen=True, slots=True)
class CommandResult:
    returncode: int
    stdout: bytes
    stderr: bytes
    timed_out: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.returncode, int):
            raise TypeError(
                "returncode must be an integer"
            )

        if not isinstance(self.stdout, bytes):
            raise TypeError("stdout must be bytes")

        if not isinstance(self.stderr, bytes):
            raise TypeError("stderr must be bytes")


class CommandExecutor(Protocol):
    def run(
        self,
        request: CommandRequest,
    ) -> CommandResult:
        ...


@dataclass(frozen=True, slots=True)
class HttpProbeRequest:
    probe_id: str
    host: str
    port: int
    method: str
    path: str
    expected_status: int
    timeout_seconds: float = 3.0
    max_body_bytes: int = 65_536
    body: bytes = b""
    attempt_count: int = 1
    automatic_retries: int = 0
    follow_redirects: bool = False

    def __post_init__(self) -> None:
        if not self.probe_id:
            raise ValueError(
                "HTTP probe_id is required"
            )

        if self.host != "127.0.0.1":
            raise ValueError(
                "HTTP host must be exact loopback"
            )

        if not 1 <= self.port <= 65_535:
            raise ValueError(
                "HTTP port is invalid"
            )

        if self.method not in {"GET", "POST"}:
            raise ValueError(
                "HTTP method is prohibited"
            )

        if (
            not self.path.startswith("/")
            or self.path.startswith("//")
            or "\r" in self.path
            or "\n" in self.path
        ):
            raise ValueError(
                "HTTP path is invalid"
            )

        if self.method == "POST" and self.path != "/health":
            raise ValueError(
                "POST is restricted to /health"
            )

        if not 100 <= self.expected_status <= 599:
            raise ValueError(
                "Expected HTTP status is invalid"
            )

        if not 0.05 <= self.timeout_seconds <= 10:
            raise ValueError(
                "HTTP timeout is outside bounds"
            )

        if not 1 <= self.max_body_bytes <= 262_144:
            raise ValueError(
                "HTTP body bound is invalid"
            )

        if self.body != b"":
            raise ValueError(
                "HTTP probe body must be empty"
            )

        if self.attempt_count != 1:
            raise ValueError(
                "HTTP attempt count must be one"
            )

        if self.automatic_retries != 0:
            raise ValueError(
                "HTTP retries are prohibited"
            )

        if self.follow_redirects is not False:
            raise ValueError(
                "HTTP redirects are prohibited"
            )


@dataclass(frozen=True, slots=True)
class HttpProbeResponse:
    status: int
    body: bytes

    def __post_init__(self) -> None:
        if not 100 <= self.status <= 599:
            raise ValueError(
                "HTTP response status is invalid"
            )

        if not isinstance(self.body, bytes):
            raise TypeError(
                "HTTP response body must be bytes"
            )


class HttpTransport(Protocol):
    def probe(
        self,
        request: HttpProbeRequest,
    ) -> HttpProbeResponse:
        ...


__all__ = (
    "CommandExecutor",
    "CommandRequest",
    "CommandResult",
    "HttpProbeRequest",
    "HttpProbeResponse",
    "HttpTransport",
)

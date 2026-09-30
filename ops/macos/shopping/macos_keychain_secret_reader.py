from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess

from core.secrets.ports import (
    SecretReference,
    SecretResolutionError,
)


TWILIO_SECRET_BACKEND = "macos.keychain"


@dataclass(frozen=True, slots=True)
class MacOSKeychainGenericPasswordReader:
    account: str
    allowed_services: frozenset[str]
    keychain_path: Path

    def __post_init__(self) -> None:
        if (
            type(self.account) is not str
            or not self.account
        ):
            raise ValueError(
                "invalid keychain account"
            )

        if (
            not self.allowed_services
            or any(
                type(value) is not str
                or not value
                for value in self.allowed_services
            )
        ):
            raise ValueError(
                "invalid keychain allowlist"
            )

    def __call__(
        self,
        reference: SecretReference,
    ) -> bytes:
        data = reference.to_dict()

        if (
            data.get("backend")
            != TWILIO_SECRET_BACKEND
        ):
            raise SecretResolutionError()

        matching_services = [
            value
            for key, value in data.items()
            if (
                key != "backend"
                and type(value) is str
                and value
                in self.allowed_services
            )
        ]

        if len(matching_services) != 1:
            raise SecretResolutionError()

        service = matching_services[0]

        result = subprocess.run(
            [
                "/usr/bin/security",
                "find-generic-password",
                "-a",
                self.account,
                "-s",
                service,
                "-w",
                str(self.keychain_path),
            ],
            capture_output=True,
            check=False,
        )

        if result.returncode != 0:
            raise SecretResolutionError()

        value = result.stdout.rstrip(
            b"\r\n"
        )

        if not value or len(value) > 4096:
            raise SecretResolutionError()

        return value

    def __repr__(self) -> str:
        return (
            "MacOSKeychainGenericPasswordReader("
            f"account={self.account!r},"
            "allowed_services=<redacted>,"
            f"keychain_path={str(self.keychain_path)!r})"
        )

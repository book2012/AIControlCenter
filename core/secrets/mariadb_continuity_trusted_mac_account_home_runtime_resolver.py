"""Darwin runtime resolver for the trusted Mac account home."""

from dataclasses import dataclass
import os
import platform
import pwd
from typing import NamedTuple


class TrustedMacAccountHomeResolutionError(RuntimeError):
    """The trusted account home could not be resolved under the frozen policy."""


class RuntimeAccountIdentityObservation(NamedTuple):
    """The paired real/effective UID observation before identity binding."""

    real_uid: int
    effective_uid: int


@dataclass(frozen=True, slots=True, init=False)
class ResolvedTrustedMacAccountHome:
    """Zero-authority result containing only the bound UID and passwd home."""

    bound_uid: int
    passwd_home: str

    def __new__(cls):
        raise TypeError(
            "ResolvedTrustedMacAccountHome is constructed only by the runtime resolver"
        )


class RuntimeHomeResolver:
    """Closed resolver whose observation sources are fixed by architecture."""

    __slots__ = ()

    def resolve_once(self) -> ResolvedTrustedMacAccountHome:
        try:
            observed_platform = platform.system()
        except Exception as exc:
            raise TrustedMacAccountHomeResolutionError(
                "platform observation failed"
            ) from exc
        if observed_platform != "Darwin":
            raise TrustedMacAccountHomeResolutionError("Darwin is required")

        try:
            real_uid = os.getuid()
        except Exception as exc:
            raise TrustedMacAccountHomeResolutionError(
                "real UID observation failed"
            ) from exc
        try:
            effective_uid = os.geteuid()
        except Exception as exc:
            raise TrustedMacAccountHomeResolutionError(
                "effective UID observation failed"
            ) from exc

        observation = RuntimeAccountIdentityObservation(real_uid, effective_uid)
        if observation.real_uid == 0 or observation.effective_uid == 0:
            raise TrustedMacAccountHomeResolutionError("root UID is prohibited")
        if observation.real_uid != observation.effective_uid:
            raise TrustedMacAccountHomeResolutionError(
                "real and effective UIDs must match"
            )
        bound_uid = observation.real_uid

        try:
            passwd_result = pwd.getpwuid(bound_uid)
        except Exception as exc:
            raise TrustedMacAccountHomeResolutionError("passwd lookup failed") from exc
        try:
            passwd_home = passwd_result.pw_dir
        except (AttributeError, IndexError, TypeError) as exc:
            raise TrustedMacAccountHomeResolutionError(
                "passwd result does not supply pw_dir"
            ) from exc
        if type(passwd_home) is not str:
            raise TrustedMacAccountHomeResolutionError("pw_dir must be a string")
        if not passwd_home:
            raise TrustedMacAccountHomeResolutionError("pw_dir must be non-empty")
        if "\0" in passwd_home:
            raise TrustedMacAccountHomeResolutionError("pw_dir must not contain NUL")
        if not passwd_home.startswith("/"):
            raise TrustedMacAccountHomeResolutionError(
                "pw_dir must be a lexically absolute POSIX path"
            )
        resolved_home = object.__new__(ResolvedTrustedMacAccountHome)
        object.__setattr__(resolved_home, "bound_uid", bound_uid)
        object.__setattr__(resolved_home, "passwd_home", passwd_home)
        return resolved_home


def resolve_trusted_mac_account_home() -> ResolvedTrustedMacAccountHome:
    """Resolve once from the fixed platform, UID, and passwd sources."""

    return RuntimeHomeResolver().resolve_once()

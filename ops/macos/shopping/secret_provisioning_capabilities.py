"""Six fixed, bounded macOS shopping secret provisioning capabilities."""

from __future__ import annotations

import filecmp
import os
import stat
import subprocess
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO

from ops.macos.shopping.secret_provisioning_adapters import MutationOutcome
from ops.macos.shopping.secret_provisioning_observations import (
    executable_present,
    observe_file,
    structurally_safe_identity,
)

BREW = Path("/opt/homebrew/bin/brew")
SOPS = Path("/opt/homebrew/bin/sops")
AGE = Path("/opt/homebrew/bin/age")
AGE_KEYGEN = Path("/opt/homebrew/bin/age-keygen")
_ENV = {"PATH": "/opt/homebrew/bin:/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"}
_TIMEOUT_SECONDS = 120
_MAX_RECIPIENT_BYTES = 1024
_AGE_RECIPIENT_HRP = "age"
_BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
_INTAKE_RELATIVE_PATH = Path(
    ".config/aicontrolcenter/shopping-secrets/inbox/offline-recovery.txt"
)
_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]

ProcessRunner = Callable[..., Any]
ExecutableObserver = Callable[[Path], bool]


@dataclass
class _MutationState:
    occurred: bool = False

    def outcome_after_error(self) -> MutationOutcome:
        return MutationOutcome.UNCERTAIN if self.occurred else MutationOutcome.FAILED


@dataclass(frozen=True, slots=True, repr=False)
class OfflineRecoveryPublicRecipient:
    """One already-public age recipient; string representations stay value-free."""

    _encoded: bytes

    def __init__(self, recipient: str) -> None:
        if not isinstance(recipient, str) or not _valid_age_recipient_text(recipient):
            raise ValueError("INVALID_OFFLINE_RECOVERY_PUBLIC_RECIPIENT")
        object.__setattr__(self, "_encoded", recipient.encode("ascii"))

    def __repr__(self) -> str:
        return "OfflineRecoveryPublicRecipient(REDACTED)"

    def __str__(self) -> str:
        return "OFFLINE_RECOVERY_PUBLIC_RECIPIENT"


def _bech32_polymod(values: Sequence[int]) -> int:
    result = 1
    generators = (0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3)
    for value in values:
        top = result >> 25
        result = ((result & 0x1FFFFFF) << 5) ^ value
        for index, generator in enumerate(generators):
            if (top >> index) & 1:
                result ^= generator
    return result


def _valid_age_recipient_text(value: str) -> bool:
    if len(value) != 62 or not value.startswith("age1") or not value.isascii():
        return False
    data = value[4:]
    if any(character not in _BECH32_CHARSET for character in data):
        return False
    # 32 public-key bytes become 52 data symbols; the final four bits are padding.
    if _BECH32_CHARSET.index(data[-7]) & 0x0F:
        return False
    expanded = [ord(character) >> 5 for character in _AGE_RECIPIENT_HRP]
    expanded += [0]
    expanded += [ord(character) & 31 for character in _AGE_RECIPIENT_HRP]
    return _bech32_polymod(expanded + [_BECH32_CHARSET.index(c) for c in data]) == 1


def _default_runner(argv: Sequence[str], **kwargs: Any) -> Any:
    return subprocess.run(argv, **kwargs)


def _uid(expected_uid: int) -> int:
    if not isinstance(expected_uid, int) or isinstance(expected_uid, bool) or expected_uid < 0:
        raise ValueError("INVALID_EXPECTED_UID")
    return expected_uid


def _safe_directory(path: Path, expected_uid: int) -> bool:
    try:
        metadata = path.lstat()
    except OSError:
        return False
    return (stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
            and metadata.st_uid == expected_uid
            and stat.S_IMODE(metadata.st_mode) & ~0o700 == 0)


def _open_trusted_intake_parent(home: Path, relative: Path, uid: int, gid: int) -> int:
    """Anchor home and traverse the fixed parent chain without pathname races."""
    home_path_metadata = home.lstat()
    directory_flags = (os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
                       | getattr(os, "O_NOFOLLOW", 0))
    descriptor = os.open(home, directory_flags)
    try:
        home_metadata = os.fstat(descriptor)
        if (not stat.S_ISDIR(home_metadata.st_mode)
                or home_metadata.st_uid != uid
                or home_metadata.st_dev != home_path_metadata.st_dev
                or home_metadata.st_ino != home_path_metadata.st_ino):
            raise RuntimeError("UNSAFE_CONTROL_PLANE_HOME")
        for component in relative.parent.parts:
            child = os.open(component, directory_flags, dir_fd=descriptor)
            try:
                metadata = os.fstat(child)
                if (not stat.S_ISDIR(metadata.st_mode)
                        or metadata.st_uid != uid or metadata.st_gid != gid
                        or stat.S_IMODE(metadata.st_mode) & ~0o700):
                    raise RuntimeError("UNSAFE_PARENT")
            except Exception:
                os.close(child)
                raise
            os.close(descriptor)
            descriptor = child
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def _safe_intake_leaf_metadata(metadata: os.stat_result, *, uid: int, gid: int,
                               expected_size: int) -> bool:
    """Validate value-free metadata for the one fixed intake artifact."""
    return (stat.S_ISREG(metadata.st_mode)
            and metadata.st_uid == uid and metadata.st_gid == gid
            and stat.S_IMODE(metadata.st_mode) & ~0o600 == 0
            and metadata.st_size == expected_size)


def _trusted_age_prevalidation(recipient: OfflineRecoveryPublicRecipient,
                               runner: ProcessRunner,
                               executable: ExecutableObserver) -> bool:
    """Validate one typed public recipient with the fixed age executable only."""
    if not executable(AGE):
        return False
    try:
        result = runner(
            (str(AGE), "--encrypt", "--recipient", recipient._encoded.decode("ascii")),
            shell=False, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, timeout=_TIMEOUT_SECONDS,
            env=dict(_ENV), check=False,
        )
    except Exception:
        return False
    return getattr(result, "returncode", None) == 0


def _outside_repository(path: Path) -> bool:
    try:
        path.relative_to(_REPOSITORY_ROOT)
    except ValueError:
        return True
    return False


def _validate_home(home: Path, expected_uid: int) -> None:
    try:
        metadata = home.lstat()
    except OSError as error:
        raise ValueError("UNSAFE_CONTROL_PLANE_HOME") from error
    if (not home.is_absolute() or not stat.S_ISDIR(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode) or metadata.st_uid != expected_uid):
        raise ValueError("UNSAFE_CONTROL_PLANE_HOME")


def _relative(metadata: Mapping[str, Any], key: str) -> Path:
    entry = metadata[key]
    if not isinstance(entry, Mapping) or entry.get("base") != "control-plane-home":
        raise ValueError("INVALID_PORTABLE_PATH_METADATA")
    value = entry.get("relative_path")
    if not isinstance(value, str) or not value:
        raise ValueError("INVALID_PORTABLE_PATH_METADATA")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts or any(part in ("", ".") for part in relative.parts):
        raise ValueError("INVALID_PORTABLE_PATH_METADATA")
    return relative


def _prepare_parent(home: Path, relative_parent: Path, expected_uid: int,
                    mutation: _MutationState) -> None:
    """Validate/create each component while recording mutation before fallible work."""
    current = home
    for component in relative_parent.parts:
        current = current / component
        try:
            current.mkdir(mode=0o700)
            mutation.occurred = True
            os.chmod(current, 0o700, follow_symlinks=False)
        except FileExistsError:
            pass
        if not _safe_directory(current, expected_uid):
            raise RuntimeError("UNSAFE_PARENT")


def _validate_existing_chain(home: Path, relative_parent: Path, expected_uid: int) -> None:
    current = home
    for component in relative_parent.parts:
        current = current / component
        if not current.exists() and not current.is_symlink():
            return
        if not _safe_directory(current, expected_uid):
            raise ValueError("UNSAFE_PARENT")


def _exclusive_temp(destination: Path, mutation: _MutationState) -> tuple[Path, BinaryIO]:
    temp = destination.parent / f".{destination.name}.tmp-{uuid.uuid4().hex}"
    descriptor = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    mutation.occurred = True
    try:
        return temp, os.fdopen(descriptor, "wb", buffering=0)
    except Exception:
        try:
            os.close(descriptor)
        finally:
            try:
                temp.unlink()
            except OSError:
                pass
        raise


def _publish_no_clobber(temp: Path, destination: Path) -> None:
    """Atomically publish in one directory without replacing any destination."""
    os.link(temp, destination, follow_symlinks=False)
    temp.unlink()


def _public_file_safe(path: Path, expected_uid: int) -> bool:
    item = observe_file(path, expected_uid=expected_uid, maximum_mode=0o600)
    return (item.regular_file and not item.symlink_rejected and item.expected_ownership
            and item.safe_mode and item.nonempty)


def _exactly_one_recipient(path: Path) -> bool:
    """Boundedly validate one value without returning or reporting that value."""
    try:
        with path.open("rb", buffering=0) as source:
            value = source.read(_MAX_RECIPIENT_BYTES + 1)
    except OSError:
        return False
    if not value or len(value) > _MAX_RECIPIENT_BYTES or b"\r" in value:
        return False
    record = value[:-1] if value.endswith(b"\n") else value
    if b"\n" in record or not record.startswith(b"age1") or len(record) <= 4:
        return False
    return all(byte in b"0123456789abcdefghijklmnopqrstuvwxyz" for byte in record[4:])


def _valid_recipient(path: Path, expected_uid: int, runner: ProcessRunner,
                     executable: ExecutableObserver) -> bool:
    if (not _public_file_safe(path, expected_uid)
            or not _exactly_one_recipient(path) or not executable(AGE)):
        return False
    try:
        result = runner(
            (str(AGE), "--encrypt", "--recipients-file", str(path)), shell=False,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, timeout=_TIMEOUT_SECONDS,
            env=dict(_ENV), check=False,
        )
    except Exception:
        return False
    return getattr(result, "returncode", None) == 0


class _FixedToolEnsure:
    _formula = ""
    _required: tuple[Path, ...] = ()

    def __init__(self, *, process_runner: ProcessRunner = _default_runner,
                 executable_observer: ExecutableObserver = executable_present) -> None:
        self._runner = process_runner
        self._executable = executable_observer

    def _ensure(self) -> MutationOutcome:
        if all(self._executable(path) for path in self._required):
            return MutationOutcome.COMPLETED
        if not self._executable(BREW):
            return MutationOutcome.FAILED
        try:
            result = self._runner((str(BREW), "install", self._formula), shell=False,
                                  stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL, timeout=_TIMEOUT_SECONDS,
                                  env=dict(_ENV), check=False)
        except Exception:
            return MutationOutcome.UNCERTAIN
        if getattr(result, "returncode", None) != 0:
            return MutationOutcome.UNCERTAIN
        return MutationOutcome.COMPLETED if all(self._executable(path) for path in self._required) else MutationOutcome.UNCERTAIN


class ConcreteEnsureSopsTool(_FixedToolEnsure):
    _formula = "sops"
    _required = (SOPS,)

    def ensure_sops_tool(self) -> MutationOutcome:
        return self._ensure()


class ConcreteEnsureAgeTooling(_FixedToolEnsure):
    _formula = "age"
    _required = (AGE, AGE_KEYGEN)

    def ensure_age_tooling(self) -> MutationOutcome:
        return self._ensure()


class _FilesystemCapability:
    def __init__(self, *, control_plane_home: Path, backend_metadata: Mapping[str, Any],
                 expected_uid: int, process_runner: ProcessRunner = _default_runner,
                 executable_observer: ExecutableObserver = executable_present) -> None:
        self._home = Path(control_plane_home)
        self._metadata = backend_metadata
        self._uid = _uid(expected_uid)
        self._runner = process_runner
        self._executable = executable_observer

    def _path(self, key: str) -> tuple[Path, Path]:
        _validate_home(self._home, self._uid)
        relative = _relative(self._metadata, key)
        _validate_existing_chain(self._home, relative.parent, self._uid)
        return self._home / relative, relative


class ConcreteCreateControlPlaneAgeIdentity(_FilesystemCapability):
    def create_control_plane_age_identity(self) -> MutationOutcome:
        mutation = _MutationState()
        try:
            destination, relative = self._path("identity_custody")
            if destination.exists() or destination.is_symlink():
                return MutationOutcome.COMPLETED if structurally_safe_identity(destination, expected_uid=self._uid) else MutationOutcome.FAILED
            if not self._executable(AGE_KEYGEN):
                return MutationOutcome.FAILED
            _prepare_parent(self._home, relative.parent, self._uid, mutation)
        except RuntimeError:
            return mutation.outcome_after_error()
        except (OSError, ValueError, KeyError, TypeError):
            return mutation.outcome_after_error()
        temp: Path | None = None
        try:
            temp, output = _exclusive_temp(destination, mutation)
            with output:
                result = self._runner((str(AGE_KEYGEN),), shell=False, stdin=subprocess.DEVNULL,
                                      stdout=output, stderr=subprocess.DEVNULL,
                                      timeout=_TIMEOUT_SECONDS, env=dict(_ENV), check=False)
            if getattr(result, "returncode", None) != 0:
                return MutationOutcome.UNCERTAIN
            os.chmod(temp, 0o600, follow_symlinks=False)
            if not structurally_safe_identity(temp, expected_uid=self._uid):
                return MutationOutcome.UNCERTAIN
            _publish_no_clobber(temp, destination)
            temp = None
            return MutationOutcome.COMPLETED if structurally_safe_identity(destination, expected_uid=self._uid) else MutationOutcome.UNCERTAIN
        except Exception:
            return mutation.outcome_after_error()
        finally:
            if temp is not None:
                try: temp.unlink()
                except OSError: pass


class ConcreteRegisterControlPlaneRecipientMetadata(_FilesystemCapability):
    def _derive(self, identity: Path, output: Any) -> Any:
        return self._runner((str(AGE_KEYGEN), "-y", str(identity)), shell=False,
                            stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.DEVNULL,
                            timeout=_TIMEOUT_SECONDS, env=dict(_ENV), check=False)

    def register_control_plane_recipient_metadata(self) -> MutationOutcome:
        mutation = _MutationState()
        temp: Path | None = None
        try:
            identity, _ = self._path("identity_custody")
            destination, relative = self._path("control_plane_recipient")
            if not structurally_safe_identity(identity, expected_uid=self._uid) or not self._executable(AGE_KEYGEN):
                return MutationOutcome.FAILED
            if destination.exists() or destination.is_symlink():
                if not _valid_recipient(destination, self._uid, self._runner, self._executable):
                    return MutationOutcome.FAILED
                temp, output = _exclusive_temp(destination, mutation)
                with output:
                    result = self._derive(identity, output)
                if getattr(result, "returncode", None) != 0:
                    return MutationOutcome.UNCERTAIN
                os.chmod(temp, 0o600, follow_symlinks=False)
                return (MutationOutcome.COMPLETED if filecmp.cmp(temp, destination, shallow=False)
                        else mutation.outcome_after_error())
            _prepare_parent(self._home, relative.parent, self._uid, mutation)
            temp, output = _exclusive_temp(destination, mutation)
            with output:
                result = self._derive(identity, output)
            if getattr(result, "returncode", None) != 0 or not _valid_recipient(temp, self._uid, self._runner, self._executable):
                return MutationOutcome.UNCERTAIN
            _publish_no_clobber(temp, destination); temp = None
            return MutationOutcome.COMPLETED
        except Exception:
            return mutation.outcome_after_error()
        finally:
            if temp is not None:
                try: temp.unlink()
                except OSError: pass


class ConcreteRegisterOfflineRecoveryPublicMetadata(_FilesystemCapability):
    def register_offline_recovery_public_metadata(self) -> MutationOutcome:
        mutation = _MutationState()
        temp: Path | None = None
        try:
            source, _ = self._path("offline_recovery_inbox")
            destination, relative = self._path("offline_recovery_recipient")
            if not _valid_recipient(source, self._uid, self._runner, self._executable):
                return MutationOutcome.FAILED
            if destination.exists() or destination.is_symlink():
                if not _valid_recipient(destination, self._uid, self._runner, self._executable):
                    return MutationOutcome.FAILED
                return MutationOutcome.COMPLETED if filecmp.cmp(source, destination, shallow=False) else MutationOutcome.FAILED
            _prepare_parent(self._home, relative.parent, self._uid, mutation)
            temp, output = _exclusive_temp(destination, mutation)
            with source.open("rb", buffering=0) as input_file, output:
                while True:
                    chunk = input_file.read(64)
                    if not chunk: break
                    output.write(chunk)
            os.chmod(temp, 0o600, follow_symlinks=False)
            if not _valid_recipient(temp, self._uid, self._runner, self._executable):
                return MutationOutcome.UNCERTAIN
            _publish_no_clobber(temp, destination); temp = None
            return MutationOutcome.COMPLETED
        except Exception:
            return mutation.outcome_after_error()
        finally:
            if temp is not None:
                try: temp.unlink()
                except OSError: pass


class ConcreteIntakeOfflineRecoveryPublicRecipient:
    """Create only the fixed public-recipient inbox artifact, exactly once."""

    def __init__(
        self, *, control_plane_home: Path, intake_policy: Mapping[str, Any],
        expected_uid: int, expected_gid: int,
        public_recipient: OfflineRecoveryPublicRecipient,
        process_runner: ProcessRunner = _default_runner,
        executable_observer: ExecutableObserver = executable_present,
    ) -> None:
        self._home = Path(control_plane_home)
        self._policy = dict(intake_policy)
        self._uid = _uid(expected_uid)
        self._gid = _uid(expected_gid)
        if not isinstance(public_recipient, OfflineRecoveryPublicRecipient):
            raise TypeError("INVALID_PUBLIC_RECIPIENT_BOUNDARY")
        self._recipient = public_recipient
        self._runner = process_runner
        self._executable = executable_observer

    def intake_offline_recovery_public_recipient(self) -> MutationOutcome:
        mutation = _MutationState()
        descriptor: int | None = None
        parent_descriptor: int | None = None
        fresh_parent_descriptor: int | None = None
        try:
            _validate_home(self._home, self._uid)
            if self._policy != {
                "base": "control-plane-home",
                "relative_path": str(_INTAKE_RELATIVE_PATH),
                "required_owner": "control-plane-user",
                "maximum_mode": "0600",
                "external_to_repository": True,
                "no_clobber": True,
                "public_recipient_only": True,
            }:
                return MutationOutcome.FAILED
            destination = self._home / _INTAKE_RELATIVE_PATH
            if not _outside_repository(destination):
                return MutationOutcome.FAILED
            if not _trusted_age_prevalidation(
                self._recipient, self._runner, self._executable
            ):
                return MutationOutcome.FAILED
            parent_descriptor = _open_trusted_intake_parent(
                self._home, _INTAKE_RELATIVE_PATH, self._uid, self._gid
            )
            descriptor = os.open(
                _INTAKE_RELATIVE_PATH.name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                0o600,
                dir_fd=parent_descriptor,
            )
            mutation.occurred = True
            payload = self._recipient._encoded + b"\n"
            if os.write(descriptor, payload) != len(payload):
                return MutationOutcome.UNCERTAIN
            os.fsync(descriptor)
            created_metadata = os.fstat(descriptor)
            if not _safe_intake_leaf_metadata(
                created_metadata, uid=self._uid, gid=self._gid,
                expected_size=len(payload),
            ):
                return MutationOutcome.UNCERTAIN
            original_parent_metadata = os.fstat(parent_descriptor)
            fresh_parent_descriptor = _open_trusted_intake_parent(
                self._home, _INTAKE_RELATIVE_PATH, self._uid, self._gid
            )
            fresh_parent_metadata = os.fstat(fresh_parent_descriptor)
            if ((fresh_parent_metadata.st_dev, fresh_parent_metadata.st_ino)
                    != (original_parent_metadata.st_dev, original_parent_metadata.st_ino)):
                return MutationOutcome.UNCERTAIN
            canonical_metadata = os.stat(
                _INTAKE_RELATIVE_PATH.name, dir_fd=fresh_parent_descriptor,
                follow_symlinks=False,
            )
            if ((canonical_metadata.st_dev, canonical_metadata.st_ino)
                    != (created_metadata.st_dev, created_metadata.st_ino)
                    or not _safe_intake_leaf_metadata(
                        canonical_metadata, uid=self._uid, gid=self._gid,
                        expected_size=len(payload),
                    )):
                return MutationOutcome.UNCERTAIN
            return MutationOutcome.COMPLETED
        except Exception:
            return mutation.outcome_after_error()
        finally:
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            if parent_descriptor is not None:
                try:
                    os.close(parent_descriptor)
                except OSError:
                    pass
            if fresh_parent_descriptor is not None:
                try:
                    os.close(fresh_parent_descriptor)
                except OSError:
                    pass


__all__ = (
    "ConcreteCreateControlPlaneAgeIdentity", "ConcreteEnsureAgeTooling",
    "ConcreteEnsureSopsTool", "ConcreteIntakeOfflineRecoveryPublicRecipient",
    "ConcreteRegisterControlPlaneRecipientMetadata",
    "ConcreteRegisterOfflineRecoveryPublicMetadata", "OfflineRecoveryPublicRecipient",
)

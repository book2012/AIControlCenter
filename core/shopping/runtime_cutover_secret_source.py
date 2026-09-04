"""Trusted, read-only runtime-cutover secret source observation.

This module establishes source provenance, filesystem safety, key-name presence,
and one fixed non-secret configuration guard. It grants no authorization and
deliberately exposes no assignment values or raw records.
"""

from __future__ import annotations

import json
import os
import re
import stat
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePath
from typing import Callable

from core.secrets.mariadb_continuity_trusted_mac_account_home_runtime_resolver import (
    ResolvedTrustedMacAccountHome,
    resolve_trusted_mac_account_home,
)
from core.secrets.mariadb_continuity_trusted_ownership_expectation import (
    TrustedOwnershipExpectation,
    issue_trusted_ownership_expectation,
)


SOURCE_AUTHORITY = "TRUSTED_MAC_ACCOUNT_HOME_RUNTIME_RESOLVER"
SOURCE_ROLE = "runtime_cutover_variable_source"
PATH_ROLE = "fixed_control_plane_application_support_secret_file"
SOURCE_COMPONENTS = (
    "Library", "Application Support", "AIControlCenter", "secrets",
    "shopping-commerce.env",
)
SOURCE_RELATIVE_PATH = str(PurePath(*SOURCE_COMPONENTS))
MAX_SOURCE_BYTES = 64 * 1024
MAX_RECORD_BYTES = 4096
_KEY_NAME = re.compile(r"SHOPPING_[A-Z0-9_]+")
WORDPRESS_PORT_KEY = "SHOPPING_WORDPRESS_PORT"
WORDPRESS_PORT_EXPECTED = "58082"


class SourceReason(str, Enum):
    READY = "READY"
    TRUST_SOURCE_UNAVAILABLE = "TRUST_SOURCE_UNAVAILABLE"
    UNSAFE_PATH = "UNSAFE_PATH"
    UNSAFE_FILESYSTEM_METADATA = "UNSAFE_FILESYSTEM_METADATA"
    EMPTY_SOURCE = "EMPTY_SOURCE"
    OVERSIZED_SOURCE = "OVERSIZED_SOURCE"
    UNSAFE_RECORD_STRUCTURE = "UNSAFE_RECORD_STRUCTURE"
    MALFORMED_ASSIGNMENT = "MALFORMED_ASSIGNMENT"
    DUPLICATE_KEY_NAMES = "DUPLICATE_KEY_NAMES"
    UNKNOWN_KEY_NAMES = "UNKNOWN_KEY_NAMES"
    MISSING_REQUIRED_KEY_NAMES = "MISSING_REQUIRED_KEY_NAMES"
    WORDPRESS_PORT_VALUE_INVALID = "WORDPRESS_PORT_VALUE_INVALID"
    CONTRACT_UNAVAILABLE = "CONTRACT_UNAVAILABLE"


class RuntimeCutoverSourceError(RuntimeError):
    """Value-free failure carrying only a typed reason code."""

    def __init__(self, reason: SourceReason) -> None:
        self.reason = reason
        super().__init__(reason.value)


@dataclass(frozen=True, slots=True)
class RuntimeCutoverSourceObservation:
    schema_version: str
    source_authority: str
    source_role: str
    path_role: str
    filesystem_safe: bool
    required_key_names_present: tuple[str, ...]
    missing_key_names: tuple[str, ...]
    duplicate_key_names: tuple[str, ...]
    unknown_key_names: tuple[str, ...]
    ready: bool
    reason_code: SourceReason
    wordpress_port_expected: str = WORDPRESS_PORT_EXPECTED
    wordpress_port_value_valid: bool = False
    values_exposed: bool = False
    mutation_performed: bool = False

    def projection(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "source_authority": self.source_authority,
            "source_role": self.source_role,
            "path_role": self.path_role,
            "filesystem_safe": self.filesystem_safe,
            "required_key_names_present": list(self.required_key_names_present),
            "missing_key_names": list(self.missing_key_names),
            "duplicate_key_names": list(self.duplicate_key_names),
            "unknown_key_names": list(self.unknown_key_names),
            "ready": self.ready,
            "reason_code": self.reason_code.value,
            "wordpress_port_expected": WORDPRESS_PORT_EXPECTED,
            "wordpress_port_value_valid": self.wordpress_port_value_valid,
            "values_exposed": False,
            "mutation_performed": False,
        }


@dataclass(frozen=True, slots=True)
class _OpenedSource:
    descriptor: int
    concrete_path: str
    metadata: os.stat_result


def _validate_components(components: tuple[str, ...]) -> None:
    if components != SOURCE_COMPONENTS or any(
        not component or component in {".", ".."} or "/" in component or "\0" in component
        for component in components
    ):
        raise RuntimeCutoverSourceError(SourceReason.UNSAFE_PATH)


def _repository_contract_path(repository_root: Path) -> Path:
    return repository_root / "deploy/shopping/config/secret-contract.json"


def _required_and_known_names(repository_root: Path) -> tuple[tuple[str, ...], frozenset[str]]:
    try:
        payload = json.loads(_repository_contract_path(repository_root).read_text(encoding="utf-8"))
        if (
            not isinstance(payload, dict)
            or payload.get("schema_version") != "1.0"
            or payload.get("value_free") is not True
            or payload.get("actions") != ["runtime_cutover", "bootstrap"]
            or not isinstance(payload.get("keys"), list)
        ):
            raise ValueError
        names: list[str] = []
        required: list[str] = []
        for item in payload["keys"]:
            name = item["name"]
            flags = item["required"]
            if (
                not isinstance(name, str) or _KEY_NAME.fullmatch(name) is None
                or name in names or list(flags) != payload["actions"]
                or any(type(flags[action]) is not bool for action in payload["actions"])
            ):
                raise ValueError
            names.append(name)
            if flags["runtime_cutover"]:
                required.append(name)
        if not required:
            raise ValueError
        return tuple(required), frozenset(names)
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        raise RuntimeCutoverSourceError(SourceReason.CONTRACT_UNAVAILABLE) from None


def _open_source(
    resolved_home: ResolvedTrustedMacAccountHome,
    ownership: TrustedOwnershipExpectation,
    repository_root: Path,
) -> tuple[_OpenedSource, list[int]]:
    if type(resolved_home) is not ResolvedTrustedMacAccountHome or type(ownership) is not TrustedOwnershipExpectation:
        raise RuntimeCutoverSourceError(SourceReason.TRUST_SOURCE_UNAVAILABLE)
    _validate_components(SOURCE_COMPONENTS)
    home = PurePath(resolved_home.passwd_home)
    if not home.is_absolute() or any(part in {"", ".", ".."} for part in home.parts[1:]):
        raise RuntimeCutoverSourceError(SourceReason.UNSAFE_PATH)
    concrete = home.joinpath(*SOURCE_COMPONENTS)
    try:
        if os.path.commonpath((str(concrete), str(repository_root.resolve()))) == str(repository_root.resolve()):
            raise RuntimeCutoverSourceError(SourceReason.UNSAFE_PATH)
    except ValueError:
        raise RuntimeCutoverSourceError(SourceReason.UNSAFE_PATH) from None
    if not all(hasattr(os, flag) for flag in ("O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC")) or os.open not in os.supports_dir_fd:
        raise RuntimeCutoverSourceError(SourceReason.UNSAFE_FILESYSTEM_METADATA)

    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    file_flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    descriptors: list[int] = []
    try:
        current = os.open("/", directory_flags)
        descriptors.append(current)
        root_metadata = os.fstat(current)
        if not stat.S_ISDIR(root_metadata.st_mode) or root_metadata.st_mode & 0o022:
            raise RuntimeCutoverSourceError(SourceReason.UNSAFE_FILESYSTEM_METADATA)

        home_components = home.parts[1:]
        parent_components = (*home_components, *SOURCE_COMPONENTS[:-1])
        home_index = len(home_components) - 1
        shared_parent_index = len(home_components) + 2
        secrets_index = len(parent_components) - 1
        for index, component in enumerate(parent_components):
            entry = os.stat(component, dir_fd=current, follow_symlinks=False)
            opened = os.open(component, directory_flags, dir_fd=current)
            current = opened
            descriptors.append(current)
            metadata = os.fstat(current)
            if (
                not stat.S_ISDIR(entry.st_mode)
                or stat.S_ISLNK(entry.st_mode)
                or not stat.S_ISDIR(metadata.st_mode)
                or (entry.st_dev, entry.st_ino) != (metadata.st_dev, metadata.st_ino)
            ):
                raise RuntimeCutoverSourceError(SourceReason.UNSAFE_FILESYSTEM_METADATA)
            mode = stat.S_IMODE(metadata.st_mode)
            if index < home_index:
                safe = metadata.st_mode & 0o022 == 0
            elif index < shared_parent_index:
                safe = (
                    (metadata.st_uid, metadata.st_gid)
                    == (ownership.expected_uid, ownership.expected_gid)
                    and metadata.st_mode & 0o022 == 0
                )
            elif index == shared_parent_index:
                safe = (
                    (metadata.st_uid, metadata.st_gid)
                    == (ownership.expected_uid, ownership.expected_gid)
                    and mode == 0o755
                )
            elif index == secrets_index:
                safe = (
                    (metadata.st_uid, metadata.st_gid)
                    == (ownership.expected_uid, ownership.expected_gid)
                    and mode == 0o700
                )
            else:
                safe = False
            if not safe:
                raise RuntimeCutoverSourceError(SourceReason.UNSAFE_FILESYSTEM_METADATA)
        descriptor = os.open(SOURCE_COMPONENTS[-1], file_flags, dir_fd=current)
        descriptors.append(descriptor)
        metadata = os.fstat(descriptor)
        mode = stat.S_IMODE(metadata.st_mode)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or (metadata.st_uid, metadata.st_gid) != (ownership.expected_uid, ownership.expected_gid)
            or mode & ~0o600
            or metadata.st_nlink != 1
        ):
            raise RuntimeCutoverSourceError(SourceReason.UNSAFE_FILESYSTEM_METADATA)
        if metadata.st_size == 0:
            raise RuntimeCutoverSourceError(SourceReason.EMPTY_SOURCE)
        if metadata.st_size < 0 or metadata.st_size > MAX_SOURCE_BYTES:
            raise RuntimeCutoverSourceError(SourceReason.OVERSIZED_SOURCE)
        return _OpenedSource(descriptor, str(concrete), metadata), descriptors
    except RuntimeCutoverSourceError:
        for opened_descriptor in reversed(descriptors):
            try:
                os.close(opened_descriptor)
            except OSError:
                pass
        raise
    except (OSError, TypeError, ValueError):
        for opened_descriptor in reversed(descriptors):
            try:
                os.close(opened_descriptor)
            except OSError:
                pass
        raise RuntimeCutoverSourceError(SourceReason.UNSAFE_FILESYSTEM_METADATA) from None


def _observe_records(
    descriptor: int, expected_size: int,
) -> tuple[frozenset[str], tuple[str, ...], bool]:
    present: set[str] = set()
    duplicates: set[str] = set()
    pending = bytearray()
    total = 0
    wordpress_port_value_valid = False

    def accept(raw_record: bytes) -> None:
        if len(raw_record) > MAX_RECORD_BYTES:
            raise RuntimeCutoverSourceError(SourceReason.OVERSIZED_SOURCE)
        if b"\0" in raw_record or b"\r" in raw_record:
            raise RuntimeCutoverSourceError(SourceReason.UNSAFE_RECORD_STRUCTURE)
        try:
            record = raw_record.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            raise RuntimeCutoverSourceError(SourceReason.UNSAFE_RECORD_STRUCTURE) from None
        if not record or record.startswith("#"):
            del record
            return
        name, separator, decoded_value = record.partition("=")
        del decoded_value, record
        if not separator or _KEY_NAME.fullmatch(name) is None:
            raise RuntimeCutoverSourceError(SourceReason.MALFORMED_ASSIGNMENT)
        if name in present:
            duplicates.add(name)
        present.add(name)
        if name == WORDPRESS_PORT_KEY:
            nonlocal wordpress_port_value_valid
            _raw_name, _raw_separator, raw_value = raw_record.partition(b"=")
            wordpress_port_value_valid = raw_value == WORDPRESS_PORT_EXPECTED.encode("ascii")
            del raw_value, _raw_name, _raw_separator

    while total <= MAX_SOURCE_BYTES:
        chunk = os.read(descriptor, min(8192, MAX_SOURCE_BYTES + 1 - total))
        if not chunk:
            break
        total += len(chunk)
        pending.extend(chunk)
        while b"\n" in pending:
            raw_record, _, remainder = pending.partition(b"\n")
            pending = bytearray(remainder)
            accept(raw_record)
        if len(pending) > MAX_RECORD_BYTES:
            raise RuntimeCutoverSourceError(SourceReason.OVERSIZED_SOURCE)
    if total > MAX_SOURCE_BYTES or total != expected_size:
        raise RuntimeCutoverSourceError(SourceReason.OVERSIZED_SOURCE)
    if pending:
        accept(bytes(pending))
    return frozenset(present), tuple(sorted(duplicates)), wordpress_port_value_valid


def _failure(reason: SourceReason, required: tuple[str, ...] = ()) -> RuntimeCutoverSourceObservation:
    return RuntimeCutoverSourceObservation(
        "1.0", SOURCE_AUTHORITY, SOURCE_ROLE, PATH_ROLE, False, (), required,
        (), (), False, reason,
    )


def _observe_runtime_cutover_source(
    *,
    resolved_home: ResolvedTrustedMacAccountHome,
    ownership: TrustedOwnershipExpectation,
    repository_root: Path,
) -> RuntimeCutoverSourceObservation:
    """Test seam accepting trust facts, never a caller-selected source path."""
    descriptors: list[int] = []
    try:
        required, known = _required_and_known_names(repository_root)
        opened, descriptors = _open_source(resolved_home, ownership, repository_root)
        present, duplicates, wordpress_port_value_valid = _observe_records(
            opened.descriptor, opened.metadata.st_size,
        )
        after = os.fstat(opened.descriptor)
        before = opened.metadata
        if (before.st_dev, before.st_ino, before.st_mode, before.st_uid, before.st_gid,
            before.st_size, before.st_nlink) != (
            after.st_dev, after.st_ino, after.st_mode, after.st_uid, after.st_gid,
            after.st_size, after.st_nlink):
            raise RuntimeCutoverSourceError(SourceReason.UNSAFE_FILESYSTEM_METADATA)
        missing = tuple(name for name in required if name not in present)
        unknown = tuple(sorted(present - known))
        reason = (
            SourceReason.DUPLICATE_KEY_NAMES if duplicates
            else SourceReason.UNKNOWN_KEY_NAMES if unknown
            else SourceReason.MISSING_REQUIRED_KEY_NAMES if missing
            else SourceReason.WORDPRESS_PORT_VALUE_INVALID
            if not wordpress_port_value_valid
            else SourceReason.READY
        )
        return RuntimeCutoverSourceObservation(
            "1.0", SOURCE_AUTHORITY, SOURCE_ROLE, PATH_ROLE, True,
            tuple(name for name in required if name in present), missing,
            duplicates, unknown, reason is SourceReason.READY, reason,
            wordpress_port_value_valid=wordpress_port_value_valid,
        )
    except RuntimeCutoverSourceError as error:
        required_names = locals().get("required", ())
        return _failure(error.reason, tuple(required_names))
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


def observe_runtime_cutover_source() -> RuntimeCutoverSourceObservation:
    """Observe the sole repository-defined source without path input or mutation."""
    repository_root = Path(__file__).resolve().parents[2]
    try:
        home = resolve_trusted_mac_account_home()
        ownership = issue_trusted_ownership_expectation(home)
    except Exception:
        return _failure(SourceReason.TRUST_SOURCE_UNAVAILABLE)
    return _observe_runtime_cutover_source(
        resolved_home=home, ownership=ownership, repository_root=repository_root,
    )


__all__ = (
    "PATH_ROLE", "SOURCE_AUTHORITY", "SOURCE_RELATIVE_PATH", "SOURCE_ROLE",
    "WORDPRESS_PORT_EXPECTED", "WORDPRESS_PORT_KEY",
    "RuntimeCutoverSourceObservation", "SourceReason",
    "observe_runtime_cutover_source",
)

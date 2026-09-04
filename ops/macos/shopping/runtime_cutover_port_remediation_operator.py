"""Mac-local fixed-path atomic capability for SHOP-SERVICE-START-01B."""

from __future__ import annotations

import os
import stat
import uuid
from pathlib import Path

from core.secrets.mariadb_continuity_trusted_mac_account_home_runtime_resolver import (
    ResolvedTrustedMacAccountHome,
    resolve_trusted_mac_account_home,
)
from core.secrets.mariadb_continuity_trusted_ownership_expectation import (
    TrustedOwnershipExpectation,
    issue_trusted_ownership_expectation,
)
from core.shopping.runtime_cutover_port_remediation import (
    DESIRED_VALUE, Outcome, Result, execute_remediation,
)
from core.shopping.runtime_cutover_secret_source import (
    MAX_RECORD_BYTES, MAX_SOURCE_BYTES, SOURCE_COMPONENTS, WORDPRESS_PORT_KEY,
    RuntimeCutoverSourceError, SourceReason, _KEY_NAME, _open_source, _required_and_known_names,
    observe_runtime_cutover_source,
)
from ops.macos.shopping.runtime_cutover_source_authorization_store import (
    RuntimeCutoverSourceAuthorizationStore,
)

_ROOT = Path(__file__).resolve().parents[3]


class _AtomicRuntimeCutoverPortMutation:
    """Private filesystem seam bound to the trusted source and one value."""

    def replace_wordpress_port(self) -> Outcome:
        home = resolve_trusted_mac_account_home()
        ownership = issue_trusted_ownership_expectation(home)
        return _replace_wordpress_port_at_trusted_source(
            resolved_home=home,
            ownership=ownership,
            repository_root=_ROOT,
        )


def _replace_wordpress_port_at_trusted_source(
    *,
    resolved_home: ResolvedTrustedMacAccountHome,
    ownership: TrustedOwnershipExpectation,
    repository_root: Path,
) -> Outcome:
    """Internal fixture seam; public callers cannot configure the live capability."""
    descriptors: list[int] = []
    temp_leaf: str | None = None
    parent_fd: int | None = None
    published = False
    try:
        required, known = _required_and_known_names(repository_root)
        opened, descriptors = _open_source(resolved_home, ownership, repository_root)
        parent_fd = descriptors[-2]
        payload = _read_exact(opened.descriptor, opened.metadata.st_size)
        transformed = _transform(payload, required, known)
        current = os.fstat(opened.descriptor)
        _same_identity(opened.metadata, current)
        temp_leaf = f".{SOURCE_COMPONENTS[-1]}.tmp-{uuid.uuid4().hex}"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
        temp_fd = os.open(temp_leaf, flags, 0o600, dir_fd=parent_fd)
        try:
            os.fchmod(temp_fd, stat.S_IMODE(opened.metadata.st_mode))
            os.fchown(temp_fd, opened.metadata.st_uid, opened.metadata.st_gid)
            _write_all(temp_fd, transformed)
            os.fsync(temp_fd)
        finally:
            os.close(temp_fd)
        leaf = SOURCE_COMPONENTS[-1]
        path_meta = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        current = os.fstat(opened.descriptor)
        _same_identity(opened.metadata, path_meta)
        _same_identity(opened.metadata, current)
        try:
            os.replace(temp_leaf, leaf, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
        except Exception:
            return Outcome.UNCERTAIN
        published = True
        temp_leaf = None
        try:
            os.fsync(parent_fd)
        except Exception:
            return Outcome.UNCERTAIN
        return Outcome.SUCCEEDED
    except RuntimeCutoverSourceError:
        return Outcome.FAILED
    except Exception:
        return Outcome.FAILED
    finally:
        if temp_leaf is not None and not published and parent_fd is not None:
            try:
                os.unlink(temp_leaf, dir_fd=parent_fd)
            except OSError:
                pass
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _read_exact(fd: int, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = os.read(fd, min(8192, remaining))
        if not chunk:
            raise RuntimeCutoverSourceError(SourceReason.UNSAFE_FILESYSTEM_METADATA)
        chunks.append(chunk)
        remaining -= len(chunk)
    if os.read(fd, 1):
        raise RuntimeCutoverSourceError(SourceReason.OVERSIZED_SOURCE)
    return b"".join(chunks)


def _transform(payload: bytes, required: tuple[str, ...], known: frozenset[str]) -> bytes:
    if not payload or len(payload) > MAX_SOURCE_BYTES or b"\0" in payload or b"\r" in payload:
        raise RuntimeCutoverSourceError(SourceReason.UNSAFE_RECORD_STRUCTURE)
    records = payload.splitlines(keepends=True)
    present: set[str] = set()
    port_indexes: list[tuple[int, int]] = []
    offset = 0
    for raw_with_newline in records:
        raw = raw_with_newline[:-1] if raw_with_newline.endswith(b"\n") else raw_with_newline
        if len(raw) > MAX_RECORD_BYTES:
            raise RuntimeCutoverSourceError(SourceReason.OVERSIZED_SOURCE)
        try:
            decoded = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            raise RuntimeCutoverSourceError(SourceReason.UNSAFE_RECORD_STRUCTURE) from None
        if decoded and not decoded.startswith("#"):
            name, separator, _value = decoded.partition("=")
            if not separator or _KEY_NAME.fullmatch(name) is None:
                raise RuntimeCutoverSourceError(SourceReason.MALFORMED_ASSIGNMENT)
            if name in present:
                raise RuntimeCutoverSourceError(SourceReason.DUPLICATE_KEY_NAMES)
            present.add(name)
            if name == WORDPRESS_PORT_KEY:
                equals = raw.index(b"=")
                port_indexes.append((offset + equals + 1, offset + len(raw)))
        offset += len(raw_with_newline)
    if present - known:
        raise RuntimeCutoverSourceError(SourceReason.UNKNOWN_KEY_NAMES)
    if any(name not in present for name in required) or len(port_indexes) != 1:
        raise RuntimeCutoverSourceError(SourceReason.MISSING_REQUIRED_KEY_NAMES)
    start, end = port_indexes[0]
    if payload[start:end] == DESIRED_VALUE.encode("ascii"):
        raise RuntimeCutoverSourceError(SourceReason.READY)
    return payload[:start] + DESIRED_VALUE.encode("ascii") + payload[end:]


def _same_identity(expected: os.stat_result, actual: os.stat_result) -> None:
    fields = ("st_dev", "st_ino", "st_mode", "st_uid", "st_gid", "st_size", "st_nlink")
    if any(getattr(expected, field) != getattr(actual, field) for field in fields):
        raise RuntimeCutoverSourceError(SourceReason.UNSAFE_FILESYSTEM_METADATA)


def _write_all(fd: int, payload: bytes) -> None:
    view = memoryview(payload)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise OSError("WRITE_FAILED")
        view = view[written:]


def run() -> Result:
    """Run the sole fixed repair, failing closed unless durable authority exists."""
    initial = observe_runtime_cutover_source()
    try:
        authorization = RuntimeCutoverSourceAuthorizationStore.open_existing()
    except Exception:
        authorization = None
    return execute_remediation(
        initial_observation=initial,
        observe_source=observe_runtime_cutover_source,
        authorization=authorization,
        mutation=_AtomicRuntimeCutoverPortMutation(),
    )


__all__ = ("run",)

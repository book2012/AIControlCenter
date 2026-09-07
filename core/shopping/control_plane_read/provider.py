"""Read-only fixed Mac source; never creates or rewrites a capability file."""
import os
import stat
from pathlib import PurePosixPath, Path

from core.secrets.mariadb_continuity_trusted_mac_account_home_runtime_resolver import resolve_trusted_mac_account_home
from core.secrets.mariadb_continuity_trusted_ownership_expectation import issue_trusted_ownership_expectation
from .capability import CapabilityError, ControlPlaneShoppingReadCapability

COMPONENTS = ("Library", "Application Support", "AIControlCenter", "secrets", "shopping-read-capability-v1.env")
KEY = b"AICONTROLCENTER_SHOPPING_READ_CAPABILITY_V1"
MAX_SOURCE_BYTES = 256


def _identity(s):
    return (s.st_dev, s.st_ino, s.st_mode, s.st_uid, s.st_gid, s.st_nlink,
            s.st_size, s.st_mtime_ns, s.st_ctime_ns)


def _read_fixed(home, uid, gid):
    """Private filesystem test seam; public provider has no path arguments."""
    descriptors = []
    edges = []
    result = None
    try:
        parts = PurePosixPath(home).parts
        if not parts or parts[0] != "/" or ".." in parts or str(PurePosixPath(home)) != home:
            raise CapabilityError()
        target = PurePosixPath(home).joinpath(*COMPONENTS)
        if target.is_relative_to(Path(__file__).resolve().parents[3]):
            raise CapabilityError()
        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
        parent = os.open("/", flags | os.O_DIRECTORY)
        descriptors.append(parent)
        root_metadata = os.fstat(parent)
        if root_metadata.st_uid != 0 or root_metadata.st_mode & 0o022:
            raise CapabilityError()
        directories = (*parts[1:], *COMPONENTS[:-1])
        for index, component in enumerate(directories):
            before = os.stat(component, dir_fd=parent, follow_symlinks=False)
            fd = os.open(component, flags | os.O_DIRECTORY, dir_fd=parent)
            descriptors.append(fd)
            current = os.fstat(fd)
            if _identity(before) != _identity(current) or not stat.S_ISDIR(current.st_mode):
                raise CapabilityError()
            if index >= len(parts) - 2:
                if (current.st_uid, current.st_gid) != (uid, gid):
                    raise CapabilityError()
            elif current.st_uid != 0:
                raise CapabilityError()
            if current.st_mode & 0o022:
                raise CapabilityError()
            if index == len(directories) - 1 and stat.S_IMODE(current.st_mode) != 0o700:
                raise CapabilityError()
            edges.append((parent, component, fd, _identity(current)))
            parent = fd
        leaf = COMPONENTS[-1]
        before = os.stat(leaf, dir_fd=parent, follow_symlinks=False)
        fd = os.open(leaf, flags | os.O_NONBLOCK, dir_fd=parent)
        descriptors.append(fd)
        current = os.fstat(fd)
        if (_identity(before) != _identity(current) or not stat.S_ISREG(current.st_mode)
                or (current.st_uid, current.st_gid) != (uid, gid)
                or stat.S_IMODE(current.st_mode) != 0o600 or current.st_nlink != 1
                or not 0 < current.st_size <= MAX_SOURCE_BYTES):
            raise CapabilityError()
        source = bytearray()
        while len(source) <= MAX_SOURCE_BYTES:
            block = os.read(fd, MAX_SOURCE_BYTES + 1 - len(source))
            if not block:
                break
            source.extend(block)
        if len(source) != current.st_size or _identity(current) != _identity(os.fstat(fd)):
            raise CapabilityError()
        edges.append((parent, leaf, fd, _identity(current)))
        if _identity(os.fstat(descriptors[0])) != _identity(root_metadata):
            raise CapabilityError()
        for directory, name, opened, original in edges:
            if (_identity(os.stat(name, dir_fd=directory, follow_symlinks=False)) != original
                    or _identity(os.fstat(opened)) != original):
                raise CapabilityError()
        # A single canonical assignment, with one optional final LF. No comments or extra keys.
        record = bytes(source)
        if record.endswith(b"\n"):
            record = record[:-1]
        prefix = KEY + b"="
        if not record.startswith(prefix) or len(record) != len(prefix) + 64:
            raise CapabilityError()
        result = ControlPlaneShoppingReadCapability(record[len(prefix):].decode("ascii"))
    except Exception:
        pass
    finally:
        for fd in reversed(descriptors):
            os.close(fd)
    if result is None:
        raise CapabilityError()
    return result


class ControlPlaneShoppingReadCapabilityFileProvider:
    __slots__ = ()

    def load(self):
        result = None
        try:
            home = resolve_trusted_mac_account_home()
            ownership = issue_trusted_ownership_expectation(home)
            if (os.getuid(), os.geteuid()) != (ownership.expected_uid,) * 2:
                raise CapabilityError()
            if (os.getgid(), os.getegid()) != (ownership.expected_gid,) * 2:
                raise CapabilityError()
            result = _read_fixed(home.passwd_home, ownership.expected_uid, ownership.expected_gid)
        except Exception:
            pass
        if result is None:
            raise CapabilityError()
        return result

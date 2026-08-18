"""Metadata-only validation of one fixed protected source slot."""

from dataclasses import dataclass
from enum import Enum
import os
from pathlib import Path
import stat
from typing import Any


class ProtectedSourceReason(str, Enum):
    PROTECTED_PARENT_MISSING = "PROTECTED_PARENT_MISSING"
    PROTECTED_PARENT_UNSAFE = "PROTECTED_PARENT_UNSAFE"
    PROTECTED_PARENT_OWNERSHIP_MISMATCH = "PROTECTED_PARENT_OWNERSHIP_MISMATCH"
    LEAF_MISSING = "LEAF_MISSING"
    LEAF_UNSAFE = "LEAF_UNSAFE"
    LEAF_OWNERSHIP_MISMATCH = "LEAF_OWNERSHIP_MISMATCH"
    LEAF_EMPTY = "LEAF_EMPTY"
    ACCEPTABLE = "ACCEPTABLE"


@dataclass(frozen=True, slots=True)
class ProtectedSourceObservation:
    reason: ProtectedSourceReason
    parent_mode_safe: bool
    parent_ownership_matches: bool
    leaf_mode_safe: bool
    leaf_ownership_matches: bool
    nonempty: bool

    def __post_init__(self) -> None:
        if type(self.reason) is not ProtectedSourceReason:
            raise TypeError("reason must be an exact ProtectedSourceReason")
        facts = (
            self.parent_mode_safe,
            self.parent_ownership_matches,
            self.leaf_mode_safe,
            self.leaf_ownership_matches,
            self.nonempty,
        )
        if any(type(fact) is not bool for fact in facts):
            raise TypeError("protected-source facts must be exact booleans")
        expected = {
            ProtectedSourceReason.PROTECTED_PARENT_MISSING: (False, False, False, False, False),
            ProtectedSourceReason.PROTECTED_PARENT_UNSAFE: (False, False, False, False, False),
            ProtectedSourceReason.PROTECTED_PARENT_OWNERSHIP_MISMATCH: (True, False, False, False, False),
            ProtectedSourceReason.LEAF_MISSING: (True, True, False, False, False),
            ProtectedSourceReason.LEAF_UNSAFE: (True, True, False, False, False),
            ProtectedSourceReason.LEAF_OWNERSHIP_MISMATCH: (True, True, True, False, False),
            ProtectedSourceReason.LEAF_EMPTY: (True, True, True, True, False),
            ProtectedSourceReason.ACCEPTABLE: (True, True, True, True, True),
        }[self.reason]
        if facts != expected:
            raise ValueError("reason contradicts protected-source facts")

    @property
    def acceptable(self) -> bool:
        return self.reason is ProtectedSourceReason.ACCEPTABLE

    def to_projection(self) -> dict[str, Any]:
        return {
            "acceptable": self.acceptable,
            "reason": self.reason.value,
            "parent_mode_safe": self.parent_mode_safe,
            "parent_ownership_matches": self.parent_ownership_matches,
            "leaf_mode_safe": self.leaf_mode_safe,
            "leaf_ownership_matches": self.leaf_ownership_matches,
            "nonempty": self.nonempty,
            "authorization_authority": False,
            "capability_authority": False,
            "execution_authority": False,
            "mutation_authority": False,
            "retry_authority": False,
            "reconnect_authority": False,
            "rollback_authority": False,
            "value_free": True,
        }


def _observation(reason: ProtectedSourceReason) -> ProtectedSourceObservation:
    facts = {
        ProtectedSourceReason.PROTECTED_PARENT_MISSING: (False, False, False, False, False),
        ProtectedSourceReason.PROTECTED_PARENT_UNSAFE: (False, False, False, False, False),
        ProtectedSourceReason.PROTECTED_PARENT_OWNERSHIP_MISMATCH: (True, False, False, False, False),
        ProtectedSourceReason.LEAF_MISSING: (True, True, False, False, False),
        ProtectedSourceReason.LEAF_UNSAFE: (True, True, False, False, False),
        ProtectedSourceReason.LEAF_OWNERSHIP_MISMATCH: (True, True, True, False, False),
        ProtectedSourceReason.LEAF_EMPTY: (True, True, True, True, False),
        ProtectedSourceReason.ACCEPTABLE: (True, True, True, True, True),
    }[reason]
    return ProtectedSourceObservation(reason, *facts)


def observe_fixed_protected_source(
    fixed_slot: Path, *, expected_uid: int, expected_gid: int
) -> ProtectedSourceObservation:
    """Inspect only the supplied slot and its immediate parent using metadata."""

    if not isinstance(fixed_slot, Path):
        raise TypeError("fixed_slot must be Path")
    if type(expected_uid) is not int or type(expected_gid) is not int:
        raise TypeError("expected uid and gid must be explicit integers")

    try:
        parent = os.lstat(fixed_slot.parent)
    except OSError:
        return _observation(ProtectedSourceReason.PROTECTED_PARENT_MISSING)
    parent_mode_safe = (
        stat.S_ISDIR(parent.st_mode)
        and not stat.S_ISLNK(parent.st_mode)
        and stat.S_IMODE(parent.st_mode) == 0o700
    )
    if not parent_mode_safe:
        return _observation(ProtectedSourceReason.PROTECTED_PARENT_UNSAFE)
    if parent.st_uid != expected_uid or parent.st_gid != expected_gid:
        return _observation(ProtectedSourceReason.PROTECTED_PARENT_OWNERSHIP_MISMATCH)

    try:
        leaf = os.lstat(fixed_slot)
    except OSError:
        return _observation(ProtectedSourceReason.LEAF_MISSING)
    leaf_mode_safe = (
        stat.S_ISREG(leaf.st_mode)
        and not stat.S_ISLNK(leaf.st_mode)
        and stat.S_IMODE(leaf.st_mode) & ~0o600 == 0
    )
    if not leaf_mode_safe:
        return _observation(ProtectedSourceReason.LEAF_UNSAFE)
    if leaf.st_uid != expected_uid or leaf.st_gid != expected_gid:
        return _observation(ProtectedSourceReason.LEAF_OWNERSHIP_MISMATCH)
    if leaf.st_size <= 0:
        return _observation(ProtectedSourceReason.LEAF_EMPTY)
    return _observation(ProtectedSourceReason.ACCEPTABLE)

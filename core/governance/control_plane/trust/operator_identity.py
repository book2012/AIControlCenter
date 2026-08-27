"""Fail-closed MAC_LOCAL_OPERATOR_V1 runtime identity boundary."""

from __future__ import annotations

from dataclasses import dataclass
import os
import pwd
import sys
from typing import Protocol

from ..domain.identity import GovernanceIdentity
from .models import OperatorIdentityError


@dataclass(frozen=True, slots=True)
class ObservedMacOperator:
    uid: int
    gid: int
    username: str
    passwd_home: str
    governance_identity: GovernanceIdentity


class TrustedMacOperatorObserver(Protocol):
    def observe(self) -> ObservedMacOperator: ...


class ProductionMacOperatorObserver:
    def observe(self) -> ObservedMacOperator:
        if sys.platform != "darwin":
            raise OperatorIdentityError("operator observation is Darwin-only")
        uid, euid = os.getuid(), os.geteuid()
        if uid != euid or uid <= 0:
            raise OperatorIdentityError("operator process identity is invalid")
        try:
            record = pwd.getpwuid(uid)
        except (KeyError, OSError) as error:
            raise OperatorIdentityError("operator passwd identity is unavailable") from error
        if record.pw_uid != uid or record.pw_gid < 0 or not record.pw_name or not record.pw_dir:
            raise OperatorIdentityError("operator passwd identity is ambiguous")
        return ObservedMacOperator(
            uid,
            record.pw_gid,
            record.pw_name,
            record.pw_dir,
            GovernanceIdentity(record.pw_name, "MAC_LOCAL_OPERATOR_V1"),
        )


def observe_operator(observer: TrustedMacOperatorObserver) -> ObservedMacOperator:
    observed = observer.observe()
    if not isinstance(observed, ObservedMacOperator):
        raise OperatorIdentityError("operator observation is unavailable or ambiguous")
    if observed.uid == 0 or observed.uid < 0 or observed.gid < 0:
        raise OperatorIdentityError("root or invalid operator is prohibited")
    if observed.governance_identity.identity_type != "MAC_LOCAL_OPERATOR_V1":
        raise OperatorIdentityError("operator identity model mismatch")
    return observed

"""Issue the repository-owned trusted ownership expectation.

The value is factual and carries zero authority. It is not unforgeable
provenance, authorization, a capability, admission or verification evidence,
filesystem existence or safety evidence, metadata evidence, RECOVER evidence
sufficiency, Production authorization or readiness, or a security boundary.
Possession and Python object identity grant zero authority. Downstream
security-sensitive boundaries must independently validate every required fact,
item of evidence, and authority.
"""

from dataclasses import dataclass
import grp

from core.secrets.mariadb_continuity_trusted_mac_account_home_runtime_resolver import (
    ResolvedTrustedMacAccountHome,
)


TRUSTED_APPLICATION_GROUP_NAME = "staff"


class TrustedOwnershipExpectationIssuanceError(RuntimeError):
    """The ownership expectation could not be issued under frozen policy."""


@dataclass(frozen=True, slots=True, init=False)
class TrustedOwnershipExpectation:
    """Exact UID/GID expectation carrying no authority or evidence."""

    expected_uid: int
    expected_gid: int

    def __new__(cls):
        raise TypeError(
            "TrustedOwnershipExpectation is constructed only by the repository issuer"
        )


def issue_trusted_ownership_expectation(
    resolved_home: ResolvedTrustedMacAccountHome,
) -> TrustedOwnershipExpectation:
    """Issue the exact repository-owned UID/GID expectation once."""

    if type(resolved_home) is not ResolvedTrustedMacAccountHome:
        raise TrustedOwnershipExpectationIssuanceError(
            "resolved_home must be ResolvedTrustedMacAccountHome"
        )

    try:
        bound_uid = resolved_home.bound_uid
    except (AttributeError, TypeError) as exc:
        raise TrustedOwnershipExpectationIssuanceError(
            "resolved_home does not supply bound_uid"
        ) from exc
    if type(bound_uid) is not int or bound_uid <= 0:
        raise TrustedOwnershipExpectationIssuanceError(
            "bound_uid must be a positive exact int"
        )

    try:
        group_record = grp.getgrnam(TRUSTED_APPLICATION_GROUP_NAME)
    except Exception as exc:
        raise TrustedOwnershipExpectationIssuanceError(
            "trusted application group lookup failed"
        ) from exc
    try:
        expected_gid = group_record.gr_gid
    except (AttributeError, IndexError, TypeError) as exc:
        raise TrustedOwnershipExpectationIssuanceError(
            "group result does not supply gr_gid"
        ) from exc
    if type(expected_gid) is not int or expected_gid < 0:
        raise TrustedOwnershipExpectationIssuanceError(
            "gr_gid must be a non-negative exact int"
        )

    expectation = object.__new__(TrustedOwnershipExpectation)
    object.__setattr__(expectation, "expected_uid", bound_uid)
    object.__setattr__(expectation, "expected_gid", expected_gid)
    return expectation

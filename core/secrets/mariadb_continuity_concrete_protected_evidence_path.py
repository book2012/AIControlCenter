"""Zero-authority lexical composition of the protected-evidence path.

The resulting value is not provenance, authorization, a capability, evidence,
or a security boundary. Python object identity is not a security boundary.
Every security-sensitive downstream boundary must independently validate the
facts, evidence, and authority that it requires.
"""

from dataclasses import dataclass

from core.secrets import (
    mariadb_continuity_authoritative_mac_protected_evidence_suffix as suffix_policy,
)
from core.secrets.mariadb_continuity_trusted_mac_account_home_runtime_resolver import (
    ResolvedTrustedMacAccountHome,
)


@dataclass(frozen=True, slots=True, init=False)
class ConcreteProtectedEvidencePath:
    """A lexical concrete path carrying no authority or filesystem fact."""

    concrete_path: str

    def __new__(cls):
        raise TypeError(
            "ConcreteProtectedEvidencePath is constructed only by the composer"
        )


def compose_concrete_protected_evidence_path(
    resolved_home: ResolvedTrustedMacAccountHome,
) -> ConcreteProtectedEvidencePath:
    """Append the repository-owned suffix without observing or normalizing."""

    if type(resolved_home) is not ResolvedTrustedMacAccountHome:
        raise TypeError("resolved_home must be ResolvedTrustedMacAccountHome")

    passwd_home = resolved_home.passwd_home
    boundary_separator = "" if passwd_home.endswith("/") else "/"
    concrete_path = (
        passwd_home
        + boundary_separator
        + suffix_policy.EXACT_PROTECTED_EVIDENCE_SUFFIX
    )

    result = object.__new__(ConcreteProtectedEvidencePath)
    object.__setattr__(result, "concrete_path", concrete_path)
    return result

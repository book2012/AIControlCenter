"""Typed durable evidence persistence boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..domain import GovernanceEvidenceBundle, GovernanceEvidenceManifest


@dataclass(frozen=True, slots=True)
class EvidencePersistenceReceipt:
    bundle_id: str
    manifest_id: str
    bundle_digest: str
    manifest_digest: str
    persisted: bool


class EvidencePersistencePort(Protocol):
    """Persist canonical evidence without granting recovery or retry authority."""

    def persist_evidence(
        self,
        bundle: GovernanceEvidenceBundle,
        manifest: GovernanceEvidenceManifest,
    ) -> EvidencePersistenceReceipt: ...


__all__ = ("EvidencePersistencePort", "EvidencePersistenceReceipt")

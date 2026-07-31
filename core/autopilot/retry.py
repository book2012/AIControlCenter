"""AIControlCenter-owned default-deny retry classification."""

from __future__ import annotations

from .models import RetryClassification


def classify_retry(
    *,
    repository_edited: bool,
    authorization_created: bool,
    permit_issued: bool,
    claim_created: bool,
    operational_write: bool,
    production_or_safety_violation: bool = False,
    evidence_complete: bool = True,
) -> RetryClassification:
    if production_or_safety_violation or operational_write or not evidence_complete:
        return RetryClassification.NO_RETRY
    if claim_created:
        return RetryClassification.MANUAL_POST_CLAIM_RECOVERY
    if authorization_created or permit_issued or repository_edited:
        return RetryClassification.SAFE_PRE_CLAIM_RECOVERY
    return RetryClassification.SAFE_PREFLIGHT_RETRY

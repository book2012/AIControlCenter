"""Strict live request parsing and fail-closed evidence validation."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any, Mapping

from core.deployment.git_readonly_evidence import (
    ReadOnlyGitEvidenceConfig,
    ReadOnlyGitEvidenceSnapshot,
    ReadOnlyGitEvidenceStatus,
    ReadOnlyGitEvidenceValidator,
)

from .models import *


def _exact(value: Mapping[str, Any], contract: type) -> None:
    expected = {field.name for field in dataclasses.fields(contract)}
    required = {field.name for field in dataclasses.fields(contract)
                if field.default is dataclasses.MISSING
                and field.default_factory is dataclasses.MISSING}
    if not required <= set(value) or set(value) - expected:
        raise ControlledOperationalBootstrapError("REQUEST_FIELDS_INVALID")


class ControlledOperationalBootstrapRequestValidator:
    def parse(self, path: Path) -> ControlledOperationalBootstrapRequest:
        raw = Path(path).read_text(encoding="utf-8")
        value = json.loads(raw)
        if not isinstance(value, dict) or canonical_json(value) != raw:
            raise ControlledOperationalBootstrapError("STRICT_CANONICAL_JSON_REQUIRED")
        validate_safe(value)
        _exact(value, ControlledOperationalBootstrapRequest)
        artifacts = value.get("artifacts")
        policy = value.get("time_policy")
        if not isinstance(artifacts, dict) or not isinstance(policy, dict):
            raise ControlledOperationalBootstrapError("REQUEST_FIELDS_INVALID")
        _exact(artifacts, ControlledOperationalBootstrapArtifactPaths)
        _exact(policy, ControlledOperationalBootstrapTimePolicy)
        value["artifacts"] = ControlledOperationalBootstrapArtifactPaths(**artifacts)
        value["time_policy"] = ControlledOperationalBootstrapTimePolicy(**policy)
        value["scope"] = ControlledOperationalBootstrapScope(value["scope"])
        value["restriction_acknowledgement_digests"] = tuple(
            value["restriction_acknowledgement_digests"])
        value["active_restriction_digests"] = tuple(value["active_restriction_digests"])
        return ControlledOperationalBootstrapRequest(**value)


class ControlledOperationalBootstrapArtifactValidator:
    def validate(self, *, request, approval, preflight, git, host, now: str) -> None:
        required_approval = {
            "status", "approved_at", "requester_identity", "operator_identity",
            "independent_approver_identity", "branch", "commit",
            "restriction_acknowledgement_digests", "synthetic", "production_authorized"}
        required_preflight = {
            "status", "branch", "commit", "trusted_operational_root",
            "managed_targets_absent", "shared_parent_digest", "ubuntu_participation"}
        if set(approval) != required_approval or set(preflight) != required_preflight:
            raise ControlledOperationalBootstrapError("ARTIFACT_FIELDS_INVALID")
        if (approval["status"] != "APPROVED" or approval["synthetic"]
                or approval["production_authorized"]):
            raise ControlledOperationalBootstrapError("APPROVAL_INVALID")
        if (approval["requester_identity"] != request.requester_identity
                or approval["operator_identity"] != request.operator_identity
                or approval["independent_approver_identity"]
                != request.independent_approver_identity
                or approval["branch"] != request.branch or approval["commit"] != request.commit
                or tuple(sorted(approval["restriction_acknowledgement_digests"]))
                != request.restriction_acknowledgement_digests):
            raise ControlledOperationalBootstrapError("APPROVAL_BINDING_INVALID")
        current = parse_timestamp(now)
        approved = parse_timestamp(str(approval["approved_at"]))
        if current < approved or (current - approved).total_seconds() > (
                request.time_policy.approval_maximum_age_seconds):
            raise ControlledOperationalBootstrapError("APPROVAL_EXPIRED")
        if (preflight["status"] not in {"PASS", "READY_WITH_RESTRICTIONS"}
                or preflight["branch"] != request.branch
                or preflight["commit"] != request.commit
                or preflight["trusted_operational_root"] != str(request.trusted_operational_root)
                or not preflight["managed_targets_absent"]
                or preflight["ubuntu_participation"]):
            raise ControlledOperationalBootstrapError("PREFLIGHT_BINDING_INVALID")
        if not isinstance(git, ReadOnlyGitEvidenceSnapshot):
            raise ControlledOperationalBootstrapError("GIT_BINDING_INVALID")
        git_report = ReadOnlyGitEvidenceValidator().validate(
            git, ReadOnlyGitEvidenceConfig(
                repository_root=git.repository_root,
                expected_branch=request.branch, expected_commit=request.commit))
        if git_report.status is not ReadOnlyGitEvidenceStatus.COMPLETE:
            raise ControlledOperationalBootstrapError("GIT_BINDING_INVALID")
        if (host.get("system") != "Darwin" or host.get("uid") in {None, 0}
                or host.get("operator_identity") != request.operator_identity
                or host.get("trusted_operational_root") != str(request.trusted_operational_root)):
            raise ControlledOperationalBootstrapError("TRUSTED_MAC_NON_ROOT_REQUIRED")

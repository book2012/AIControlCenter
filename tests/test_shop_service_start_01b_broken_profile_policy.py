from __future__ import annotations

import ast
import json
from dataclasses import fields
from pathlib import Path

from core.infrastructure.profile_recovery import (
    EvidenceState,
    MutationCandidate,
    ProfileHealth,
    ProfileHealthFacts,
    RecoveryEvidence,
    RecoveryOutcome,
    SHOPPING_PROFILE,
    SHOPPING_STATE_VOLUMES,
    decide_profile_recovery,
)
from core.shopping.observability.service_start import ServiceStartState


ROOT = Path(__file__).resolve().parents[1]


def facts(
    health: ProfileHealth,
    *,
    exists: bool | None = True,
    running: bool | None = False,
) -> ProfileHealthFacts:
    return ProfileHealthFacts(
        profile=SHOPPING_PROFILE,
        exists=exists,
        raw_inventory_status="externally-supplied-diagnostic",
        runtime_running=running,
        health=health,
    )


def test_broken_is_separate_from_shopping_stopped_state() -> None:
    assert ProfileHealth.BROKEN.value not in {state.value for state in ServiceStartState}
    assert decide_profile_recovery(
        facts(ProfileHealth.BROKEN), RecoveryEvidence()
    ).candidate is None


def test_unknown_selects_no_mutation() -> None:
    decision = decide_profile_recovery(facts(ProfileHealth.UNKNOWN), RecoveryEvidence())
    assert decision.outcome is RecoveryOutcome.MUTATION_UNDETERMINED
    assert decision.candidate is None


def test_healthy_stopped_requires_independent_lifecycle_only_proof() -> None:
    decision = decide_profile_recovery(facts(ProfileHealth.HEALTHY), RecoveryEvidence())
    assert decision.outcome is RecoveryOutcome.RECOVERY_EVIDENCE_REQUIRED
    assert decision.candidate is None


def test_healthy_stopped_can_classify_only_a_start_candidate() -> None:
    decision = decide_profile_recovery(
        facts(ProfileHealth.HEALTHY),
        RecoveryEvidence(lifecycle_only_start=EvidenceState.PROVEN),
    )
    assert decision.outcome is RecoveryOutcome.READY_FOR_LIFECYCLE_START
    assert decision.candidate is MutationCandidate.START_EXISTING_PROFILE_ONCE
    assert decision.destructive_recovery_available is False
    assert decision.to_json_safe()["mutation_selected"] is False


def test_broken_never_selects_recreation_and_unknown_storage_fails_closed() -> None:
    decision = decide_profile_recovery(
        facts(ProfileHealth.BROKEN),
        RecoveryEvidence(storage_preservation=EvidenceState.UNKNOWN),
    )
    assert decision.outcome is RecoveryOutcome.STORAGE_PRESERVATION_REQUIRED
    assert decision.candidate is None
    assert decision.destructive_recovery_available is False
    assert decision.to_json_safe()["mutation_selected"] is False


def test_broken_storage_preservation_is_safety_evidence_not_authority() -> None:
    decision = decide_profile_recovery(
        facts(ProfileHealth.BROKEN),
        RecoveryEvidence(storage_preservation=EvidenceState.PROVEN),
    )
    assert decision.storage_protection_evidence_satisfied is True
    assert decision.destructive_recovery_available is False
    assert decision.candidate is None
    projection = decision.to_json_safe()
    assert projection["storage_protection_evidence_satisfied"] is True
    assert projection["mutation_selected"] is False


def test_broken_verified_backup_restore_is_safety_evidence_not_authority() -> None:
    decision = decide_profile_recovery(
        facts(ProfileHealth.BROKEN),
        RecoveryEvidence(verified_backup_restore=EvidenceState.PROVEN),
    )
    assert decision.storage_protection_evidence_satisfied is True
    assert decision.destructive_recovery_available is False
    assert decision.candidate is None


def test_unknown_storage_protection_proof_exposes_no_mutation_candidate() -> None:
    decision = decide_profile_recovery(
        facts(ProfileHealth.UNKNOWN),
        RecoveryEvidence(storage_preservation=EvidenceState.PROVEN),
    )
    assert decision.storage_protection_evidence_satisfied is True
    assert decision.destructive_recovery_available is False
    assert decision.candidate is None


def test_mutation_candidate_contract_contains_no_destructive_operation() -> None:
    assert {candidate.value for candidate in MutationCandidate} == {
        "START_EXISTING_PROFILE_ONCE"
    }


def test_destructive_recovery_is_unavailable_for_every_current_outcome() -> None:
    cases = (
        (facts(ProfileHealth.HEALTHY), RecoveryEvidence()),
        (
            facts(ProfileHealth.HEALTHY),
            RecoveryEvidence(lifecycle_only_start=EvidenceState.PROVEN),
        ),
        (facts(ProfileHealth.HEALTHY, running=True), RecoveryEvidence()),
        (facts(ProfileHealth.BROKEN), RecoveryEvidence()),
        (
            facts(ProfileHealth.BROKEN),
            RecoveryEvidence(storage_preservation=EvidenceState.PROVEN),
        ),
        (facts(ProfileHealth.UNKNOWN), RecoveryEvidence()),
        (facts(ProfileHealth.HEALTHY, exists=None), RecoveryEvidence()),
        (facts(ProfileHealth.HEALTHY, exists=False), RecoveryEvidence()),
    )
    assert {
        decide_profile_recovery(case_facts, evidence).outcome
        for case_facts, evidence in cases
    } == set(RecoveryOutcome)
    assert all(
        decide_profile_recovery(case_facts, evidence).destructive_recovery_available
        is False
        for case_facts, evidence in cases
    )


def test_storage_policy_names_only_canonical_persistent_state() -> None:
    assert SHOPPING_STATE_VOLUMES == (
        "ai-shopping-database",
        "ai-shopping-wordpress",
    )


def test_identity_authority_retry_and_deterministic_json_contract() -> None:
    assert SHOPPING_PROFILE == "aicontrolcenter-commerce"
    decision = decide_profile_recovery(facts(ProfileHealth.BROKEN), RecoveryEvidence())
    first = json.dumps(decision.to_json_safe(), sort_keys=True, separators=(",", ":"))
    second = json.dumps(decision.to_json_safe(), sort_keys=True, separators=(",", ":"))
    assert first == second
    projection = decision.to_json_safe()
    assert projection["production_authority"] is False
    assert projection["ubuntu_authority"] is False
    assert projection["automatic_retry"] is False


def test_policy_layer_contains_no_process_or_command_surface() -> None:
    path = ROOT / "core/infrastructure/profile_recovery.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports = {
        node.names[0].name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
    }
    names = {field.name for field in fields(ProfileHealthFacts)}
    names.update(field.name for field in fields(RecoveryEvidence))
    names.update(field.name for field in fields(type(decide_profile_recovery(
        facts(ProfileHealth.UNKNOWN), RecoveryEvidence()
    ))))
    assert not imports & {"subprocess", "os", "shlex"}
    assert not names & {
        "command",
        "argv",
        "shell",
        "authorization",
        "subprocess",
        "runtime_mutation",
    }

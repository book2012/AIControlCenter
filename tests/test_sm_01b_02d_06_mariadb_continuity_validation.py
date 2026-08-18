import ast
import dataclasses
import json
import subprocess
from pathlib import Path

import pytest

from core.secrets.mariadb_continuity_validation import (
    AccountProfile,
    ConsumerCompatibility,
    ContinuityBaselineProfile,
    DataIdentityProfile,
    DatabaseProfile,
    GrantsProfile,
    MariaDBContinuityValidationRequest,
    MariaDBContinuityValidationResult,
    MariaDBContinuityValidationService,
    TargetProfile,
    ValidationFact,
    ValidationOutcome,
    ValidationProfile,
    ValidationReasonCode,
)


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_FILES = (
    ROOT / "core/secrets/mariadb_continuity_validation.py",
    ROOT / "core/secrets/mariadb_continuity_validation_port.py",
    ROOT / "ops/macos/shopping/mariadb_continuity_validation_adapter.py",
)
EXPECTED_ACTIONS = {
    "SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE",
    "SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE",
    "SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE",
    "SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE",
    "SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE",
    "SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE",
}
PROVISIONING_SOURCES = (
    ROOT / "core/governance/control_plane/application/shopping_provisioning_coordinator.py",
    ROOT / "ops/macos/shopping/secret_provisioning_adapters.py",
)


def request():
    return MariaDBContinuityValidationRequest.canonical()


def result(outcome, count, facts, reason, compatibility=ConsumerCompatibility.NOT_EVALUATED):
    return MariaDBContinuityValidationResult(
        outcome=outcome,
        attempted_count=count,
        request=request(),
        credential_acceptance=facts[0],
        expected_database_identity=facts[1],
        expected_account_identity=facts[2],
        required_grants=facts[3],
        data_identity=facts[4],
        data_continuity=facts[5],
        consumer_compatibility=compatibility,
        reason_code=reason,
    )


def test_outcome_vocabulary_is_exact():
    assert {item.value for item in ValidationOutcome} == {
        "VALIDATED", "REJECTED", "UNAVAILABLE", "UNSAFE", "MALFORMED", "UNCERTAIN",
    }


def test_request_is_closed_value_free_and_result_is_frozen_slotted():
    expected_types = {
        "target": TargetProfile,
        "account_profile": AccountProfile,
        "database_profile": DatabaseProfile,
        "grants_profile": GrantsProfile,
        "data_identity_profile": DataIdentityProfile,
        "continuity_baseline_profile": ContinuityBaselineProfile,
        "validation_profile": ValidationProfile,
    }
    assert {field.name: field.type for field in dataclasses.fields(request())} == expected_types
    assert [field.name for field in dataclasses.fields(MariaDBContinuityValidationResult)] == [
        "outcome", "attempted_count", "request", "credential_acceptance",
        "expected_database_identity", "expected_account_identity", "required_grants",
        "data_identity", "data_continuity", "consumer_compatibility", "reason_code",
    ]
    assert not hasattr(request(), "__dict__")
    assert not hasattr(result(
        ValidationOutcome.VALIDATED, 1, (ValidationFact.CONFIRMED,) * 6,
        ValidationReasonCode.ALL_MANDATORY_FACTS_CONFIRMED,
    ), "__dict__")
    with pytest.raises(dataclasses.FrozenInstanceError):
        request().target = TargetProfile.SHOPPING_SECRET_PROVISIONING


def test_validated_requires_every_mandatory_fact_and_one_attempt():
    validated = result(
        ValidationOutcome.VALIDATED, 1, (ValidationFact.CONFIRMED,) * 6,
        ValidationReasonCode.ALL_MANDATORY_FACTS_CONFIRMED,
    )
    assert validated.attempted_count == 1
    assert all(fact is ValidationFact.CONFIRMED for fact in validated.mandatory_facts)
    incomplete = (ValidationFact.CONFIRMED,) * 5 + (ValidationFact.NOT_EVALUATED,)
    with pytest.raises(ValueError):
        result(ValidationOutcome.VALIDATED, 1, incomplete,
               ValidationReasonCode.ALL_MANDATORY_FACTS_CONFIRMED)


@pytest.mark.parametrize(
    ("outcome", "count", "facts", "reason"),
    (
        (ValidationOutcome.VALIDATED, 0, (ValidationFact.CONFIRMED,) * 6,
         ValidationReasonCode.ALL_MANDATORY_FACTS_CONFIRMED),
        (ValidationOutcome.REJECTED, 0,
         (ValidationFact.REJECTED,) + (ValidationFact.NOT_EVALUATED,) * 5,
         ValidationReasonCode.CREDENTIAL_EXPLICITLY_REJECTED),
        (ValidationOutcome.REJECTED, 1,
         (ValidationFact.REJECTED, ValidationFact.CONFIRMED) + (ValidationFact.NOT_EVALUATED,) * 4,
         ValidationReasonCode.CREDENTIAL_EXPLICITLY_REJECTED),
        (ValidationOutcome.UNAVAILABLE, 1, (ValidationFact.NOT_EVALUATED,) * 6,
         ValidationReasonCode.CAPABILITY_UNAVAILABLE_BEFORE_ATTEMPT),
        (ValidationOutcome.UNSAFE, 1, (ValidationFact.NOT_EVALUATED,) * 6,
         ValidationReasonCode.VALIDATION_PRECONDITION_UNSAFE),
        (ValidationOutcome.MALFORMED, 1, (ValidationFact.NOT_EVALUATED,) * 6,
         ValidationReasonCode.CAPABILITY_OBSERVATION_MALFORMED),
        (ValidationOutcome.UNCERTAIN, 0,
         (ValidationFact.UNCERTAIN,) + (ValidationFact.NOT_EVALUATED,) * 5,
         ValidationReasonCode.ATTEMPT_RESULT_UNCERTAIN),
        (ValidationOutcome.UNCERTAIN, 1,
         (ValidationFact.CONFIRMED,) + (ValidationFact.NOT_EVALUATED,) * 5,
         ValidationReasonCode.ATTEMPT_RESULT_UNCERTAIN),
    ),
)
def test_direct_result_construction_rejects_contradictions(outcome, count, facts, reason):
    with pytest.raises(ValueError):
        result(outcome, count, facts, reason)


def test_result_rejects_wrong_reason_compatibility_and_attempt_range():
    facts = (ValidationFact.CONFIRMED,) * 6
    with pytest.raises(ValueError):
        result(ValidationOutcome.VALIDATED, 1, facts,
               ValidationReasonCode.ATTEMPT_RESULT_UNCERTAIN)
    with pytest.raises(ValueError):
        result(ValidationOutcome.VALIDATED, 1, facts,
               ValidationReasonCode.ALL_MANDATORY_FACTS_CONFIRMED, "EVALUATED")
    for count in (-1, 2, True):
        with pytest.raises(ValueError):
            result(ValidationOutcome.VALIDATED, count, facts,
                   ValidationReasonCode.ALL_MANDATORY_FACTS_CONFIRMED)


def test_legitimate_partial_uncertain_preserves_confirmed_facts():
    observed = result(
        ValidationOutcome.UNCERTAIN, 1,
        (ValidationFact.CONFIRMED, ValidationFact.CONFIRMED,
         ValidationFact.UNCERTAIN, ValidationFact.NOT_EVALUATED,
         ValidationFact.NOT_EVALUATED, ValidationFact.NOT_EVALUATED),
        ValidationReasonCode.ATTEMPT_RESULT_UNCERTAIN,
    )
    assert observed.credential_acceptance is ValidationFact.CONFIRMED


@pytest.mark.parametrize(
    ("outcome", "count", "facts", "reason"),
    (
        (ValidationOutcome.REJECTED, 1,
         (ValidationFact.REJECTED,) + (ValidationFact.NOT_EVALUATED,) * 5,
         ValidationReasonCode.CREDENTIAL_EXPLICITLY_REJECTED),
        (ValidationOutcome.UNAVAILABLE, 0, (ValidationFact.NOT_EVALUATED,) * 6,
         ValidationReasonCode.CAPABILITY_UNAVAILABLE_BEFORE_ATTEMPT),
        (ValidationOutcome.UNSAFE, 0, (ValidationFact.NOT_EVALUATED,) * 6,
         ValidationReasonCode.VALIDATION_PRECONDITION_UNSAFE),
        (ValidationOutcome.MALFORMED, 0, (ValidationFact.NOT_EVALUATED,) * 6,
         ValidationReasonCode.CAPABILITY_OBSERVATION_MALFORMED),
        (ValidationOutcome.UNCERTAIN, 1,
         (ValidationFact.UNCERTAIN,) + (ValidationFact.NOT_EVALUATED,) * 5,
         ValidationReasonCode.ATTEMPT_RESULT_UNCERTAIN),
    ),
)
def test_closed_outcome_invariants(outcome, count, facts, reason):
    observed = result(outcome, count, facts, reason)
    assert observed.outcome is outcome
    contradictory_count = 1 - count
    with pytest.raises(ValueError):
        result(outcome, contradictory_count, facts, reason)


def test_projection_is_deterministic_json_safe_and_zero_authority():
    observed = result(
        ValidationOutcome.VALIDATED, 1, (ValidationFact.CONFIRMED,) * 6,
        ValidationReasonCode.ALL_MANDATORY_FACTS_CONFIRMED,
    )
    first = observed.to_projection()
    assert json.dumps(first, sort_keys=True) == json.dumps(observed.to_projection(), sort_keys=True)
    assert first["mutation_authority"] is False
    assert first["authorization_authority"] is False
    assert first["retry_prohibited"] is True
    assert first["value_free"] is True
    assert first["secret_values_read"] is False
    assert first["facts"]["consumer_compatibility"] == "NOT_EVALUATED"
    forbidden = {
        "password", "secret", "username", "host", "port", "path", "dsn", "url",
        "sql", "command", "argv", "executable", "callback", "authorization",
        "authorization_id", "capability", "capability_id", "mutation_budget",
        "execution_request", "execution_receipt", "replay_token", "candidate", "fallback",
    }
    keys = set()
    def collect(value):
        if isinstance(value, dict):
            assert all(type(key) is str for key in value)
            keys.update(value)
            for child in value.values(): collect(child)
        elif isinstance(value, list):
            for child in value: collect(child)
        else:
            assert type(value) in {str, bool, int, float, type(None)}
    collect(first)
    assert not (keys & forbidden)


def test_service_delegates_exactly_once_and_rejects_wrong_result_type():
    class FakePort:
        calls = 0
        def validate_once(self, factual_request, capability):
            self.calls += 1
            return result(
                ValidationOutcome.UNAVAILABLE, 0, (ValidationFact.NOT_EVALUATED,) * 6,
                ValidationReasonCode.CAPABILITY_UNAVAILABLE_BEFORE_ATTEMPT,
            )
    port = FakePort()
    service = MariaDBContinuityValidationService(port)
    assert service.validate_once(request(), object()).outcome is ValidationOutcome.UNAVAILABLE
    assert port.calls == 1

    class BadPort:
        def validate_once(self, factual_request, capability): return {}
    with pytest.raises(TypeError):
        MariaDBContinuityValidationService(BadPort()).validate_once(request(), object())


def test_production_modules_have_no_forbidden_imports_or_capability_factory():
    forbidden_roots = {
        "os", "subprocess", "pathlib", "sqlite3", "socket", "requests", "urllib",
        "docker", "pymysql", "MySQLdb", "mysql", "mariadb", "sqlalchemy",
    }
    forbidden_fragments = {
        "GovernanceAuthorization", "AuthorizationConsumptionPort", "GovernanceMutationBudget",
        "GovernanceExecutionRequest", "GovernanceExecutionReceipt", "ControlledExecutionPort",
        "ShoppingProvisioningGovernanceCoordinator",
    }
    for path in PRODUCTION_FILES:
        source = path.read_text()
        tree = ast.parse(source)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        assert not (imported & forbidden_roots)
        assert not any(fragment in source for fragment in forbidden_fragments)
        assert "core.governance.control_plane" not in source
        assert "shopping_provisioning_coordinator" not in source
        assert "secret_provisioning_adapters" not in source
    core_tree = ast.parse(PRODUCTION_FILES[0].read_text())
    assert not any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and ("capability" in node.name.lower() or "authoriz" in node.name.lower())
        for node in ast.walk(core_tree)
    )


def test_request_result_and_projection_never_contain_capability():
    assert "capability" not in {field.name for field in dataclasses.fields(request())}
    assert "capability" not in {
        field.name for field in dataclasses.fields(MariaDBContinuityValidationResult)
    }
    projected = result(
        ValidationOutcome.VALIDATED, 1, (ValidationFact.CONFIRMED,) * 6,
        ValidationReasonCode.ALL_MANDATORY_FACTS_CONFIRMED,
    ).to_projection()
    assert "capability" not in json.dumps(projected, sort_keys=True).lower()


def test_exact_six_existing_provisioning_actions_are_preserved():
    for path in PROVISIONING_SOURCES:
        strings = {
            node.value for node in ast.walk(ast.parse(path.read_text()))
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
            and node.value.startswith("SHOPPING_SECRET_") and ":" in node.value
        }
        assert strings == EXPECTED_ACTIONS
    subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--", *(str(path.relative_to(ROOT)) for path in PROVISIONING_SOURCES)],
        cwd=ROOT, check=True,
    )


def test_sm_01b_02d_05_and_config_are_unchanged_from_head():
    subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--", "core/secrets/mariadb_continuity.py"],
        cwd=ROOT, check=True,
    )
    subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--", "config/"], cwd=ROOT, check=True,
    )

import ast
import json
from dataclasses import asdict
from pathlib import Path

import pytest

from core.secrets.mariadb_continuity_concrete_validator import (
    BindingState,
    ExpectedValidationBinding,
    FixedReadOnlyQueryPlan,
    ObservationFact,
    QueryPlanState,
    SanitizedValidationObservation,
    canonical_expected_validation_binding,
    canonical_fixed_read_only_query_plan,
    decide_validation,
    is_safe_read_only_sql,
)
from core.secrets.mariadb_continuity_sources import (
    ContinuityEvidenceCategory,
    DataIdentityCategory,
)
from core.secrets.mariadb_continuity_validation import ValidationOutcome
from ops.macos.shopping.mariadb_continuity_concrete_validator_adapter import (
    MacPyMySQLContinuityValidatorAdapter,
)


ROOT = Path(__file__).parents[1]
CORE = ROOT / "core/secrets/mariadb_continuity_concrete_validator.py"
ADAPTER = ROOT / "ops/macos/shopping/mariadb_continuity_concrete_validator_adapter.py"
ARCH = ROOT / "docs/architecture/MACRO-WU-08-CONCRETE-MARIADB-CONTINUITY-VALIDATOR-PREPARATION.md"


def observation(fact: ObservationFact = ObservationFact.MATCH) -> SanitizedValidationObservation:
    return SanitizedValidationObservation(
        credential_authentication=fact,
        database_identity=fact,
        account_identity=fact,
        required_grants=fact,
        data_identity=tuple((category, fact) for category in DataIdentityCategory),
        continuity_lineage=tuple((category, fact) for category in ContinuityEvidenceCategory),
        continuity_baseline=fact,
    )


def synthetic_ready_contracts(sql: str = "SELECT 1") -> tuple[ExpectedValidationBinding, FixedReadOnlyQueryPlan]:
    """Synthetic test plumbing only; object mutation is explicitly not authority."""
    binding = canonical_expected_validation_binding()
    plan = canonical_fixed_read_only_query_plan()
    object.__setattr__(binding, "state", BindingState.COMPLETE)
    object.__setattr__(plan, "state", QueryPlanState.READY)
    object.__setattr__(plan, "statements", (sql,))
    return binding, plan


class FakeDriver:
    def __init__(self, result: object = None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.calls = 0
        self.seen_secret = None

    def observe_once(self, binding, plan, secret):
        self.calls += 1
        self.seen_secret = secret
        if self.error:
            raise self.error
        return self.result


def test_exact_terminal_outcome_set_and_authoritative_categories() -> None:
    assert {item.value for item in ValidationOutcome} == {
        "VALIDATED", "REJECTED", "UNAVAILABLE", "UNSAFE", "MALFORMED", "UNCERTAIN"
    }
    binding = canonical_expected_validation_binding()
    assert binding.data_categories == tuple(DataIdentityCategory)
    assert [item.value for item in binding.data_categories] == [
        "WORDPRESS_IDENTITY", "SITE_IDENTITY", "APPLICATION_IDENTITY",
        "CLOSED_SCHEMA_CHARACTERISTICS", "CLOSED_TABLE_CHARACTERISTICS",
    ]
    assert binding.lineage_categories == tuple(ContinuityEvidenceCategory)
    assert [item.value for item in binding.lineage_categories] == [
        "LOGICAL_EXPORT", "RECOVERY_ARTIFACT", "PERSISTENT_VOLUME_SNAPSHOT"
    ]


def test_validated_requires_every_required_fact() -> None:
    assert decide_validation(observation()).outcome is ValidationOutcome.VALIDATED
    for field in ("credential_authentication", "database_identity", "account_identity", "required_grants", "continuity_baseline"):
        values = observation()
        object.__setattr__(values, field, ObservationFact.MISSING)
        assert decide_validation(values).outcome is ValidationOutcome.UNCERTAIN
    values = observation()
    object.__setattr__(values, "data_identity", values.data_identity[:-1])
    assert decide_validation(values).outcome is ValidationOutcome.MALFORMED
    values = observation()
    object.__setattr__(values, "continuity_lineage", values.continuity_lineage[:-1])
    assert decide_validation(values).outcome is ValidationOutcome.MALFORMED


def test_mismatch_ambiguity_and_malformed_inputs_fail_closed() -> None:
    assert decide_validation(observation(ObservationFact.MISMATCH)).outcome is ValidationOutcome.REJECTED
    assert decide_validation(observation(ObservationFact.AMBIGUOUS)).outcome is ValidationOutcome.UNCERTAIN
    assert decide_validation(object()).outcome is ValidationOutcome.MALFORMED
    duplicate = observation()
    object.__setattr__(duplicate, "data_identity", (duplicate.data_identity[0],) * 5)
    assert decide_validation(duplicate).outcome is ValidationOutcome.MALFORMED


@pytest.mark.parametrize("sql", [
    "INSERT INTO x VALUES (1)", "UPDATE x SET y=1", "DELETE FROM x", "SET @x=1",
    "CREATE TABLE x(y INT)", "ALTER TABLE x ADD y INT", "DROP TABLE x", "GRANT SELECT ON x TO y",
    "REVOKE SELECT ON x FROM y", "FLUSH PRIVILEGES", "LOCK TABLES x READ", "UNLOCK TABLES",
    "CALL p()", "LOAD DATA INFILE 'x' INTO TABLE y", "SELECT 1 INTO OUTFILE 'x'",
    "SELECT 1; DELETE FROM x", "SELECT 1 -- ambiguous", "SELECT /* comment */ 1",
])
def test_mutation_or_ambiguous_sql_is_rejected(sql: str) -> None:
    assert is_safe_read_only_sql(sql) is False


@pytest.mark.parametrize(("sql", "expected"), [
    ("SELECT 1", True),
    ("SELECT 1;", True),
    ("SELECT 1;   ", True),
    ("SELECT 1;;", False),
    ("SELECT 1; ;", False),
    ("SELECT 1; DELETE FROM x", False),
])
def test_only_one_optional_trailing_semicolon_is_allowed(sql: str, expected: bool) -> None:
    assert is_safe_read_only_sql(sql) is expected


def test_canonical_missing_plan_is_unavailable_and_unsafe_plan_never_invokes() -> None:
    driver = FakeDriver(observation())
    adapter = MacPyMySQLContinuityValidatorAdapter(driver)
    result = adapter.validate_once(canonical_expected_validation_binding(), canonical_fixed_read_only_query_plan(), object())
    assert result.outcome is ValidationOutcome.UNAVAILABLE
    assert driver.calls == 0
    binding, plan = synthetic_ready_contracts("DELETE FROM x")
    result = adapter.validate_once(binding, plan, object())
    assert result.outcome is ValidationOutcome.UNSAFE
    assert driver.calls == 0


def test_exactly_one_invocation_success_and_sanitized_failure_without_secret_retention() -> None:
    secret = "synthetic-wu08-secret"
    binding, plan = synthetic_ready_contracts()
    success = FakeDriver(observation())
    result = MacPyMySQLContinuityValidatorAdapter(success).validate_once(binding, plan, secret)
    assert result.outcome is ValidationOutcome.VALIDATED
    assert success.calls == 1 and success.seen_secret is secret
    assert secret not in repr(result)
    assert secret not in json.dumps(result.to_projection())
    assert secret not in json.dumps(asdict(result))

    failure = FakeDriver(error=RuntimeError(f"driver leaked {secret}"))
    result = MacPyMySQLContinuityValidatorAdapter(failure).validate_once(binding, plan, secret)
    assert result.outcome is ValidationOutcome.UNCERTAIN
    assert failure.calls == 1
    assert result.reason == "SANITIZED_DRIVER_FAILURE"
    assert secret not in repr(result) + json.dumps(result.to_projection())


def test_no_retry_environment_governance_or_controlled_execution_coupling() -> None:
    sources = (CORE.read_text(), ADAPTER.read_text())
    trees = tuple(ast.parse(source) for source in sources)
    imported = set()
    for tree in trees:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
    assert not any(name.startswith("core.governance") for name in imported)
    joined = "\n".join(sources).lower()
    for forbidden in ("authorizationconsumptionport", "controlledexecutionport", "os.environ", "getenv(", "ubuntu", "docker", "colima"):
        assert forbidden not in joined
    assert not any(
        token in name.lower()
        for name in imported
        for token in ("wordpress", "woocommerce", "composition")
    )
    function_names = {
        node.name.lower() for tree in trees for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert function_names.isdisjoint({"retry", "reconnect", "fallback", "discover", "enumerate_candidates", "recover", "rollback", "compensate"})
    assert "while" not in {type(node).__name__.lower() for tree in trees for node in ast.walk(tree)}


def test_no_production_composition_or_ubuntu_implementation_and_architecture_truth() -> None:
    changed_runtime_names = {CORE.name, ADAPTER.name}
    assert not any("ubuntu" in name.lower() or "composition" in name.lower() for name in changed_runtime_names)
    text = ARCH.read_text()
    for fact in (
        "PRODUCTION_ACCESS_PERFORMED=false", "PROTECTED_SOURCE_ACCESS_PERFORMED=false",
        "CREDENTIAL_VALIDATION_PERFORMED=false", "MARIADB_CONNECTION_PERFORMED=false",
        "SQL_EXECUTION_PERFORMED=false", "PRODUCTION_AUTHORIZATION_CONSUMED=false",
        "PRODUCTION_VALIDATION_AVAILABLE=false", "RECOVER_EVIDENCE_SUFFICIENT=false",
        "RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT",
    ):
        assert fact in text


def test_existing_contracts_remain_semantically_separate() -> None:
    imported_modules = {
        node.module
        for path in (CORE, ADAPTER)
        for node in ast.walk(ast.parse(path.read_text()))
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "core.secrets.mariadb_continuity_offline_historical_evidence_evaluator" not in imported_modules
    assert "ops.macos.shopping.mariadb_continuity_pymysql_adapter" not in imported_modules
    assert "core.governance.control_plane.ports.execution" not in imported_modules
    assert "core.governance.control_plane.ports.authorization_consumption" not in imported_modules
    assert (ROOT / "requirements.txt").read_text().splitlines().count("PyMySQL==1.2.0") == 1

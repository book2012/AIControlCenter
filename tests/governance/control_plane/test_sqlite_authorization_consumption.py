"""Durable fail-closed SQLite authorization consumption."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import inspect
from pathlib import Path
import sqlite3
from types import SimpleNamespace

import pytest

from core.governance.control_plane.adapters.sqlite import (
    SQLiteAuthorizationConsumptionAdapter,
    SQLiteAuthorizationConsumptionError,
    SQLiteAuthorizationConsumptionPathPolicy,
    SQLiteOwnershipIdentity,
    SQLitePathPolicyError,
    SQLiteSchemaError,
)
from core.governance.control_plane.adapters.sqlite.codec import digest_canonical, encode_binding
from core.governance.control_plane.adapters.sqlite.schema import APPLICATION_ID, DDL, USER_VERSION
from core.governance.control_plane.application import (
    GovernanceOrchestrationContext, OrchestrationDisposition, decide_next_disposition,
)
from core.governance.control_plane.domain import (
    AuthorizationDecision,
    AuthorizationState,
    GovernanceAuthorization,
    GovernanceAuthorizationDecision,
    GovernanceAuthorizationRequest,
    GovernanceExecutionRequest,
    GovernanceIdentity,
    GovernanceMutationBudget,
    MutationBudgetLineItem,
    MutationBudgetStatus,
    MutationInvocationOutcome,
    PreconditionComparisonResult,
    PreconditionComparisonStatus,
    RepeatedAuthorizationConsumption,
    account_mutation_invocation,
    transition_authorization,
)
from core.governance.control_plane.ports import AuthorizationConsumptionCommand

NOW = datetime(2026, 8, 17, tzinfo=timezone.utc)
REPOSITORY = Path(__file__).resolve().parents[3]


def command(**identity_changes: str) -> AuthorizationConsumptionCommand:
    lifecycle = identity_changes.get("lifecycle_id", "lifecycle-1")
    authorization_id = identity_changes.get("authorization_id", "authorization-1")
    budget_id = identity_changes.get("mutation_budget_id", "budget-1")
    request_id = identity_changes.get("authorization_request_id", "request-1")
    decision_id = identity_changes.get("authorization_decision_id", "decision-1")
    claim_id = identity_changes.get("claim_id", "claim-1")
    execution_id = identity_changes.get("execution_request_id", "execution-1")
    request = GovernanceAuthorizationRequest(
        "1.0.0", request_id, lifecycle, GovernanceIdentity("human", "requester-secret-name"),
        "CONTROLLED_CHANGE", "target-1", "managed", "raw secret reason",
        ("SERVICE_RESTART",), budget_id, NOW,
    )
    decision = GovernanceAuthorizationDecision(
        "1.0.0", decision_id, request_id, GovernanceIdentity("human", "approver-secret-name"),
        AuthorizationDecision.APPROVED, ("POLICY_SATISFIED",), NOW,
        NOW + timedelta(hours=1), ("SERVICE_RESTART",), budget_id, "sha256:snapshot",
    )
    authorization = transition_authorization(
        GovernanceAuthorization(request), AuthorizationState.AUTHORIZED, "APPROVED", NOW,
        decision=decision, authorization_id=authorization_id,
    ).authorization
    budget = GovernanceMutationBudget(
        "1.0.0", budget_id, authorization_id,
        (MutationBudgetLineItem("SERVICE_RESTART", 2),),
    )
    execution = GovernanceExecutionRequest(
        "1.0.0", execution_id, lifecycle, authorization_id, claim_id, budget_id,
        "SERVICE_RESTART", "target-1", "sha256:plan", NOW,
    )
    return AuthorizationConsumptionCommand(authorization, budget, execution)


def adapter(tmp_path: Path, **kwargs: object) -> SQLiteAuthorizationConsumptionAdapter:
    identity = SQLiteOwnershipIdentity(tmp_path.stat().st_uid, tmp_path.stat().st_gid)
    return SQLiteAuthorizationConsumptionAdapter.for_test(
        tmp_path / "evidence.sqlite3", repository_root=REPOSITORY,
        ownership_identity=identity,
        clock=lambda: NOW, **kwargs,  # type: ignore[arg-type]
    )


def rows(path: Path) -> list[tuple[object, ...]]:
    with sqlite3.connect(path) as connection:
        return connection.execute("SELECT * FROM authorization_consumptions").fetchall()


def test_valid_first_consumption_is_exact_zero_count_committed_evidence(tmp_path: Path) -> None:
    result = adapter(tmp_path).consume_once(command())
    assert result.authorization.state is AuthorizationState.CONSUMED
    assert result.mutation_budget.status is MutationBudgetStatus.CONSUMED
    assert all(
        (item.actual_invocation_count, item.completed_count, item.uncertain_count) == (0, 0, 0)
        for item in result.mutation_budget.line_items
    )
    receipt = result.consumption_receipt
    assert (receipt.lifecycle_id, receipt.authorization_id, receipt.mutation_budget_id) == (
        "lifecycle-1", "authorization-1", "budget-1"
    )
    assert (receipt.claim_id, receipt.execution_request_id) == ("claim-1", "execution-1")
    assert rows(tmp_path / "evidence.sqlite3")[0][9] == "COMMITTED"


def test_external_exact_replay_and_fresh_adapter_fail_closed(tmp_path: Path) -> None:
    adapter(tmp_path).consume_once(command())
    with pytest.raises(RepeatedAuthorizationConsumption):
        adapter(tmp_path).consume_once(command())


@pytest.mark.parametrize("field", [
    "lifecycle_id", "authorization_id", "mutation_budget_id", "claim_id",
    "execution_request_id", "authorization_request_id", "authorization_decision_id",
])
def test_every_independently_protected_identifier_conflict_fails_closed(
    tmp_path: Path, field: str
) -> None:
    store = adapter(tmp_path)
    store.consume_once(command())
    changes = {
        name: f"other-{name}" for name in (
            "lifecycle_id", "authorization_id", "mutation_budget_id", "claim_id",
            "execution_request_id", "authorization_request_id", "authorization_decision_id",
        )
    }
    changes[field] = {
        "lifecycle_id": "lifecycle-1", "authorization_id": "authorization-1",
        "mutation_budget_id": "budget-1", "claim_id": "claim-1",
        "execution_request_id": "execution-1", "authorization_request_id": "request-1",
        "authorization_decision_id": "decision-1",
    }[field]
    with pytest.raises(RepeatedAuthorizationConsumption):
        store.consume_once(command(**changes))


def test_binding_digest_is_stable_and_binding_conflict_fails_closed(tmp_path: Path) -> None:
    first = command()
    assert encode_binding(first) == encode_binding(command())
    store = adapter(tmp_path)
    store.consume_once(first)
    changed = command()
    object.__setattr__(changed.execution_request, "plan_digest", "sha256:different")
    with pytest.raises(RepeatedAuthorizationConsumption):
        store.consume_once(changed)


def test_durably_claimed_restart_has_no_recovery_or_claim_stealing(tmp_path: Path) -> None:
    def stop_after_claim(stage: str, _connection: sqlite3.Connection) -> None:
        if stage == "during_final_transaction":
            raise RuntimeError("stop")

    with pytest.raises(RuntimeError):
        adapter(tmp_path, fault=stop_after_claim).consume_once(command())
    assert rows(tmp_path / "evidence.sqlite3")[0][9] == "DURABLY_CLAIMED"
    with pytest.raises(RepeatedAuthorizationConsumption):
        adapter(tmp_path).consume_once(command())
    assert rows(tmp_path / "evidence.sqlite3")[0][9] == "DURABLY_CLAIMED"


def test_failure_before_claim_commit_rolls_back_without_compensation_record(tmp_path: Path) -> None:
    def fail(stage: str, _connection: sqlite3.Connection) -> None:
        if stage == "before_claim_commit":
            raise RuntimeError("before claim commit")

    with pytest.raises(RuntimeError):
        adapter(tmp_path, fault=fail).consume_once(command())
    assert rows(tmp_path / "evidence.sqlite3") == []


def test_failure_during_final_transaction_leaves_irreversible_claim(tmp_path: Path) -> None:
    def fail(stage: str, _connection: sqlite3.Connection) -> None:
        if stage == "during_final_transaction":
            raise RuntimeError("final transaction")

    with pytest.raises(RuntimeError):
        adapter(tmp_path, fault=fail).consume_once(command())
    assert rows(tmp_path / "evidence.sqlite3")[0][9:] == ("DURABLY_CLAIMED", None, None)


def test_ambiguous_commit_reconciles_only_exact_same_call(tmp_path: Path) -> None:
    def ambiguous(stage: str, _connection: sqlite3.Connection) -> None:
        if stage == "after_final_commit":
            raise sqlite3.OperationalError("ack lost")

    result = adapter(tmp_path, fault=ambiguous).consume_once(command())
    assert result.authorization.state is AuthorizationState.CONSUMED
    with pytest.raises(RepeatedAuthorizationConsumption):
        adapter(tmp_path).consume_once(command())


def test_ambiguous_commit_with_tampered_state_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "evidence.sqlite3"

    def ambiguous_and_tamper(stage: str, _connection: sqlite3.Connection) -> None:
        if stage == "after_final_commit":
            with sqlite3.connect(path) as independent:
                independent.execute(
                    "UPDATE authorization_consumptions SET integrity_hash='sha256:tampered'"
                )
            raise sqlite3.OperationalError("ack lost")

    with pytest.raises(SQLiteAuthorizationConsumptionError):
        adapter(tmp_path, fault=ambiguous_and_tamper).consume_once(command())
    assert rows(path)[0][-1] == "sha256:tampered"


def test_database_reopen_and_two_instances_observe_same_barrier(tmp_path: Path) -> None:
    first, second = adapter(tmp_path), adapter(tmp_path)
    first.consume_once(command())
    with pytest.raises(RepeatedAuthorizationConsumption):
        second.consume_once(command())


def test_concurrent_duplicate_has_one_success_and_one_fail_closed(tmp_path: Path) -> None:
    first, second = adapter(tmp_path), adapter(tmp_path)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(instance.consume_once, command()) for instance in (first, second)]
    outcomes = []
    for future in futures:
        try:
            future.result()
            outcomes.append("success")
        except RepeatedAuthorizationConsumption:
            outcomes.append("repeated")
    assert sorted(outcomes) == ["repeated", "success"]


def test_schema_mismatch_and_inconsistent_record_fail_closed(tmp_path: Path) -> None:
    store = adapter(tmp_path)
    path = tmp_path / "evidence.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA user_version=99")
    with pytest.raises(SQLiteAuthorizationConsumptionError):
        store.consume_once(command())


@pytest.mark.parametrize("unsafe_ddl", (
    [DDL.replace("lifecycle_id TEXT PRIMARY KEY NOT NULL", "lifecycle_id TEXT NOT NULL")]
    + [
        DDL.replace(f"{column} TEXT NOT NULL UNIQUE", f"{column} TEXT NOT NULL")
        for column in (
            "authorization_id", "mutation_budget_id", "claim_id", "execution_request_id",
            "authorization_request_id", "authorization_decision_id",
        )
    ]
    + [
        DDL.replace(
            "barrier_state TEXT NOT NULL CHECK (barrier_state IN ('DURABLY_CLAIMED', 'COMMITTED'))",
            "barrier_state TEXT NOT NULL",
        ),
        DDL.replace(
            """,
    CHECK (
        (barrier_state = 'DURABLY_CLAIMED' AND committed_json IS NULL AND integrity_hash IS NULL)
        OR
        (barrier_state = 'COMMITTED' AND committed_json IS NOT NULL AND integrity_hash IS NOT NULL)
    )
""",
            "\n",
        ),
        DDL.replace("mutation_budget_id TEXT NOT NULL UNIQUE", "mutation_budget_id TEXT UNIQUE"),
        DDL.replace(") STRICT;", ");"),
    ]
))
def test_same_column_unsafe_schema_constraints_are_rejected(
    tmp_path: Path, unsafe_ddl: str
) -> None:
    path = tmp_path / "evidence.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.executescript(unsafe_ddl)
        connection.execute(f"PRAGMA application_id={APPLICATION_ID}")
        connection.execute(f"PRAGMA user_version={USER_VERSION}")
    path.chmod(0o600)
    with pytest.raises(SQLiteSchemaError):
        adapter(tmp_path)


@pytest.mark.parametrize("pragma, value", [("application_id", 17), ("user_version", 99)])
def test_empty_foreign_database_is_never_adopted(
    tmp_path: Path, pragma: str, value: int
) -> None:
    path = tmp_path / "evidence.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute(f"PRAGMA {pragma}={value}")
    path.chmod(0o600)
    with pytest.raises(SQLiteSchemaError):
        adapter(tmp_path)
    with sqlite3.connect(path) as connection:
        assert connection.execute(f"PRAGMA {pragma}").fetchone() == (value,)
        assert connection.execute(
            "SELECT name FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%'"
        ).fetchall() == []


def test_corrupt_committed_integrity_is_never_returned(tmp_path: Path) -> None:
    store = adapter(tmp_path)
    store.consume_once(command())
    with sqlite3.connect(tmp_path / "evidence.sqlite3") as connection:
        connection.execute("UPDATE authorization_consumptions SET integrity_hash='bad'")
    with pytest.raises(RepeatedAuthorizationConsumption):
        store.consume_once(command())


def test_busy_lock_times_out_and_fails_closed(tmp_path: Path) -> None:
    store = adapter(tmp_path, busy_timeout_ms=10)
    with sqlite3.connect(tmp_path / "evidence.sqlite3", isolation_level=None) as lock:
        lock.execute("BEGIN IMMEDIATE")
        with pytest.raises(SQLiteAuthorizationConsumptionError):
            store.consume_once(command())


def test_path_policy_rejects_relative_traversal_repository_and_symlink(tmp_path: Path) -> None:
    identity = SQLiteOwnershipIdentity(tmp_path.stat().st_uid, tmp_path.stat().st_gid)
    policy = SQLiteAuthorizationConsumptionPathPolicy.isolated_test(
        repository_root=REPOSITORY, test_root=tmp_path, ownership_identity=identity
    )
    with pytest.raises(SQLitePathPolicyError):
        policy.validate(Path("relative.sqlite3"))
    with pytest.raises(SQLitePathPolicyError):
        policy.validate(tmp_path / ".." / "escape.sqlite3")
    repo_policy = SQLiteAuthorizationConsumptionPathPolicy.isolated_test(
        repository_root=REPOSITORY, test_root=REPOSITORY, ownership_identity=identity
    )
    with pytest.raises(SQLitePathPolicyError):
        repo_policy.validate(REPOSITORY / "evidence.sqlite3")
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(SQLitePathPolicyError):
        policy.validate(link / "evidence.sqlite3")


def test_production_path_is_portable_mac_application_support(tmp_path: Path) -> None:
    home = tmp_path / "portable-home"
    policy = SQLiteAuthorizationConsumptionPathPolicy.production(
        repository_root=REPOSITORY, home=home,
        ownership_identity=SQLiteOwnershipIdentity(tmp_path.stat().st_uid, tmp_path.stat().st_gid),
    )
    value = policy.production_path()
    assert value == home / "Library/Application Support/AIControlCenter/governance/authorization-consumption.sqlite3"
    assert "/Users/kyouhan" not in inspect.getsource(SQLiteAuthorizationConsumptionPathPolicy)


def production_policy(tmp_path: Path) -> tuple[SQLiteAuthorizationConsumptionPathPolicy, Path, Path]:
    home = tmp_path / "portable-home"
    shared_parent = home / "Library/Application Support/AIControlCenter"
    shared_parent.mkdir(parents=True, mode=0o755)
    shared_parent.chmod(0o755)
    identity = SQLiteOwnershipIdentity(shared_parent.stat().st_uid, shared_parent.stat().st_gid)
    policy = SQLiteAuthorizationConsumptionPathPolicy.production(
        repository_root=REPOSITORY, home=home, ownership_identity=identity
    )
    return policy, shared_parent, policy.production_path()


def test_production_shared_parent_0755_is_accepted_without_mutation(tmp_path: Path) -> None:
    policy, shared_parent, path = production_policy(tmp_path)
    policy.prepare(path)
    assert stat_mode(shared_parent) == 0o755
    assert stat_mode(path.parent) == 0o700


def test_production_missing_shared_parent_fails_without_recursive_creation(tmp_path: Path) -> None:
    home = tmp_path / "missing-home"
    identity = SQLiteOwnershipIdentity(tmp_path.stat().st_uid, tmp_path.stat().st_gid)
    policy = SQLiteAuthorizationConsumptionPathPolicy.production(
        repository_root=REPOSITORY, home=home, ownership_identity=identity
    )
    path = policy.production_path()
    with pytest.raises(SQLitePathPolicyError):
        policy.prepare(path)
    assert not (home / "Library/Application Support/AIControlCenter").exists()


def test_existing_production_governance_0755_fails_closed(tmp_path: Path) -> None:
    policy, _shared_parent, path = production_policy(tmp_path)
    path.parent.mkdir(mode=0o755)
    path.parent.chmod(0o755)
    with pytest.raises(SQLitePathPolicyError):
        policy.prepare(path)


def test_wrong_production_governance_ownership_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    policy, _shared_parent, path = production_policy(tmp_path)
    path.parent.mkdir(mode=0o700)
    original_stat = Path.stat

    def fake_stat(candidate: Path, *, follow_symlinks: bool = True) -> object:
        details = original_stat(candidate, follow_symlinks=follow_symlinks)
        if candidate == path.parent and not follow_symlinks:
            return SimpleNamespace(
                st_uid=details.st_uid + 1, st_gid=details.st_gid, st_mode=details.st_mode
            )
        return details

    monkeypatch.setattr(Path, "stat", fake_stat)
    with pytest.raises(SQLitePathPolicyError, match="ownership"):
        policy.prepare(path)


def test_production_database_is_private_and_owned(tmp_path: Path) -> None:
    policy, _shared_parent, path = production_policy(tmp_path)
    policy.prepare(path)
    path.touch(mode=0o600)
    policy.secure_database(path)
    details = path.stat()
    assert stat_mode(path) == 0o600
    assert (details.st_uid, details.st_gid) == (
        policy.ownership_identity.uid, policy.ownership_identity.gid
    )


def stat_mode(path: Path) -> int:
    return path.stat().st_mode & 0o777


def test_path_policy_rejects_unsafe_governance_permissions_and_database_mode(
    tmp_path: Path
) -> None:
    identity = SQLiteOwnershipIdentity(tmp_path.stat().st_uid, tmp_path.stat().st_gid)
    policy = SQLiteAuthorizationConsumptionPathPolicy.isolated_test(
        repository_root=REPOSITORY, test_root=tmp_path, ownership_identity=identity
    )
    path = tmp_path / "evidence.sqlite3"
    tmp_path.chmod(0o755)
    with pytest.raises(SQLitePathPolicyError):
        policy.prepare(path)
    tmp_path.chmod(0o700)
    path.touch()
    path.chmod(0o644)
    assert stat_mode(path) == 0o644
    with pytest.raises(SQLitePathPolicyError):
        policy.prepare(path)


def test_adapter_creates_private_owned_database(tmp_path: Path) -> None:
    adapter(tmp_path)
    path = tmp_path / "evidence.sqlite3"
    assert path.stat().st_mode & 0o777 == 0o600
    assert (path.stat().st_uid, path.stat().st_gid) == (
        tmp_path.stat().st_uid, tmp_path.stat().st_gid
    )


def test_canonical_receipt_hash_has_structural_identifier_boundaries() -> None:
    first = {"identifiers": ["alpha|beta", "gamma"], "consumed_at": NOW.isoformat()}
    second = {"identifiers": ["alpha", "beta|gamma"], "consumed_at": NOW.isoformat()}
    assert "|".join(first["identifiers"]) == "|".join(second["identifiers"])
    assert digest_canonical(first) != digest_canonical(second)


def test_persisted_representation_is_value_free_and_has_no_forbidden_tokens(tmp_path: Path) -> None:
    adapter(tmp_path).consume_once(command())
    content = (tmp_path / "evidence.sqlite3").read_bytes().lower()
    for forbidden in (
        b"raw secret reason", b"requester-secret-name", b"approver-secret-name",
        b"private key", b"credential", b"mariadb", b"argv", b"shell command",
        b"/bin/", b"shopping", b"execution_authority", b"allow_single_invocation",
    ):
        assert forbidden not in content


def test_adapter_has_no_shopping_ops_or_generic_command_surface() -> None:
    source = inspect.getsource(inspect.getmodule(SQLiteAuthorizationConsumptionAdapter))
    lowered = source.lower()
    assert "shopping" not in lowered and "subprocess" not in lowered and "ubuntu" not in lowered
    public = [name for name in vars(SQLiteAuthorizationConsumptionAdapter) if not name.startswith("_")]
    assert public == ["for_test", "consume_once"]
    for forbidden in ("execute", "shell", "argv", "command_text"):
        assert not hasattr(SQLiteAuthorizationConsumptionAdapter, forbidden)


def test_result_does_not_grant_sec02_authority_and_replay_cannot_resurrect_it(tmp_path: Path) -> None:
    store = adapter(tmp_path)
    result = store.consume_once(command())
    assert not hasattr(result, "allow_single_invocation")
    accounted = account_mutation_invocation(
        result.mutation_budget, "SERVICE_RESTART", MutationInvocationOutcome.COMPLETED
    )
    assert accounted.line_items[0].actual_invocation_count == 1
    comparison = PreconditionComparisonResult(
        PreconditionComparisonStatus.MATCH, "snapshot-1", "snapshot-2", (),
        "sha256:snapshot", "sha256:snapshot",
    )
    policy_decision = decide_next_disposition(GovernanceOrchestrationContext(
        authorization=result.authorization,
        precondition_comparison=comparison,
        mutation_budget=accounted,
        consumption_receipt=result.consumption_receipt,
        execution_request=result.execution_request,
        invocation_already_attempted=True,
    ))
    assert policy_decision.disposition is not OrchestrationDisposition.ALLOW_SINGLE_INVOCATION
    with pytest.raises(RepeatedAuthorizationConsumption):
        adapter(tmp_path).consume_once(command())

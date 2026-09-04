from __future__ import annotations

import inspect
import json

import pytest

from core.shopping import wordpress_port_reconciliation as reconciliation
from core.shopping.observability.storage_continuity import (
    DATABASE_DESTINATION,
    DATABASE_VOLUME,
    WORDPRESS_DESTINATION,
    WORDPRESS_VOLUME,
    ContinuityCompleteness,
    ContinuityReason,
    StorageContinuityObservation,
    VolumeContinuitySnapshot,
)
from core.shopping.runtime_cutover_secret_source import (
    PATH_ROLE,
    SOURCE_AUTHORITY,
    SOURCE_ROLE,
    RuntimeCutoverSourceObservation,
    SourceReason,
)


def volume(name: str, destination: str, *, present: bool = True):
    return VolumeContinuitySnapshot(
        name, present, "local", "local", "2026-09-04T00:00:00Z", True,
        destination, destination, "volume",
        "database" if name == DATABASE_VOLUME else "wordpress",
        "shopping-db" if name == DATABASE_VOLUME else "shopping-wordpress",
        ContinuityCompleteness.COMPLETE, ContinuityReason.NONE,
    )


def storage(*items: VolumeContinuitySnapshot) -> StorageContinuityObservation:
    return StorageContinuityObservation(tuple(items) or (
        volume(DATABASE_VOLUME, DATABASE_DESTINATION),
        volume(WORDPRESS_VOLUME, WORDPRESS_DESTINATION),
    ))


def source(*, ready: bool = True) -> RuntimeCutoverSourceObservation:
    return RuntimeCutoverSourceObservation(
        "1.0", SOURCE_AUTHORITY, SOURCE_ROLE, PATH_ROLE, ready, (), (), (), (),
        ready, SourceReason.READY if ready else SourceReason.TRUST_SOURCE_UNAVAILABLE,
    )


def container(*, exists=True, running=True, healthy=True, publishers=()):
    return reconciliation.ContainerRuntimeFact(exists, running, healthy, publishers)


def facts(*, database=None, wordpress=None, volumes=None, reachable=True,
          context=reconciliation.TARGET_CONTEXT,
          project=reconciliation.COMPOSE_PROJECT,
          database_name=reconciliation.DATABASE_CONTAINER,
          wordpress_name=reconciliation.WORDPRESS_CONTAINER):
    return reconciliation.WordPressPortRuntimeFacts(
        context, project, database_name, wordpress_name, reachable,
        database or container(),
        wordpress or container(publishers=(reconciliation.EXPECTED_BEFORE_BINDING,)),
        volumes or storage(),
    )


class OneShotAuthorization:
    def __init__(self, available=True):
        self.available = available
        self.calls = []

    def consume_once(self, mutation_id):
        self.calls.append(mutation_id)
        if not self.available:
            return False
        self.available = False
        return mutation_id == reconciliation.MUTATION_ID


@pytest.fixture(autouse=True)
def fixed_source_observer(monkeypatch):
    monkeypatch.setattr(reconciliation, "observe_runtime_cutover_source", source)


def test_exact_state_is_candidate_but_cannot_execute_without_authorization() -> None:
    decision = reconciliation.classify_reconciliation(facts(), source())
    assert decision.classification is reconciliation.Classification.CANDIDATE
    assert decision.mutation_selected is False
    calls = []
    result = reconciliation.execute_reconciliation(
        observe_runtime=facts, observe_storage=storage, authorization=None,
        runner=lambda invocation: calls.append(invocation),
    )
    assert not result.mutation_executed and calls == []


def test_pure_classifier_has_no_authorization_bool_and_never_selects() -> None:
    parameters = inspect.signature(reconciliation.classify_reconciliation).parameters
    assert "authorization_valid" not in parameters
    decision = reconciliation.classify_reconciliation(facts(), source())
    assert decision.classification is reconciliation.Classification.CANDIDATE
    assert decision.mutation_selected is False
    with pytest.raises(TypeError):
        reconciliation.classify_reconciliation(  # type: ignore[call-arg]
            facts(), source(), authorization_valid=True,
        )


def test_already_desired_selects_no_mutation() -> None:
    current = facts(wordpress=container(publishers=(reconciliation.EXPECTED_AFTER_BINDING,)))
    decision = reconciliation.classify_reconciliation(current, source())
    assert decision.classification is reconciliation.Classification.ALREADY_DESIRED
    assert not decision.mutation_selected


@pytest.mark.parametrize(
    ("current", "reason"),
    [
        (facts(wordpress=container(exists=False)), "WORDPRESS_ABSENT"),
        (facts(wordpress=container(healthy=False)), "WORDPRESS_NOT_HEALTHY"),
        (facts(wordpress=container(publishers=("127.0.0.1:59999->80/tcp",))),
         "WORDPRESS_BINDING_NOT_EXPECTED_BEFORE"),
        (facts(database=container(exists=False)), "DATABASE_ABSENT"),
        (facts(database=container(healthy=False)), "DATABASE_NOT_HEALTHY"),
        (facts(database=container(publishers=("127.0.0.1:3306->3306/tcp",))),
         "DATABASE_HOST_PUBLISHER_PRESENT"),
    ],
)
def test_runtime_preconditions_fail_closed(current, reason) -> None:
    decision = reconciliation.classify_reconciliation(current, source())
    assert decision.classification is reconciliation.Classification.BLOCKED
    assert reason in decision.reason_codes
    assert not decision.mutation_selected


@pytest.mark.parametrize(
    "volumes",
    [
        storage(volume(DATABASE_VOLUME, DATABASE_DESTINATION)),
        storage(volume(WORDPRESS_VOLUME, WORDPRESS_DESTINATION)),
        storage(volume(DATABASE_VOLUME, "/wrong"),
                volume(WORDPRESS_VOLUME, WORDPRESS_DESTINATION)),
        storage(volume(DATABASE_VOLUME, DATABASE_DESTINATION),
                volume(WORDPRESS_VOLUME, "/wrong")),
    ],
)
def test_canonical_volume_absence_or_wrong_destination_fails_closed(volumes) -> None:
    decision = reconciliation.classify_reconciliation(
        facts(volumes=volumes), source(),
    )
    assert decision.classification is reconciliation.Classification.BLOCKED
    assert "CANONICAL_STORAGE_NOT_READY" in decision.reason_codes


def test_volume_attachment_to_wrong_container_fails_closed() -> None:
    wordpress = volume(WORDPRESS_VOLUME, WORDPRESS_DESTINATION)
    wordpress = VolumeContinuitySnapshot(
        wordpress.volume_name, wordpress.present, wordpress.driver,
        wordpress.scope, wordpress.created_at, wordpress.expected_attachment,
        wordpress.expected_destination, wordpress.observed_destination,
        wordpress.attachment_type, wordpress.service, "wrong-container",
        wordpress.completeness, wordpress.reason,
    )
    decision = reconciliation.classify_reconciliation(
        facts(volumes=storage(volume(DATABASE_VOLUME, DATABASE_DESTINATION), wordpress)),
        source(),
    )
    assert decision.classification is reconciliation.Classification.BLOCKED


def test_runtime_cutover_source_must_be_ready() -> None:
    decision = reconciliation.classify_reconciliation(
        facts(), source(ready=False),
    )
    assert decision.classification is reconciliation.Classification.BLOCKED
    assert not decision.mutation_selected


def test_target_and_source_cannot_be_caller_overridden() -> None:
    assert tuple(inspect.signature(reconciliation.build_mutation_invocation).parameters) == ()
    execution_parameters = inspect.signature(reconciliation.execute_reconciliation).parameters
    assert not ({"context", "project", "service", "container", "env_file", "observe_source"}
                & set(execution_parameters))
    assert reconciliation.TARGET_CONTEXT == "colima-aicontrolcenter-commerce"
    assert reconciliation.COMPOSE_PROJECT == "ai-shopping"
    assert reconciliation.COMPOSE_SERVICE == "wordpress"
    assert reconciliation.WORDPRESS_CONTAINER == "shopping-wordpress"

    for replacement in (
        facts(context="wrong"), facts(project="wrong"),
        facts(database_name="wrong"), facts(wordpress_name="wrong"),
    ):
        assert reconciliation.classify_reconciliation(
            replacement, source(),
        ).classification is reconciliation.Classification.BLOCKED


def test_invocation_is_exactly_bounded_wordpress_only(monkeypatch) -> None:
    fixed = "/trusted/home/Library/Application Support/AIControlCenter/secrets/shopping-commerce.env"
    monkeypatch.setattr(reconciliation, "_trusted_runtime_cutover_path", lambda: fixed)
    argv = reconciliation.build_mutation_invocation().argv
    assert argv == (
        "docker", "--context", "colima-aicontrolcenter-commerce", "compose",
        "--project-name", "ai-shopping", "--file", "deploy/shopping/compose.yaml",
        "--env-file", fixed, "up", "-d", "--no-deps", "--pull", "never",
        "--force-recreate", "wordpress",
    )
    assert argv[-1:] == ("wordpress",)
    for forbidden in ("down", "volume", "rm", "prune", "build", "database",
                      "shopping-db", "wp-cli"):
        assert forbidden not in argv
    assert not ("pull" in argv and "--pull" not in argv)


def execute(authorization, runner, *, runtime_observer=facts,
            storage_observer=storage):
    return reconciliation.execute_reconciliation(
        observe_runtime=runtime_observer, observe_storage=storage_observer,
        authorization=authorization, runner=runner,
    )


def test_missing_or_consumed_authorization_never_executes() -> None:
    calls = []
    assert not execute(None, calls.append).mutation_executed
    consumed = OneShotAuthorization(available=False)
    assert not execute(consumed, calls.append).mutation_executed
    assert calls == []


def test_consumed_authorization_revalidates_fresh_evidence_then_executes_once(
    monkeypatch,
) -> None:
    monkeypatch.setattr(reconciliation, "_trusted_runtime_cutover_path", lambda: "/fixed/source")
    runtime_calls = []
    storage_calls = []
    source_calls = []
    monkeypatch.setattr(
        reconciliation, "observe_runtime_cutover_source",
        lambda: source_calls.append(True) or source(),
    )
    result = execute(
        OneShotAuthorization(),
        lambda _: reconciliation.ExecutionOutcome.SUCCEEDED,
        runtime_observer=lambda: runtime_calls.append(True) or facts(),
        storage_observer=lambda: storage_calls.append(True) or storage(),
    )
    assert result.authorization_consumed and result.mutation_executed
    assert result.decision.mutation_selected
    assert len(runtime_calls) == 2
    assert len(source_calls) == 2
    assert len(storage_calls) == 3  # initial, expected-before, post-attempt


@pytest.mark.parametrize(
    "fresh_runtime",
    [
        facts(wordpress=container(publishers=("127.0.0.1:59999->80/tcp",))),
        facts(wordpress=container(healthy=False)),
        facts(database=container(healthy=False)),
        facts(database=container(publishers=("127.0.0.1:3306->3306/tcp",))),
    ],
)
def test_fresh_runtime_change_consumes_authorization_without_selecting_or_running(
    fresh_runtime,
) -> None:
    runtime_observations = [facts(), fresh_runtime]
    calls = []
    result = execute(
        OneShotAuthorization(), calls.append,
        runtime_observer=lambda: runtime_observations.pop(0),
    )
    assert result.authorization_consumed
    assert not result.decision.mutation_selected
    assert not result.mutation_executed
    assert result.to_json_safe()["automatic_retry"] is False
    assert calls == []


def test_fresh_storage_change_consumes_authorization_without_execution() -> None:
    invalid = storage(volume(DATABASE_VOLUME, DATABASE_DESTINATION))
    observations = [storage(), invalid]
    calls = []
    result = execute(
        OneShotAuthorization(), calls.append,
        storage_observer=lambda: observations.pop(0),
    )
    assert result.authorization_consumed
    assert not result.decision.mutation_selected and not result.mutation_executed
    assert calls == []


def test_fresh_source_change_consumes_authorization_without_execution(monkeypatch) -> None:
    observations = [source(), source(ready=False)]
    monkeypatch.setattr(
        reconciliation, "observe_runtime_cutover_source",
        lambda: observations.pop(0),
    )
    calls = []
    result = execute(OneShotAuthorization(), calls.append)
    assert result.authorization_consumed
    assert not result.decision.mutation_selected and not result.mutation_executed
    assert calls == []


def test_one_authorization_cannot_generate_second_execution(monkeypatch) -> None:
    monkeypatch.setattr(reconciliation, "_trusted_runtime_cutover_path", lambda: "/fixed/source")
    authorization = OneShotAuthorization()
    calls = []
    first = execute(authorization, lambda invocation: calls.append(invocation) or reconciliation.ExecutionOutcome.SUCCEEDED)
    second = execute(authorization, lambda invocation: calls.append(invocation) or reconciliation.ExecutionOutcome.SUCCEEDED)
    assert first.mutation_executed and first.authorization_consumed
    assert not second.mutation_executed
    assert len(calls) == 1


@pytest.mark.parametrize("outcome", [
    reconciliation.ExecutionOutcome.FAILED,
    reconciliation.ExecutionOutcome.UNCERTAIN,
])
def test_failure_or_uncertainty_consumes_authorization_without_retry(monkeypatch, outcome) -> None:
    monkeypatch.setattr(reconciliation, "_trusted_runtime_cutover_path", lambda: "/fixed/source")
    authorization = OneShotAuthorization()
    calls = []
    result = execute(authorization, lambda invocation: calls.append(invocation) or outcome)
    assert len(calls) == 1
    assert result.authorization_consumed and result.mutation_executed
    assert result.outcome is outcome
    assert result.fresh_read_only_reconciliation_required
    assert result.to_json_safe()["automatic_retry"] is False


def test_runner_exception_is_uncertain_and_is_not_retried(monkeypatch) -> None:
    monkeypatch.setattr(reconciliation, "_trusted_runtime_cutover_path", lambda: "/fixed/source")
    calls = 0
    def runner(_invocation):
        nonlocal calls
        calls += 1
        raise RuntimeError("unknown result")
    result = execute(OneShotAuthorization(), runner)
    assert calls == 1 and result.outcome is reconciliation.ExecutionOutcome.UNCERTAIN
    assert result.authorization_consumed


def test_pre_and_post_storage_identity_is_not_preservation_or_backup(monkeypatch) -> None:
    monkeypatch.setattr(reconciliation, "_trusted_runtime_cutover_path", lambda: "/fixed/source")
    observations = [storage(), storage(), storage()]
    result = execute(
        OneShotAuthorization(), lambda _: reconciliation.ExecutionOutcome.SUCCEEDED,
        storage_observer=lambda: observations.pop(0),
    )
    output = result.to_json_safe()
    assert output["storage_identity_continuity"]["volume_identity_continuity_proven"]
    assert output["content_preservation_proven"] is False
    assert output["backup_restore_proven"] is False


def test_json_contract_has_fixed_authority_and_no_external_surfaces() -> None:
    output = reconciliation.classify_reconciliation(facts(), source()).to_json_safe()
    assert output["authoritative_work_item"] == "SHOP-SERVICE-START-01B"
    assert output["environment"] == "CONTROLLED_NON_PRODUCTION"
    assert output["database_mutation_allowed"] is False
    assert output["volume_deletion_allowed"] is False
    assert output["production_authority"] is False
    assert output["ubuntu_authority"] is False
    assert output["authorization_required"] is True
    assert "secret" not in json.dumps(output).lower()

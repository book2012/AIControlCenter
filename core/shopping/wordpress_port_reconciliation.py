"""Governed one-shot WordPress publisher reconciliation boundary.

Planning is pure. Runtime observation, authorization consumption, and the one
allowed Compose invocation are injected capabilities. This module never issues
authorization and never retries or rolls back.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from time import sleep
from typing import Callable, Protocol

from core.secrets.mariadb_continuity_trusted_mac_account_home_runtime_resolver import (
    resolve_trusted_mac_account_home,
)
from core.shopping.observability.storage_continuity import (
    DATABASE_VOLUME,
    WORDPRESS_VOLUME,
    StorageContinuityObservation,
    VolumeIdentityContinuityResult,
    compare_volume_identity_continuity,
    validate_storage_observation,
)
from core.shopping.runtime_cutover_secret_source import (
    SOURCE_COMPONENTS,
    WORDPRESS_PORT_EXPECTED,
    RuntimeCutoverSourceObservation,
    SourceReason,
    observe_runtime_cutover_source,
)


AUTHORITATIVE_WORK_ITEM = "SHOP-SERVICE-START-01B"
ENVIRONMENT = "CONTROLLED_NON_PRODUCTION"
TARGET_CONTEXT = "colima-aicontrolcenter-commerce"
COMPOSE_PROJECT = "ai-shopping"
COMPOSE_FILE = "deploy/shopping/compose.yaml"
COMPOSE_SERVICE = "wordpress"
WORDPRESS_CONTAINER = "shopping-wordpress"
DATABASE_CONTAINER = "shopping-db"
EXPECTED_BEFORE_BINDING = "127.0.0.1:58081->80/tcp"
EXPECTED_AFTER_BINDING = "127.0.0.1:58082->80/tcp"
MUTATION_ID = "SHOP-SERVICE-START-01B:WORDPRESS_PORT_58081_TO_58082"

# deploy/shopping/compose.yaml gives WordPress a 60-second start period followed
# by 20 healthcheck retries at 15-second intervals. Observe immediately, then
# cover that fixed 360-second convergence horizon without exposing timing knobs.
_POST_STABILIZATION_INTERVAL_SECONDS = 15
_POST_STABILIZATION_MAX_OBSERVATIONS = 25


@dataclass(frozen=True, slots=True)
class ContainerRuntimeFact:
    exists: bool
    running: bool
    healthy: bool
    publishers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WordPressPortRuntimeFacts:
    target_context: str
    compose_project: str
    database_container: str
    wordpress_container: str
    docker_context_reachable: bool
    database: ContainerRuntimeFact
    wordpress: ContainerRuntimeFact
    storage: StorageContinuityObservation


class Classification(StrEnum):
    CANDIDATE = "CANDIDATE"
    ALREADY_DESIRED = "ALREADY_DESIRED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class ReconciliationDecision:
    classification: Classification
    reason_codes: tuple[str, ...]
    mutation_selected: bool

    def to_json_safe(self) -> dict[str, object]:
        return _base_projection(
            mutation_selected=self.mutation_selected,
            mutation_executed=False,
            classification=self.classification.value,
            reason_codes=list(self.reason_codes),
        )


class AuthorizationConsumption(Protocol):
    """Dedicated durable WordPress authority; no caller-selected mutation."""

    def consume(self) -> object: ...


class AuthorizationConsumptionState(StrEnum):
    NOT_CONSUMED = "NOT_CONSUMED"
    CONSUMED = "CONSUMED"
    UNCERTAIN = "UNCERTAIN"


class ExecutionOutcome(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    UNCERTAIN = "UNCERTAIN"


@dataclass(frozen=True, slots=True)
class MutationInvocation:
    argv: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    decision: ReconciliationDecision
    mutation_executed: bool
    outcome: ExecutionOutcome | None
    authorization_consumed: bool | None
    fresh_read_only_reconciliation_required: bool
    pre_storage_observation: StorageContinuityObservation | None
    post_storage_observation: StorageContinuityObservation | None
    storage_identity_continuity: VolumeIdentityContinuityResult | None
    post_runtime_observation: WordPressPortRuntimeFacts | None = None
    post_source_observation: RuntimeCutoverSourceObservation | None = None
    post_runtime_validated: bool = False

    failure_stage: str | None = None

    @property
    def authorization_consumption_state(self) -> AuthorizationConsumptionState:
        if self.authorization_consumed is None:
            return AuthorizationConsumptionState.UNCERTAIN
        return (AuthorizationConsumptionState.CONSUMED if self.authorization_consumed
                else AuthorizationConsumptionState.NOT_CONSUMED)

    def to_json_safe(self) -> dict[str, object]:
        return _base_projection(
            mutation_selected=self.decision.mutation_selected,
            mutation_executed=self.mutation_executed,
            classification=self.decision.classification.value,
            reason_codes=list(self.decision.reason_codes),
            outcome=self.outcome.value if self.outcome else None,
            authorization_consumed=self.authorization_consumed,
            authorization_consumption_state=self.authorization_consumption_state.value,
            failure_stage=self.failure_stage,
            fresh_read_only_reconciliation_required=(
                self.fresh_read_only_reconciliation_required
            ),
            pre_storage_observation=(self.pre_storage_observation.to_json_safe()
                                     if self.pre_storage_observation else None),
            post_storage_observation=(
                self.post_storage_observation.to_json_safe()
                if self.post_storage_observation else None
            ),
            storage_identity_continuity=(
                self.storage_identity_continuity.to_json_safe()
                if self.storage_identity_continuity else None
            ),
            content_preservation_proven=False,
            backup_restore_proven=False,
            post_runtime_validated=self.post_runtime_validated,
        )


def _base_projection(*, mutation_selected: bool, mutation_executed: bool,
                     **extra: object) -> dict[str, object]:
    return {
        "authoritative_work_item": AUTHORITATIVE_WORK_ITEM,
        "environment": ENVIRONMENT,
        "target_context": TARGET_CONTEXT,
        "compose_project": COMPOSE_PROJECT,
        "compose_service": COMPOSE_SERVICE,
        "expected_before_binding": EXPECTED_BEFORE_BINDING,
        "expected_after_binding": EXPECTED_AFTER_BINDING,
        "database_mutation_allowed": False,
        "volume_deletion_allowed": False,
        "automatic_retry": False,
        "production_authority": False,
        "ubuntu_authority": False,
        "authorization_required": True,
        "mutation_selected": mutation_selected,
        "mutation_executed": mutation_executed,
        **extra,
    }


def classify_reconciliation(
    facts: WordPressPortRuntimeFacts,
    source: RuntimeCutoverSourceObservation,
) -> ReconciliationDecision:
    """Pure fail-closed classification with no runtime or authorization calls."""
    reasons: list[str] = []
    if facts.target_context != TARGET_CONTEXT:
        reasons.append("TARGET_CONTEXT_MISMATCH")
    if facts.compose_project != COMPOSE_PROJECT:
        reasons.append("COMPOSE_PROJECT_MISMATCH")
    if facts.database_container != DATABASE_CONTAINER:
        reasons.append("DATABASE_CONTAINER_MISMATCH")
    if facts.wordpress_container != WORDPRESS_CONTAINER:
        reasons.append("WORDPRESS_CONTAINER_MISMATCH")
    if facts.docker_context_reachable is not True:
        reasons.append("DOCKER_CONTEXT_UNREACHABLE")
    database = facts.database
    if not database.exists:
        reasons.append("DATABASE_ABSENT")
    if not database.running:
        reasons.append("DATABASE_NOT_RUNNING")
    if not database.healthy:
        reasons.append("DATABASE_NOT_HEALTHY")
    if database.publishers:
        reasons.append("DATABASE_HOST_PUBLISHER_PRESENT")
    wordpress = facts.wordpress
    if not wordpress.exists:
        reasons.append("WORDPRESS_ABSENT")
    if not wordpress.running:
        reasons.append("WORDPRESS_NOT_RUNNING")
    if not wordpress.healthy:
        reasons.append("WORDPRESS_NOT_HEALTHY")
    storage_targets = {
        item.volume_name: (item.service, item.container)
        for item in facts.storage.volumes
    }
    if validate_storage_observation(facts.storage) or storage_targets != {
        DATABASE_VOLUME: ("database", DATABASE_CONTAINER),
        WORDPRESS_VOLUME: (COMPOSE_SERVICE, WORDPRESS_CONTAINER),
    }:
        reasons.append("CANONICAL_STORAGE_NOT_READY")
    if not (
        type(source) is RuntimeCutoverSourceObservation
        and source.ready is True
        and source.reason_code is SourceReason.READY
        and source.filesystem_safe is True
        and source.values_exposed is False
        and source.wordpress_port_expected == WORDPRESS_PORT_EXPECTED
        and source.wordpress_port_value_valid is True
    ):
        reasons.append("RUNTIME_CUTOVER_SOURCE_NOT_READY")
    if wordpress.publishers == (EXPECTED_AFTER_BINDING,):
        if reasons:
            return ReconciliationDecision(Classification.BLOCKED, tuple(reasons), False)
        return ReconciliationDecision(Classification.ALREADY_DESIRED, (), False)
    if wordpress.publishers != (EXPECTED_BEFORE_BINDING,):
        reasons.append("WORDPRESS_BINDING_NOT_EXPECTED_BEFORE")
    if reasons:
        return ReconciliationDecision(Classification.BLOCKED, tuple(reasons), False)
    return ReconciliationDecision(Classification.CANDIDATE, (), False)


def _with_storage(
    facts: WordPressPortRuntimeFacts,
    storage: StorageContinuityObservation,
) -> WordPressPortRuntimeFacts:
    """Bind an independently observed storage snapshot to runtime facts."""
    return WordPressPortRuntimeFacts(
        facts.target_context, facts.compose_project, facts.database_container,
        facts.wordpress_container, facts.docker_context_reachable,
        facts.database, facts.wordpress, storage,
    )


def _select_governed_mutation(
    decision: ReconciliationDecision,
) -> ReconciliationDecision:
    """Select only an already revalidated candidate inside execution."""
    if decision.classification is not Classification.CANDIDATE:
        raise ValueError("only an exact candidate can be selected")
    return ReconciliationDecision(Classification.CANDIDATE, (), True)


def _trusted_runtime_cutover_path() -> str:
    """Resolve the sole env-file path from the trusted Darwin passwd authority."""
    home = resolve_trusted_mac_account_home()
    return str(Path(home.passwd_home).joinpath(*SOURCE_COMPONENTS))


def build_mutation_invocation() -> MutationInvocation:
    """Build the immutable WordPress-only invocation; accepts no caller target."""
    return MutationInvocation((
        "docker", "--context", TARGET_CONTEXT, "compose",
        "--project-name", COMPOSE_PROJECT, "--file", COMPOSE_FILE,
        "--env-file", _trusted_runtime_cutover_path(), "up", "-d",
        "--no-deps", "--pull", "never", "--force-recreate", COMPOSE_SERVICE,
    ))


def _sleep_between_post_observations() -> None:
    """Private fixed timing seam; tests may replace it without public knobs."""
    sleep(_POST_STABILIZATION_INTERVAL_SECONDS)


def _observe_post_state(
    observe_runtime: Callable[[], WordPressPortRuntimeFacts],
    observe_storage: Callable[[], StorageContinuityObservation],
    pre_mutation_storage: StorageContinuityObservation,
) -> tuple[
    WordPressPortRuntimeFacts | None,
    StorageContinuityObservation | None,
    RuntimeCutoverSourceObservation | None,
    VolumeIdentityContinuityResult | None,
    bool,
]:
    """Collect one fail-closed, read-only post-mutation evidence set."""
    try:
        post_runtime = observe_runtime()
        post_storage = observe_storage()
        post_source = observe_runtime_cutover_source()
        continuity = compare_volume_identity_continuity(
            pre_mutation_storage, post_storage,
        )
        post_facts = _with_storage(post_runtime, post_storage)
        post_decision = classify_reconciliation(post_facts, post_source)
        validated = (
            post_decision.classification is Classification.ALREADY_DESIRED
            and continuity.volume_identity_continuity_proven
        )
        return post_runtime, post_storage, post_source, continuity, validated
    except Exception:
        return None, None, None, None, False


def _stabilize_succeeded_post_state(
    observe_runtime: Callable[[], WordPressPortRuntimeFacts],
    observe_storage: Callable[[], StorageContinuityObservation],
    pre_mutation_storage: StorageContinuityObservation,
) -> tuple[
    WordPressPortRuntimeFacts | None,
    StorageContinuityObservation | None,
    RuntimeCutoverSourceObservation | None,
    VolumeIdentityContinuityResult | None,
    bool,
]:
    """Bound successful mutation follow-up to fixed read-only observations."""
    latest = (None, None, None, None, False)
    for observation_number in range(_POST_STABILIZATION_MAX_OBSERVATIONS):
        if observation_number:
            _sleep_between_post_observations()
        observed = _observe_post_state(
            observe_runtime, observe_storage, pre_mutation_storage,
        )
        if all(item is None for item in observed[:4]):
            break
        latest = observed
        if latest[-1]:
            break
    return latest


def _diagnostic_failure(stage: str, consumed: bool | None) -> ReconciliationResult:
    """Only repository-owned stages enter this value-free failure projection."""
    return ReconciliationResult(
        ReconciliationDecision(Classification.BLOCKED, (stage + "_FAILED",), False),
        False, None, consumed, consumed is not False, None, None, None,
        failure_stage=stage,
    )


def execute_reconciliation(
    *,
    observe_runtime: Callable[[], WordPressPortRuntimeFacts],
    observe_storage: Callable[[], StorageContinuityObservation],
    authorization: AuthorizationConsumption | None,
    runner: Callable[[MutationInvocation], ExecutionOutcome],
) -> ReconciliationResult:
    """Consume at most one authorization and make at most one mutation call."""
    pre_storage = None
    stage = "INITIAL_RUNTIME_OBSERVATION"
    try:
        initial_runtime = observe_runtime()
        stage = "INITIAL_STORAGE_OBSERVATION"
        pre_storage = observe_storage()
        stage = "INITIAL_FACT_BINDING"
        initial_facts = _with_storage(initial_runtime, pre_storage)
        stage = "INITIAL_SOURCE_OBSERVATION"
        initial_source = observe_runtime_cutover_source()
        stage = "INITIAL_CLASSIFICATION"
        candidate = classify_reconciliation(initial_facts, initial_source)
    except Exception:
        return _diagnostic_failure(stage, False)
    if candidate.classification is not Classification.CANDIDATE:
        return ReconciliationResult(candidate, False, None, False, False,
                                    pre_storage, None, None)
    if authorization is None:
        return ReconciliationResult(candidate, False, None, False, False,
                                    pre_storage, None, None)
    consumed = False
    stage = "AUTHORIZATION_PREPARATION"
    try:
        from core.secrets.mariadb_continuity_trusted_ownership_expectation import (
            issue_trusted_ownership_expectation,
        )
        from core.shopping.wordpress_port_authorization import validate_consumption_result
        trusted_home = resolve_trusted_mac_account_home()
        identity = issue_trusted_ownership_expectation(trusted_home)
        stage = "AUTHORIZATION_CONSUMPTION"
        consumed = None  # Entering consume may cross a durable boundary.
        consumption = authorization.consume()
        stage = "AUTHORIZATION_RECEIPT_VALIDATION"
        validate_consumption_result(
            consumption, now=datetime.now(timezone.utc),
            uid=identity.expected_uid, gid=identity.expected_gid,
        )
    except Exception as error:
        from core.shopping.wordpress_port_authorization import ConsumptionFailure
        if type(error) is ConsumptionFailure:
            consumed = {AuthorizationConsumptionState.NOT_CONSUMED: False,
                        AuthorizationConsumptionState.CONSUMED: True}.get(error.state)
        return _diagnostic_failure(stage, consumed)

    fresh_runtime: WordPressPortRuntimeFacts | None = None
    fresh_storage: StorageContinuityObservation | None = None
    fresh_source: RuntimeCutoverSourceObservation | None = None
    observation_reasons: list[str] = []
    try:
        fresh_runtime = observe_runtime()
    except Exception:
        observation_reasons.append("FRESH_RUNTIME_OBSERVATION_FAILED")
    try:
        fresh_storage = observe_storage()
    except Exception:
        observation_reasons.append("FRESH_STORAGE_OBSERVATION_FAILED")
    try:
        fresh_source = observe_runtime_cutover_source()
    except Exception:
        observation_reasons.append("FRESH_RUNTIME_CUTOVER_SOURCE_OBSERVATION_FAILED")
    if observation_reasons:
        blocked = ReconciliationDecision(
            Classification.BLOCKED, tuple(observation_reasons), False,
        )
        return ReconciliationResult(
            blocked, False, None, True, False,
            pre_storage, fresh_storage, None,
        )

    assert fresh_runtime is not None
    assert fresh_storage is not None
    assert fresh_source is not None
    try:
        fresh_facts = _with_storage(fresh_runtime, fresh_storage)
        revalidated = classify_reconciliation(fresh_facts, fresh_source)
    except Exception:
        return _diagnostic_failure("FRESH_CLASSIFICATION", True)
    if revalidated.classification is not Classification.CANDIDATE:
        return ReconciliationResult(
            revalidated, False, None, True, False,
            pre_storage, fresh_storage, None,
        )

    selected = _select_governed_mutation(revalidated)
    try:
        invocation = build_mutation_invocation()
    except Exception:
        return _diagnostic_failure("MUTATION_PREPARATION", True)
    try:
        outcome = runner(invocation)
        if outcome not in tuple(ExecutionOutcome):
            outcome = ExecutionOutcome.UNCERTAIN
    except Exception:
        outcome = ExecutionOutcome.UNCERTAIN
    if outcome is ExecutionOutcome.SUCCEEDED:
        (post_runtime, post_storage, post_source, continuity,
         post_validated) = _stabilize_succeeded_post_state(
             observe_runtime, observe_storage, fresh_storage,
         )
    else:
        (post_runtime, post_storage, post_source, continuity,
         post_validated) = _observe_post_state(
             observe_runtime, observe_storage, fresh_storage,
         )
    if outcome is ExecutionOutcome.SUCCEEDED and not post_validated:
        outcome = ExecutionOutcome.UNCERTAIN
    return ReconciliationResult(
        selected, True, outcome, True, True, pre_storage, post_storage, continuity,
        post_runtime, post_source, post_validated,
    )


__all__ = (
    "AUTHORITATIVE_WORK_ITEM", "Classification", "ContainerRuntimeFact",
    "ENVIRONMENT", "ExecutionOutcome", "MutationInvocation",
    "ReconciliationDecision", "ReconciliationResult", "WordPressPortRuntimeFacts",
    "build_mutation_invocation", "classify_reconciliation", "execute_reconciliation",
)

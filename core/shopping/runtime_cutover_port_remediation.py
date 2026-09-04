"""Governed, fixed runtime-cutover WordPress-port source remediation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Callable, Protocol

from core.shopping.runtime_cutover_secret_source import (
    WORDPRESS_PORT_EXPECTED,
    WORDPRESS_PORT_KEY,
    RuntimeCutoverSourceObservation,
    SourceReason,
)

AUTHORITATIVE_WORK_ITEM = "SHOP-SERVICE-START-01B"
ENVIRONMENT = "CONTROLLED_NON_PRODUCTION"
MUTATION_ID = "SHOP-SERVICE-START-01B:RUNTIME_CUTOVER_SOURCE_PORT_TO_58082"
DESIRED_VALUE = WORDPRESS_PORT_EXPECTED


class Classification(StrEnum):
    CANDIDATE = "CANDIDATE"
    ALREADY_DESIRED = "ALREADY_DESIRED"
    BLOCKED = "BLOCKED"


class Outcome(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    UNCERTAIN = "UNCERTAIN"


class AuthorizationConsumption(Protocol):
    def consume_once(self, mutation_id: str) -> bool: ...


class FixedSourceMutation(Protocol):
    def replace_wordpress_port(self) -> Outcome: ...


@dataclass(frozen=True, slots=True)
class Decision:
    classification: Classification
    reason_codes: tuple[str, ...]
    mutation_selected: bool = False


@dataclass(frozen=True, slots=True)
class Result:
    classification: Classification
    reason_codes: tuple[str, ...]
    authorization_consumed: bool
    mutation_selected: bool
    mutation_executed: bool
    outcome: Outcome | None
    fresh_read_only_reconciliation_required: bool
    source_ready_after: bool
    source_port_valid_after: bool

    def to_json_safe(self) -> dict[str, object]:
        return {
            "authoritative_work_item": AUTHORITATIVE_WORK_ITEM,
            "environment": ENVIRONMENT,
            "mutation_id": MUTATION_ID,
            "classification": self.classification.value,
            "reason_codes": list(self.reason_codes),
            "authorization_required": True,
            "authorization_consumed": self.authorization_consumed,
            "mutation_selected": self.mutation_selected,
            "mutation_executed": self.mutation_executed,
            "outcome": self.outcome.value if self.outcome else None,
            "fresh_read_only_reconciliation_required": self.fresh_read_only_reconciliation_required,
            "expected_key": WORDPRESS_PORT_KEY,
            "expected_value": DESIRED_VALUE,
            "source_ready_after": self.source_ready_after,
            "source_port_valid_after": self.source_port_valid_after,
            "automatic_retry": False,
            "production_authority": False,
            "ubuntu_authority": False,
            "database_mutation_allowed": False,
            "wordpress_runtime_mutation_allowed": False,
            "secret_values_retained": False,
            "secret_values_emitted": False,
            "secret_values_logged": False,
            "secret_values_hashed": False,
            "secret_values_semantically_compared": False,
        }


def classify_candidate(source: RuntimeCutoverSourceObservation) -> Decision:
    """Pure classification only; mutation selection is deliberately impossible."""
    if type(source) is not RuntimeCutoverSourceObservation:
        return Decision(Classification.BLOCKED, ("SOURCE_OBSERVATION_INVALID",))
    if (
        source.filesystem_safe is True
        and source.wordpress_port_expected == DESIRED_VALUE
        and source.wordpress_port_value_valid is True
        and source.ready is True
        and source.reason_code is SourceReason.READY
        and source.values_exposed is False
    ):
        return Decision(Classification.ALREADY_DESIRED, ())
    if (
        source.filesystem_safe is True
        and source.wordpress_port_expected == DESIRED_VALUE
        and source.wordpress_port_value_valid is False
        and source.ready is False
        and source.reason_code is SourceReason.WORDPRESS_PORT_VALUE_INVALID
        and source.values_exposed is False
        and not source.missing_key_names
        and not source.duplicate_key_names
        and not source.unknown_key_names
    ):
        return Decision(Classification.CANDIDATE, ())
    return Decision(Classification.BLOCKED, (source.reason_code.value,))


def execute_remediation(
    *,
    initial_observation: RuntimeCutoverSourceObservation,
    observe_source: Callable[[], RuntimeCutoverSourceObservation],
    authorization: AuthorizationConsumption | None,
    mutation: FixedSourceMutation,
) -> Result:
    initial = classify_candidate(initial_observation)
    if initial.classification is not Classification.CANDIDATE or authorization is None:
        return Result(initial.classification, initial.reason_codes, False, False, False,
                      None, False, False, False)
    try:
        consumed = authorization.consume_once(MUTATION_ID) is True
    except Exception:
        consumed = False
    if not consumed:
        return Result(initial.classification, initial.reason_codes, False, False, False,
                      None, False, False, False)
    try:
        fresh = classify_candidate(observe_source())
    except Exception:
        fresh = Decision(Classification.BLOCKED, ("FRESH_SOURCE_OBSERVATION_FAILED",))
    if fresh.classification is not Classification.CANDIDATE:
        return Result(fresh.classification, fresh.reason_codes, True, False, False,
                      None, False, False, False)
    try:
        outcome = mutation.replace_wordpress_port()
        if outcome not in tuple(Outcome):
            outcome = Outcome.UNCERTAIN
    except Exception:
        outcome = Outcome.UNCERTAIN
    if outcome is not Outcome.SUCCEEDED:
        return Result(fresh.classification, (outcome.value,), True, True, True,
                      outcome, True, False, False)
    try:
        after = observe_source()
    except Exception:
        after = None
    valid = bool(after and classify_candidate(after).classification is Classification.ALREADY_DESIRED)
    final_outcome = Outcome.SUCCEEDED if valid else Outcome.FAILED
    reasons = () if valid else ("POST_SOURCE_NOT_READY",)
    return Result(fresh.classification, reasons, True, True, True, final_outcome,
                  not valid, bool(after and after.ready),
                  bool(after and after.wordpress_port_value_valid))


__all__ = ("AUTHORITATIVE_WORK_ITEM", "AuthorizationConsumption", "Classification",
           "DESIRED_VALUE", "Decision", "ENVIRONMENT", "FixedSourceMutation",
           "MUTATION_ID", "Outcome", "Result", "classify_candidate",
           "execute_remediation")

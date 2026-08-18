"""Value-free Phase B2A MariaDB continuity observation contracts."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ContinuityValidationCategory(str, Enum):
    CREDENTIAL_ACCEPTED = "CREDENTIAL_ACCEPTED"
    EXPECTED_DATABASE_IDENTITY = "EXPECTED_DATABASE_IDENTITY"
    EXPECTED_ACCOUNT_IDENTITY = "EXPECTED_ACCOUNT_IDENTITY"
    REQUIRED_GRANTS = "REQUIRED_GRANTS"
    EXPECTED_DATA_IDENTITY = "EXPECTED_DATA_IDENTITY"
    DECLARED_DATA_CONTINUITY = "DECLARED_DATA_CONTINUITY"


class ObservationState(str, Enum):
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    NOT_EVALUATED = "NOT_EVALUATED"
    UNCERTAIN = "UNCERTAIN"


class ConsumerCompatibility(str, Enum):
    NOT_EVALUATED = "NOT_EVALUATED"


@dataclass(frozen=True, slots=True)
class MariaDBContinuityObservations:
    """Canonical current facts; fields are closed against caller forgery."""

    facts: tuple[tuple[ContinuityValidationCategory, ObservationState], ...] = field(
        default_factory=lambda: tuple(
            (category, ObservationState.NOT_EVALUATED)
            for category in ContinuityValidationCategory
        ),
        init=False,
    )
    consumer_compatibility: ConsumerCompatibility = field(
        default=ConsumerCompatibility.NOT_EVALUATED, init=False
    )
    complete_validation: bool = field(default=False, init=False)

    def to_projection(self) -> dict[str, Any]:
        return {
            "facts": {category.value: state.value for category, state in self.facts},
            "consumer_compatibility": self.consumer_compatibility.value,
            "complete_validation": self.complete_validation,
            "authorization_authority": False,
            "capability_authority": False,
            "execution_authority": False,
            "mutation_authority": False,
            "retry_authority": False,
            "reconnect_authority": False,
            "rollback_authority": False,
            "value_free": True,
        }


@dataclass(frozen=True, slots=True)
class MariaDBContinuityRuntimeObservation:
    """Value-free output of one future validation attempt."""

    credential_accepted: ObservationState
    expected_database_identity: ObservationState
    expected_account_identity: ObservationState
    required_grants: ObservationState
    expected_data_identity: ObservationState
    declared_data_continuity: ObservationState
    consumer_compatibility: ConsumerCompatibility = field(
        default=ConsumerCompatibility.NOT_EVALUATED, init=False
    )

    def __post_init__(self) -> None:
        for state in self.facts:
            if type(state[1]) is not ObservationState:
                raise TypeError("runtime facts must be exact ObservationState values")

    @property
    def facts(self) -> tuple[tuple[ContinuityValidationCategory, ObservationState], ...]:
        return (
            (ContinuityValidationCategory.CREDENTIAL_ACCEPTED, self.credential_accepted),
            (ContinuityValidationCategory.EXPECTED_DATABASE_IDENTITY, self.expected_database_identity),
            (ContinuityValidationCategory.EXPECTED_ACCOUNT_IDENTITY, self.expected_account_identity),
            (ContinuityValidationCategory.REQUIRED_GRANTS, self.required_grants),
            (ContinuityValidationCategory.EXPECTED_DATA_IDENTITY, self.expected_data_identity),
            (ContinuityValidationCategory.DECLARED_DATA_CONTINUITY, self.declared_data_continuity),
        )

    @property
    def complete_validation(self) -> bool:
        return all(state is ObservationState.CONFIRMED for _, state in self.facts)

    def to_projection(self) -> dict[str, Any]:
        return {
            "facts": {category.value: state.value for category, state in self.facts},
            "consumer_compatibility": self.consumer_compatibility.value,
            "complete_validation": self.complete_validation,
            "authorization_authority": False,
            "capability_authority": False,
            "execution_authority": False,
            "mutation_authority": False,
            "retry_authority": False,
            "reconnect_authority": False,
            "rollback_authority": False,
            "value_free": True,
        }


def canonical_phase_b2a_observations() -> MariaDBContinuityObservations:
    return MariaDBContinuityObservations()

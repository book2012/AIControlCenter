"""Value-free MariaDB historical credential-continuity decision metadata.

The resulting record contains factual metadata only.  It is not a
GovernanceAuthorization, AuthorizationConsumptionResult, mutation budget,
execution request, execution receipt, or execution authority.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ContinuityState(str, Enum):
    """Closed set of factual continuity states."""

    UNRESOLVED = "UNRESOLVED"
    STRATEGY_DECLARED = "STRATEGY_DECLARED"
    VALIDATION_REQUIRED = "VALIDATION_REQUIRED"
    RESOLVED = "RESOLVED"


class ContinuityStrategy(str, Enum):
    """Closed set of caller-declared continuity strategies."""

    RECOVER = "RECOVER"
    ROTATE = "ROTATE"
    REPLACE = "REPLACE"


class NextBoundaryType(str, Enum):
    """Descriptive boundary labels; these labels grant no authority."""

    HUMAN_DECISION_REQUIRED = "HUMAN_DECISION_REQUIRED"
    RECOVERY_VALIDATION_REQUIRED = "RECOVERY_VALIDATION_REQUIRED"
    FUTURE_GOVERNED_MUTATION_REQUIRED = "FUTURE_GOVERNED_MUTATION_REQUIRED"
    CONTINUITY_RESOLVED = "CONTINUITY_RESOLVED"


@dataclass(frozen=True, slots=True)
class ContinuityObservation:
    """Smallest caller-supplied, value-free set of factual observations."""

    strategy: ContinuityStrategy | None = None
    recovery_source_declared: bool = False
    validation_confirmed: bool = False

    def __post_init__(self) -> None:
        if self.strategy is not None and not isinstance(self.strategy, ContinuityStrategy):
            raise TypeError("strategy must be a ContinuityStrategy or None")
        if type(self.recovery_source_declared) is not bool:
            raise TypeError("recovery_source_declared must be bool")
        if type(self.validation_confirmed) is not bool:
            raise TypeError("validation_confirmed must be bool")
        if self.strategy is None and self.validation_confirmed:
            raise ValueError("validation cannot be confirmed without a strategy")
        if self.strategy is None and self.recovery_source_declared:
            raise ValueError("a recovery source cannot be declared without a strategy")
        if (
            self.strategy in (ContinuityStrategy.ROTATE, ContinuityStrategy.REPLACE)
            and self.recovery_source_declared
        ):
            raise ValueError("recovery-source metadata is valid only for RECOVER")


@dataclass(frozen=True, slots=True)
class ContinuityDecision:
    """Pure decision record whose projection is deterministic and JSON-safe."""

    state: ContinuityState
    strategy: ContinuityStrategy | None
    recovery_source_declared: bool
    validation_confirmed: bool
    reason_code: str
    next_boundary_type: NextBoundaryType

    def __post_init__(self) -> None:
        if not isinstance(self.state, ContinuityState):
            raise TypeError("state must be a ContinuityState")
        if self.strategy is not None and not isinstance(self.strategy, ContinuityStrategy):
            raise TypeError("strategy must be a ContinuityStrategy or None")
        if type(self.recovery_source_declared) is not bool:
            raise TypeError("recovery_source_declared must be bool")
        if type(self.validation_confirmed) is not bool:
            raise TypeError("validation_confirmed must be bool")
        if not isinstance(self.next_boundary_type, NextBoundaryType):
            raise TypeError("next_boundary_type must be a NextBoundaryType")

        valid_combinations = {
            ContinuityState.UNRESOLVED: (
                None,
                False,
                False,
                "MARIADB_HISTORICAL_CREDENTIAL_CONTINUITY_UNRESOLVED",
                NextBoundaryType.HUMAN_DECISION_REQUIRED,
            ),
            ContinuityState.VALIDATION_REQUIRED: (
                ContinuityStrategy.RECOVER,
                True,
                False,
                "MARIADB_RECOVERY_VALIDATION_REQUIRED",
                NextBoundaryType.RECOVERY_VALIDATION_REQUIRED,
            ),
        }
        if self.state in valid_combinations:
            expected = valid_combinations[self.state]
            actual = (
                self.strategy,
                self.recovery_source_declared,
                self.validation_confirmed,
                self.reason_code,
                self.next_boundary_type,
            )
            if actual != expected:
                raise ValueError(f"contradictory {self.state.value} continuity decision")
            return

        if self.state is ContinuityState.STRATEGY_DECLARED:
            expected_boundary = (
                NextBoundaryType.HUMAN_DECISION_REQUIRED
                if self.strategy is ContinuityStrategy.RECOVER
                else NextBoundaryType.FUTURE_GOVERNED_MUTATION_REQUIRED
            )
            if not (
                self.strategy in tuple(ContinuityStrategy)
                and self.recovery_source_declared is False
                and self.validation_confirmed is False
                and self.reason_code == "MARIADB_CONTINUITY_STRATEGY_DECLARED"
                and self.next_boundary_type is expected_boundary
            ):
                raise ValueError("contradictory STRATEGY_DECLARED continuity decision")
            return

        if not (
            self.strategy in tuple(ContinuityStrategy)
            and self.validation_confirmed is True
            and self.recovery_source_declared
            is (self.strategy is ContinuityStrategy.RECOVER)
            and self.reason_code == "MARIADB_CONTINUITY_RESOLVED"
            and self.next_boundary_type is NextBoundaryType.CONTINUITY_RESOLVED
        ):
            raise ValueError("contradictory RESOLVED continuity decision")

    def to_projection(self) -> dict[str, Any]:
        """Return value-free descriptive metadata, never executable authority."""

        return {
            "schema_version": "1.0",
            "inspection": "READ_ONLY",
            "owner": "MAC_MINI_M4_AICONTROLCENTER_CONTROL_PLANE",
            "value_free": True,
            "secret_values_read": False,
            "mutation_authority": False,
            "continuity": {
                "state": self.state.value,
                "strategy": self.strategy.value if self.strategy is not None else None,
                "recovery_source_declared": self.recovery_source_declared,
                "production_validation_required": (
                    self.state is ContinuityState.VALIDATION_REQUIRED
                ),
                "resolved": self.state is ContinuityState.RESOLVED,
                "reason_codes": [self.reason_code],
            },
            "next_boundary": {
                "boundary_type": self.next_boundary_type.value,
                "capability_id": None,
            },
        }


def decide_continuity(observation: ContinuityObservation) -> ContinuityDecision:
    """Project caller-supplied facts without inspecting or changing any system."""

    if not isinstance(observation, ContinuityObservation):
        raise TypeError("observation must be ContinuityObservation")

    strategy = observation.strategy
    if strategy is None:
        return ContinuityDecision(
            state=ContinuityState.UNRESOLVED,
            strategy=None,
            recovery_source_declared=False,
            validation_confirmed=False,
            reason_code="MARIADB_HISTORICAL_CREDENTIAL_CONTINUITY_UNRESOLVED",
            next_boundary_type=NextBoundaryType.HUMAN_DECISION_REQUIRED,
        )

    if observation.validation_confirmed:
        if strategy is ContinuityStrategy.RECOVER and not observation.recovery_source_declared:
            raise ValueError("RECOVER validation requires a declared recovery source")
        return ContinuityDecision(
            state=ContinuityState.RESOLVED,
            strategy=strategy,
            recovery_source_declared=observation.recovery_source_declared,
            validation_confirmed=True,
            reason_code="MARIADB_CONTINUITY_RESOLVED",
            next_boundary_type=NextBoundaryType.CONTINUITY_RESOLVED,
        )

    if strategy is ContinuityStrategy.RECOVER and observation.recovery_source_declared:
        return ContinuityDecision(
            state=ContinuityState.VALIDATION_REQUIRED,
            strategy=strategy,
            recovery_source_declared=True,
            validation_confirmed=False,
            reason_code="MARIADB_RECOVERY_VALIDATION_REQUIRED",
            next_boundary_type=NextBoundaryType.RECOVERY_VALIDATION_REQUIRED,
        )

    boundary = (
        NextBoundaryType.HUMAN_DECISION_REQUIRED
        if strategy is ContinuityStrategy.RECOVER
        else NextBoundaryType.FUTURE_GOVERNED_MUTATION_REQUIRED
    )
    return ContinuityDecision(
        state=ContinuityState.STRATEGY_DECLARED,
        strategy=strategy,
        recovery_source_declared=False,
        validation_confirmed=False,
        reason_code="MARIADB_CONTINUITY_STRATEGY_DECLARED",
        next_boundary_type=boundary,
    )

"""Pure factual lifecycle state for a one-shot continuity attempt."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class AttemptState(str, Enum):
    NEW = "NEW"
    AUTHORIZED = "AUTHORIZED"
    CONSUMED = "CONSUMED"
    PRE_ATTEMPT = "PRE_ATTEMPT"
    ATTEMPT_INITIATED = "ATTEMPT_INITIATED"
    TERMINAL = "TERMINAL"


_NEXT_STATE = {
    AttemptState.NEW: (AttemptState.AUTHORIZED,),
    AttemptState.AUTHORIZED: (AttemptState.CONSUMED,),
    AttemptState.CONSUMED: (AttemptState.PRE_ATTEMPT,),
    AttemptState.PRE_ATTEMPT: (
        AttemptState.ATTEMPT_INITIATED,
        AttemptState.TERMINAL,
    ),
    AttemptState.ATTEMPT_INITIATED: (AttemptState.TERMINAL,),
    AttemptState.TERMINAL: (),
}


@dataclass(frozen=True, slots=True)
class MariaDBContinuityAttempt:
    """Value-free snapshot; AUTHORIZED records only an observed fact."""

    state: AttemptState
    initiation_occurred: bool = False

    def __post_init__(self) -> None:
        if type(self.state) is not AttemptState:
            raise TypeError("state must be AttemptState")
        if type(self.initiation_occurred) is not bool:
            raise TypeError("initiation_occurred must be bool")
        requires_initiation = self.state is AttemptState.ATTEMPT_INITIATED
        permits_initiation = self.state in (
            AttemptState.ATTEMPT_INITIATED,
            AttemptState.TERMINAL,
        )
        if requires_initiation and not self.initiation_occurred:
            raise ValueError("ATTEMPT_INITIATED requires initiation fact")
        if self.initiation_occurred and not permits_initiation:
            raise ValueError("initiation fact contradicts state")

    @classmethod
    def new(cls) -> "MariaDBContinuityAttempt":
        return cls(AttemptState.NEW)

    @property
    def attempted_count(self) -> int:
        return int(self.initiation_occurred)

    def transition(self, next_state: AttemptState) -> "MariaDBContinuityAttempt":
        if type(next_state) is not AttemptState:
            raise TypeError("next_state must be AttemptState")
        if next_state not in _NEXT_STATE[self.state]:
            raise ValueError(f"invalid transition from {self.state.value}")
        initiated = self.initiation_occurred or (
            next_state is AttemptState.ATTEMPT_INITIATED
        )
        return type(self)(next_state, initiated)

    def to_projection(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "initiation_occurred": self.initiation_occurred,
            "attempted_count": self.attempted_count,
            "authorization_authority": False,
            "capability_authority": False,
            "execution_authority": False,
            "mutation_authority": False,
            "retry_authority": False,
            "rollback_authority": False,
            "value_free": True,
        }

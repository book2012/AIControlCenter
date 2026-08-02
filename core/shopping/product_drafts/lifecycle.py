"""Pure closed lifecycle transition evaluation."""
from __future__ import annotations
from dataclasses import dataclass, fields, replace
from datetime import datetime
from enum import Enum

from .models import LifecycleState, ProductDraftRevision
from .serialization import sha256_digest
from .values import ActorReference, SCHEMA_VERSION, require_digest, require_text, require_utc

PERMITTED_TRANSITIONS=frozenset({
 (LifecycleState.DRAFT,LifecycleState.VALIDATED),(LifecycleState.VALIDATED,LifecycleState.DRAFT),
 (LifecycleState.VALIDATED,LifecycleState.REVIEW_REQUIRED),(LifecycleState.REVIEW_REQUIRED,LifecycleState.APPROVED),
 (LifecycleState.REVIEW_REQUIRED,LifecycleState.REJECTED),(LifecycleState.APPROVED,LifecycleState.REVOKED),
 (LifecycleState.APPROVED,LifecycleState.SUPERSEDED),(LifecycleState.APPROVED,LifecycleState.DEPLOYMENT_READY),
 (LifecycleState.DRAFT,LifecycleState.SUPERSEDED),(LifecycleState.VALIDATED,LifecycleState.SUPERSEDED),
 (LifecycleState.REVIEW_REQUIRED,LifecycleState.SUPERSEDED),(LifecycleState.REJECTED,LifecycleState.SUPERSEDED),
 (LifecycleState.REVOKED,LifecycleState.SUPERSEDED),(LifecycleState.DEPLOYMENT_READY,LifecycleState.REVOKED),
 (LifecycleState.DEPLOYMENT_READY,LifecycleState.SUPERSEDED)})

class TransitionOutcome(str,Enum):
    APPLIED="APPLIED"; IDEMPOTENT_REPLAY="IDEMPOTENT_REPLAY"; REJECTED_INVALID_TRANSITION="REJECTED_INVALID_TRANSITION"
    REJECTED_CONFLICT="REJECTED_CONFLICT"; REJECTED_IDEMPOTENCY_KEY_REUSE="REJECTED_IDEMPOTENCY_KEY_REUSE"

@dataclass(frozen=True,slots=True)
class TransitionCommand:
    draft_id:str; revision_id:str; expected_revision_id:str; expected_revision_number:int
    from_state:LifecycleState; to_state:LifecycleState; actor:ActorReference; correlation_id:str; audit_reference:str
    idempotency_key:str; command_digest:str; requested_at:datetime; kind:str="COMMAND"; schema_version:str=SCHEMA_VERSION
    def __post_init__(self):
        for n in ("draft_id","revision_id","expected_revision_id","correlation_id","audit_reference","idempotency_key"): require_text(getattr(self,n),n)
        if type(self.expected_revision_number) is not int or self.expected_revision_number<1: raise ValueError("expected_revision_number must be >= 1")
        for n in ("from_state","to_state"):
            if not isinstance(getattr(self,n),LifecycleState): object.__setattr__(self,n,LifecycleState(getattr(self,n)))
        if not isinstance(self.actor, ActorReference):
            raise ValueError("actor must be an ActorReference")
        require_digest(self.command_digest,"command_digest"); require_utc(self.requested_at,"requested_at")
        if self.kind != "COMMAND" or self.schema_version != SCHEMA_VERSION:
            raise ValueError("unsupported transition command contract")

@dataclass(frozen=True,slots=True)
class TransitionResult:
    draft_id:str; revision_id:str; previous_state:LifecycleState; state:LifecycleState; outcome:TransitionOutcome
    idempotency_key:str; command_digest:str; result_digest:str; audit_reference:str; completed_at:datetime
    kind:str="RESULT"; schema_version:str=SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in (
            "draft_id", "revision_id", "idempotency_key",
            "audit_reference",
        ):
            require_text(getattr(self, name), name)
        for name in ("previous_state", "state"):
            if not isinstance(getattr(self, name), LifecycleState):
                object.__setattr__(self, name, LifecycleState(getattr(self, name)))
        if not isinstance(self.outcome, TransitionOutcome):
            object.__setattr__(self, "outcome", TransitionOutcome(self.outcome))
        require_digest(self.command_digest, "command_digest")
        require_digest(self.result_digest, "result_digest")
        require_utc(self.completed_at, "completed_at")
        if self.kind != "RESULT" or self.schema_version != SCHEMA_VERSION:
            raise ValueError("unsupported transition result contract")

def evaluate_transition(revision:ProductDraftRevision, command:TransitionCommand, completed_at:datetime) -> TransitionResult:
    """Evaluate without I/O; caller explicitly supplies the completion timestamp."""
    require_utc(completed_at,"completed_at")
    conflict=(command.draft_id!=revision.draft_id or command.revision_id!=revision.revision_id or
      command.expected_revision_id!=revision.revision_id or command.expected_revision_number!=revision.revision_number or command.from_state!=revision.state)
    outcome=TransitionOutcome.REJECTED_CONFLICT if conflict else (TransitionOutcome.APPLIED if (command.from_state,command.to_state) in PERMITTED_TRANSITIONS else TransitionOutcome.REJECTED_INVALID_TRANSITION)
    state=command.to_state if outcome is TransitionOutcome.APPLIED else revision.state
    seed={"draft_id":revision.draft_id,"revision_id":revision.revision_id,"previous_state":revision.state.value,"state":state.value,"outcome":outcome.value,"idempotency_key":command.idempotency_key,"command_digest":command.command_digest,"audit_reference":command.audit_reference,"completed_at":completed_at}
    return TransitionResult(revision.draft_id,revision.revision_id,revision.state,state,outcome,command.idempotency_key,command.command_digest,sha256_digest(seed),command.audit_reference,completed_at)

def replay_result(result:TransitionResult) -> TransitionResult:
    seed = {item.name: getattr(result, item.name) for item in fields(result)}
    seed["outcome"]=TransitionOutcome.IDEMPOTENT_REPLAY
    seed.pop("result_digest",None)
    return replace(result,outcome=TransitionOutcome.IDEMPOTENT_REPLAY,result_digest=sha256_digest(seed))

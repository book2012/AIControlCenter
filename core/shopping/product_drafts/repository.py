"""Replaceable repository port and isolated in-memory development adapter."""
from __future__ import annotations
from typing import Protocol
from dataclasses import replace

from .errors import DuplicateRevisionError, RevisionChainError, RevisionSequenceError
from .lifecycle import TransitionCommand, TransitionOutcome, TransitionResult, evaluate_transition, replay_result
from .models import ProductDraftRevision
from .serialization import sha256_digest

class ProductDraftRepository(Protocol):
    def store(self, revision:ProductDraftRevision)->None: ...
    def fetch(self,draft_id:str,revision_id:str)->ProductDraftRevision|None: ...
    def fetch_current(self,draft_id:str)->ProductDraftRevision|None: ...
    def get_idempotency(self,draft_id:str,key:str)->tuple[str,TransitionResult]|None: ...
    def bind_idempotency(self,draft_id:str,key:str,digest:str,result:TransitionResult)->None: ...
    def transition(self,command:TransitionCommand,completed_at)->TransitionResult: ...

class InMemoryProductDraftRepository(ProductDraftRepository):
    def __init__(self): self._revisions={}; self._current={}; self._idempotency={}
    def store(self,revision):
        if not isinstance(revision, ProductDraftRevision):
            raise TypeError("revision must be a ProductDraftRevision")
        key=(revision.draft_id,revision.revision_id)
        if key in self._revisions: raise DuplicateRevisionError("duplicate revision_id")
        current=self._current.get(revision.draft_id)
        if current is None:
            if revision.revision_number!=1 or revision.identity.previous_revision_id is not None: raise RevisionSequenceError("first stored revision must be number 1")
        else:
            if revision.revision_number!=current.revision_number+1: raise RevisionSequenceError("revision numbers must be monotonic")
            if revision.identity.previous_revision_id!=current.revision_id: raise RevisionChainError("previous_revision_id must reference current revision")
        self._revisions[key]=revision; self._current[revision.draft_id]=revision
    def fetch(self,draft_id,revision_id): return self._revisions.get((draft_id,revision_id))
    def fetch_current(self,draft_id): return self._current.get(draft_id)
    def get_idempotency(self,draft_id,key): return self._idempotency.get((draft_id,key))
    def bind_idempotency(self,draft_id,key,digest,result):
        existing = self._idempotency.get((draft_id, key))
        if existing is not None and existing != (digest, result):
            raise ValueError("idempotency records are immutable")
        self._idempotency[(draft_id,key)]=(digest,result)

    def transition(self,command:TransitionCommand,completed_at)->TransitionResult:
        record=self.get_idempotency(command.draft_id,command.idempotency_key)
        if record:
            digest,result=record
            if digest==command.command_digest: return replay_result(result)
            rejected = replace(
                result,
                outcome=TransitionOutcome.REJECTED_IDEMPOTENCY_KEY_REUSE,
                command_digest=command.command_digest,
                result_digest=command.command_digest,
            )
            seed = {
                name: getattr(rejected, name)
                for name in rejected.__dataclass_fields__
                if name != "result_digest"
            }
            return replace(rejected, result_digest=sha256_digest(seed))
        revision=self.fetch_current(command.draft_id)
        if revision is None: raise KeyError(command.draft_id)
        result=evaluate_transition(revision,command,completed_at)
        if result.outcome is TransitionOutcome.APPLIED:
            updated=revision.with_state(result.state); self._revisions[(updated.draft_id,updated.revision_id)]=updated; self._current[updated.draft_id]=updated
        self.bind_idempotency(command.draft_id,command.idempotency_key,command.command_digest,result)
        return result

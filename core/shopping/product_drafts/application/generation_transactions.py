"""Narrow application contract for durable generation coordination."""
from __future__ import annotations

from typing import Protocol

from .generation import GenerationOperationClaim, ProductDraftGenerationResult


class DurableGenerationTransactionPort(Protocol):
    def claim(self, key: str, command_digest: str, draft_id: str,
              revision_id: str) -> GenerationOperationClaim: ...
    def complete(self, key: str, command_digest: str, result: ProductDraftGenerationResult) -> None: ...
    def fail(self, key: str, command_digest: str) -> None: ...
    def replay_generation(self, key: str, command_digest: str) -> ProductDraftGenerationResult | None: ...


__all__ = ("DurableGenerationTransactionPort",)

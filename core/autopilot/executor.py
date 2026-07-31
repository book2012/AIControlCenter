"""Bounded executor port only; AUTO-01 supplies no adapter or runtime."""

from __future__ import annotations

from typing import Protocol

from .models import ExecutorRequest, ExecutorResult


class BoundedExecutorPort(Protocol):
    @property
    def identity(self) -> str: ...

    def describe(self, request: ExecutorRequest) -> ExecutorResult: ...

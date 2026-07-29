"""Mac-only, non-production sandbox adapter."""

from core.deployment.sandbox_adapter.mac import MacSandboxAdapter, SandboxAdapterError

__all__ = ("MacSandboxAdapter", "SandboxAdapterError")

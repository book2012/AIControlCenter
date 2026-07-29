"""Process-local replay protection for deterministic simulation composition."""

from __future__ import annotations

from threading import Lock


class InMemoryReplayGuard:
    """Dependency-injected, process-local, single-use authorization guard."""

    def __init__(self) -> None:
        self._consumed: set[str] = set()
        self._lock = Lock()

    def consume(self, authorization_id: str, nonce: str) -> bool:
        key_pairs = (f"authorization:{authorization_id}", f"nonce:{nonce}")
        with self._lock:
            if any(key in self._consumed for key in key_pairs):
                return False
            self._consumed.update(key_pairs)
            return True


__all__ = ("InMemoryReplayGuard",)

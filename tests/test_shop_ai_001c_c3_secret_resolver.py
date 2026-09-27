from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
import copy
import pickle
import ast
from pathlib import Path

import pytest

from core.secrets.ports import (
    EphemeralSecretLease, SecretLeaseConsumed, SecretLeaseExpired,
    SecretReference, SecretResolutionError,
)
from ops.macos.shopping.provider_secret_resolver import ProviderSecretResolver


REFERENCE = SecretReference(backend="macos.keychain", key_name="shopping.provider")


def test_secret_reference_and_lease_are_value_free_until_one_shot_consume() -> None:
    lease = EphemeralSecretLease("provider-secret")
    assert "provider-secret" not in repr(lease)
    assert "provider-secret" not in str(lease)
    assert lease.consume() == "provider-secret"
    with pytest.raises(SecretLeaseConsumed):
        lease.consume()
    with pytest.raises(TypeError):
        copy.copy(lease)
    with pytest.raises(TypeError):
        pickle.dumps(lease)
    assert not hasattr(lease, "model_dump")


def test_mac_resolver_uses_only_an_injected_reader_and_never_mutates_environment() -> None:
    calls = []
    before = dict(os.environ)
    resolver = ProviderSecretResolver(lambda reference: calls.append(reference) or b"secret")
    assert calls == []
    lease = resolver.resolve(REFERENCE)
    assert calls == [REFERENCE]
    assert lease.consume() == b"secret"
    assert dict(os.environ) == before


def test_secret_reader_failures_are_sanitized_and_invalid_material_is_rejected() -> None:
    inert = ProviderSecretResolver()
    with pytest.raises(SecretResolutionError):
        inert.resolve(REFERENCE)
    resolver = ProviderSecretResolver(lambda reference: (_ for _ in ()).throw(
        RuntimeError("raw secret provider-secret"),
    ))
    with pytest.raises(RuntimeError) as error:
        resolver.resolve(REFERENCE)
    assert "provider-secret" not in str(error.value)
    assert "provider-secret" not in repr(error.value)

    invalid = ProviderSecretResolver(lambda reference: "")
    with pytest.raises(RuntimeError):
        invalid.resolve(REFERENCE)


def test_secret_lease_expiry_uses_injected_utc_clock_and_releases_material() -> None:
    current = [datetime(2026, 9, 27, 12, 0, tzinfo=timezone.utc)]
    resolver = ProviderSecretResolver(
        lambda reference: "secret", utc_clock=lambda: current[0],
        lease_ttl=timedelta(minutes=1),
    )
    lease = resolver.resolve(REFERENCE)
    current[0] += timedelta(minutes=1)
    with pytest.raises(SecretLeaseExpired):
        lease.consume()
    with pytest.raises(SecretLeaseConsumed):
        lease.consume()


def test_mac_foundation_has_no_host_or_network_secret_access() -> None:
    path = Path(__file__).parents[1] / "ops/macos/shopping/provider_secret_resolver.py"
    tree = ast.parse(path.read_text())
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    rendered = "\n".join(imports).lower()
    for forbidden in (
        "subprocess", "requests", "httpx", "urllib", "socket", "keyring",
        "security", "boto", "twilio", "vonage", "messagebird",
    ):
        assert forbidden not in rendered

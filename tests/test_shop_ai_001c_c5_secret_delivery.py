from __future__ import annotations

from core.secrets.ports import SecretReference
from core.shopping.ports.provider_activation import SecretDeliveryContract
from ops.macos.shopping.provider_integration_composition import (
    build_disabled_provider_integration,
)


REFERENCE = SecretReference(backend="macos.keychain", key_name="future.provider")


def test_secret_delivery_contract_is_metadata_only() -> None:
    contract = SecretDeliveryContract(reference=REFERENCE)
    assert contract.reference.to_dict() == {
        "backend": "macos.keychain", "key_name": "future.provider",
    }
    assert contract.lease_required is True
    assert contract.consumer_boundary == "PROVIDER_SPECIFIC_TRANSPORT_ONLY"
    rendered = repr(contract)
    assert rendered == "SecretDeliveryContract(<metadata-only>)"
    assert REFERENCE.backend not in rendered
    assert REFERENCE.key_name not in rendered


def test_disabled_composition_never_resolves_secret_material() -> None:
    calls = []

    class Resolver:
        def resolve(self, reference):
            calls.append(reference)
            raise AssertionError("C5-B must not resolve credentials")

    composition = build_disabled_provider_integration()
    metadata = composition.secret_delivery_contract(REFERENCE)
    assert metadata.reference == REFERENCE
    assert composition.secret_resolver is None
    assert composition.credential_resolution_performed is False
    assert calls == []

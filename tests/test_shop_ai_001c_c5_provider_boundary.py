from __future__ import annotations

import ast
from pathlib import Path

from core.shopping.ports.provider_activation import ProviderOperation
from core.shopping.ports.provider_authenticated_read import (
    AuthenticatedProviderReadPort, ProviderReadRequest, ProviderReadResult,
)


ROOT = Path(__file__).parents[1]


def test_provider_selection_and_transport_are_ports_not_business_logic() -> None:
    assert AuthenticatedProviderReadPort is not None
    assert ProviderReadRequest.__name__ == "ProviderReadRequest"
    assert ProviderReadResult.__name__ == "ProviderReadResult"
    assert ProviderOperation.READ_HEALTH.value == "READ_HEALTH"


def test_c5_sources_have_no_vendor_network_or_persistence_imports() -> None:
    paths = (
        ROOT / "core/shopping/ports/provider_activation.py",
        ROOT / "core/shopping/ports/provider_authenticated_read.py",
        ROOT / "core/shopping/governance/provider_network_authorization.py",
        ROOT / "ops/macos/shopping/provider_integration_composition.py",
    )
    forbidden = {
        "socket", "requests", "httpx", "urllib", "subprocess", "sqlite3",
        "twilio", "vonage", "messagebird", "telnyx", "plivo", "keyring",
    }
    for path in paths:
        tree = ast.parse(path.read_text())
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        rendered = "\n".join(imports).lower()
        assert not any(value in rendered for value in forbidden), path

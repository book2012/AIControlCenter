from __future__ import annotations

from pathlib import Path

import pytest

from core.governance.control_plane.contracts import (
    CONTRACT_NAMES,
    SCHEMA_FAMILY_VERSION,
    UnknownGovernanceContractError,
    load_contract_registry,
)


def test_registry_is_exact_deterministic_and_unique() -> None:
    registry = load_contract_registry()
    assert registry.contract_names == CONTRACT_NAMES
    assert len(CONTRACT_NAMES) == 16
    assert len(set(CONTRACT_NAMES)) == 16
    bindings = tuple(registry.contracts.values())
    assert len({item.resource_name for item in bindings}) == 16
    assert len({item.schema_id for item in bindings}) == 16
    assert all(item.schema_version == SCHEMA_FAMILY_VERSION for item in bindings)


def test_registry_resources_exist_and_use_draft_2020_12() -> None:
    registry = load_contract_registry()
    for binding in registry.contracts.values():
        assert (registry.schema_root / binding.resource_name).is_file()
        assert registry.contract_schema(binding.contract_name)["$schema"] == (
            "https://json-schema.org/draft/2020-12/schema"
        )


def test_unknown_contract_fails_closed() -> None:
    with pytest.raises(UnknownGovernanceContractError):
        load_contract_registry().contract_schema("UnknownGovernanceContract")


def test_lookup_returns_isolated_schema_copy() -> None:
    registry = load_contract_registry()
    first = registry.contract_schema(CONTRACT_NAMES[0])
    first["title"] = "mutated-by-caller"
    first["properties"]["request_id"]["description"] = "also mutated"
    second = registry.contract_schema(CONTRACT_NAMES[0])
    assert second["title"] == CONTRACT_NAMES[0]
    assert "description" not in second["properties"]["request_id"]


def test_custom_root_cannot_substitute_missing_resources(tmp_path: Path) -> None:
    with pytest.raises(Exception):
        load_contract_registry(schema_root=tmp_path)

from __future__ import annotations

import ast
import json
import math
from pathlib import Path

import pytest

from core.shopping.contracts.snapshot_normalization import (
    CANONICAL_SNAPSHOT_CONTRACTS,
    NormalizedSnapshot,
    SnapshotNormalizationContractError,
    normalize_snapshot,
    snapshot_normalization_contract_manifest,
)


CONTRACT = "SnapshotEnvelope"
EXPECTED_CONTRACTS = ["SnapshotEnvelope", "SnapshotEnvelopePage"]
EXPECTED_SCHEMA_IDS = ["urn:aicontrolcenter:shopping:contract:v1:content-snapshot", "urn:aicontrolcenter:shopping:contract:v1:content-snapshot-page", "urn:aicontrolcenter:shopping:contract:v1:product-snapshot", "urn:aicontrolcenter:shopping:contract:v1:product-snapshot-page", "urn:aicontrolcenter:shopping:contract:v1:snapshot-envelope", "urn:aicontrolcenter:shopping:contract:v1:snapshot-envelope-page"]


def test_manifest_is_pure_read_only_and_stateless():
    manifest = (
        snapshot_normalization_contract_manifest()
    )

    assert manifest[
        "authoritative_port"
    ] == "SnapshotRepositoryPort"

    assert manifest[
        "pure_normalization"
    ] is True

    assert manifest[
        "immutable_read_model"
    ] is True

    assert manifest[
        "persistence"
    ] is False

    assert manifest[
        "database_write"
    ] is False

    assert manifest[
        "filesystem_write"
    ] is False

    assert manifest[
        "network"
    ] is False

    assert manifest[
        "write_methods_allowed"
    ] is False

    assert manifest[
        "schema_validation"
    ] == "deferred_to_SPF-009"


def test_manifest_uses_inventory_contracts_and_schema_ids():
    manifest = (
        snapshot_normalization_contract_manifest()
    )

    assert manifest[
        "canonical_contracts"
    ] == EXPECTED_CONTRACTS

    assert manifest[
        "canonical_schema_ids"
    ] == EXPECTED_SCHEMA_IDS

    assert set(
        CANONICAL_SNAPSHOT_CONTRACTS
    ) == set(
        EXPECTED_CONTRACTS
    )


def test_normalize_returns_immutable_read_model():
    result = normalize_snapshot(
        contract=CONTRACT,
        payload={
            "snapshot_id": "snapshot-1",
            "value": 1,
        },
    )

    assert isinstance(
        result,
        NormalizedSnapshot,
    )

    assert result.contract == CONTRACT


def test_serialization_is_deterministic():
    first = normalize_snapshot(
        contract=CONTRACT,
        payload={
            "z": 1,
            "a": 2,
        },
    )

    second = normalize_snapshot(
        contract=CONTRACT,
        payload={
            "a": 2,
            "z": 1,
        },
    )

    assert (
        first.canonical_json
        == second.canonical_json
    )


def test_input_is_deep_copied():
    payload = {
        "snapshot_id": "snapshot-1",
        "nested": {
            "items": [
                {
                    "value": 1,
                }
            ],
        },
    }

    result = normalize_snapshot(
        contract=CONTRACT,
        payload=payload,
    )

    before = result.to_json()

    payload[
        "nested"
    ][
        "items"
    ][0][
        "value"
    ] = 999

    assert result.to_json() == before


def test_to_json_returns_independent_copy():
    result = normalize_snapshot(
        contract=CONTRACT,
        payload={
            "snapshot_id": "snapshot-1",
            "nested": {
                "value": 1,
            },
        },
    )

    first = result.to_json()

    first[
        "nested"
    ][
        "value"
    ] = 999

    second = result.to_json()

    assert second[
        "nested"
    ][
        "value"
    ] == 1


def test_unknown_contract_is_rejected():
    with pytest.raises(
        SnapshotNormalizationContractError,
        match=(
            "shopping.snapshot.unknown_contract"
        ),
    ):
        normalize_snapshot(
            contract=(
                "VendorPrivateSnapshot"
            ),
            payload={},
        )


def test_top_level_non_object_is_rejected():
    with pytest.raises(
        SnapshotNormalizationContractError,
        match=(
            "shopping.snapshot.object_required"
        ),
    ):
        normalize_snapshot(
            contract=CONTRACT,
            payload=[],
        )


def test_nested_non_json_value_is_rejected():
    with pytest.raises(
        SnapshotNormalizationContractError,
        match=(
            "shopping.snapshot.non_json_value"
        ),
    ):
        normalize_snapshot(
            contract=CONTRACT,
            payload={
                "unsafe": object(),
            },
        )


def test_non_finite_number_is_rejected():
    for value in (
        math.nan,
        math.inf,
        -math.inf,
    ):
        with pytest.raises(
            SnapshotNormalizationContractError,
            match=(
                "shopping.snapshot.non_finite_number"
            ),
        ):
            normalize_snapshot(
                contract=CONTRACT,
                payload={
                    "value": value,
                },
            )


def test_canonical_bytes_are_stable_utf8_json():
    result = normalize_snapshot(
        contract=CONTRACT,
        payload={
            "name": "쇼핑",
            "value": 1,
        },
    )

    assert (
        result.canonical_bytes
        == result.canonical_json.encode(
            "utf-8"
        )
    )

    assert (
        json.loads(
            result.canonical_bytes
            .decode(
                "utf-8"
            )
        )
        == result.to_json()
    )


def test_module_has_no_network_persistence_or_environment_imports():
    path = Path(
        "core/shopping/contracts/snapshot_normalization.py"
    )

    tree = ast.parse(
        path.read_text(
            encoding="utf-8"
        )
    )

    forbidden = {
        "aiohttp",
        "httpx",
        "os",
        "pathlib",
        "redis",
        "requests",
        "shelve",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "subprocess",
        "urllib",
    }

    imported = set()

    for node in ast.walk(
        tree
    ):
        if isinstance(
            node,
            ast.Import,
        ):
            for item in node.names:
                imported.add(
                    item.name.split(
                        "."
                    )[0]
                )

        elif (
            isinstance(
                node,
                ast.ImportFrom,
            )
            and node.module
        ):
            imported.add(
                node.module.split(
                    "."
                )[0]
            )

    assert not (
        imported
        & forbidden
    )

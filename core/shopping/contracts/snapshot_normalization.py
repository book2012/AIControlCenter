from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


class SnapshotNormalizationContractError(
    ValueError
):
    pass


CANONICAL_SNAPSHOT_CONTRACTS = frozenset(
    ["SnapshotEnvelope", "SnapshotEnvelopePage"]
)

CANONICAL_SNAPSHOT_SCHEMA_IDS = tuple(
    ["urn:aicontrolcenter:shopping:contract:v1:content-snapshot", "urn:aicontrolcenter:shopping:contract:v1:content-snapshot-page", "urn:aicontrolcenter:shopping:contract:v1:product-snapshot", "urn:aicontrolcenter:shopping:contract:v1:product-snapshot-page", "urn:aicontrolcenter:shopping:contract:v1:snapshot-envelope", "urn:aicontrolcenter:shopping:contract:v1:snapshot-envelope-page"]
)

CANONICAL_SNAPSHOT_SCHEMA_PATHS = tuple(
    ["core/shopping/contracts/schemas/v1/content-snapshot-page.schema.json", "core/shopping/contracts/schemas/v1/content-snapshot.schema.json", "core/shopping/contracts/schemas/v1/product-snapshot-page.schema.json", "core/shopping/contracts/schemas/v1/product-snapshot.schema.json", "core/shopping/contracts/schemas/v1/snapshot-envelope-page.schema.json", "core/shopping/contracts/schemas/v1/snapshot-envelope.schema.json"]
)


def _copy_json_value(
    value: Any,
) -> Any:
    if value is None:
        return None

    if isinstance(
        value,
        bool,
    ):
        return value

    if isinstance(
        value,
        int,
    ):
        return value

    if isinstance(
        value,
        float,
    ):
        if not math.isfinite(
            value
        ):
            raise SnapshotNormalizationContractError(
                "shopping.snapshot.non_finite_number"
            )

        return value

    if isinstance(
        value,
        str,
    ):
        return value

    if isinstance(
        value,
        Mapping,
    ):
        copied = {}

        for key, child in value.items():
            if not isinstance(
                key,
                str,
            ):
                raise SnapshotNormalizationContractError(
                    "shopping.snapshot.non_string_key"
                )

            copied[
                key
            ] = _copy_json_value(
                child
            )

        return copied

    if isinstance(
        value,
        list,
    ):
        return [
            _copy_json_value(
                child
            )
            for child in value
        ]

    raise SnapshotNormalizationContractError(
        "shopping.snapshot.non_json_value"
    )


@dataclass(
    frozen=True,
    slots=True,
)
class NormalizedSnapshot:
    contract: str
    _canonical_json: str

    @property
    def canonical_json(
        self,
    ) -> str:
        return self._canonical_json

    @property
    def canonical_bytes(
        self,
    ) -> bytes:
        return self._canonical_json.encode(
            "utf-8"
        )

    def to_json(
        self,
    ) -> dict[str, Any]:
        value = json.loads(
            self._canonical_json
        )

        if not isinstance(
            value,
            dict,
        ):
            raise RuntimeError(
                "normalized snapshot root invariant violated"
            )

        return value


def normalize_snapshot(
    *,
    contract: str,
    payload: Mapping[str, Any],
) -> NormalizedSnapshot:
    if (
        not isinstance(
            contract,
            str,
        )
        or contract
        not in CANONICAL_SNAPSHOT_CONTRACTS
    ):
        raise SnapshotNormalizationContractError(
            "shopping.snapshot.unknown_contract"
        )

    if not isinstance(
        payload,
        Mapping,
    ):
        raise SnapshotNormalizationContractError(
            "shopping.snapshot.object_required"
        )

    copied = _copy_json_value(
        payload
    )

    try:
        canonical_json = json.dumps(
            copied,
            allow_nan=False,
            ensure_ascii=False,
            separators=(
                ",",
                ":",
            ),
            sort_keys=True,
        )
    except (
        TypeError,
        ValueError,
    ):
        raise SnapshotNormalizationContractError(
            "shopping.snapshot.serialization_error"
        ) from None

    return NormalizedSnapshot(
        contract=contract,
        _canonical_json=canonical_json,
    )


def snapshot_normalization_contract_manifest(
) -> dict[str, Any]:
    return {
        "authoritative_port": (
            "SnapshotRepositoryPort"
        ),
        "canonical_contracts": sorted(
            CANONICAL_SNAPSHOT_CONTRACTS
        ),
        "canonical_schema_ids": list(
            CANONICAL_SNAPSHOT_SCHEMA_IDS
        ),
        "canonical_schema_paths": list(
            CANONICAL_SNAPSHOT_SCHEMA_PATHS
        ),
        "database_write": False,
        "deterministic": True,
        "filesystem_write": False,
        "immutable_read_model": True,
        "input_mutation": False,
        "network": False,
        "persistence": False,
        "pure_normalization": True,
        "schema_validation": (
            "deferred_to_SPF-009"
        ),
        "snapshot_creation": False,
        "snapshot_delete": False,
        "snapshot_update": False,
        "write_methods_allowed": False,
    }


__all__ = (
    "CANONICAL_SNAPSHOT_CONTRACTS",
    "CANONICAL_SNAPSHOT_SCHEMA_IDS",
    "CANONICAL_SNAPSHOT_SCHEMA_PATHS",
    "NormalizedSnapshot",
    "SnapshotNormalizationContractError",
    "normalize_snapshot",
    "snapshot_normalization_contract_manifest",
)

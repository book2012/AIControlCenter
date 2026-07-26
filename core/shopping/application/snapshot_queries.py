from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from core.shopping.contracts.snapshot_normalization import (
    NormalizedSnapshot,
    normalize_snapshot,
)


class SnapshotQueryContractError(ValueError):
    pass


class SnapshotQueryDenied(PermissionError):
    pass


ReadAuthorizationCallable = Callable[
    [str],
    Awaitable[bool],
]


CAPABILITY_BY_METHOD = MappingProxyType(
    {'get_latest_snapshot': 'shopping.snapshot.get', 'list_snapshots': 'shopping.snapshot.list'}
)

CONTRACT_BY_METHOD = MappingProxyType(
    {'get_latest_snapshot': 'SnapshotEnvelope', 'list_snapshots': 'SnapshotEnvelopePage'}
)

ARGUMENTS_BY_METHOD = MappingProxyType(
    {
        key: tuple(value)
        for key, value
        in {'get_latest_snapshot': ['context', 'external_id', 'snapshot_type'], 'list_snapshots': ['context', 'page', 'snapshot_type']}.items()
    }
)

REQUIRED_ARGUMENTS_BY_METHOD = MappingProxyType(
    {
        key: frozenset(value)
        for key, value
        in {'get_latest_snapshot': ['context', 'external_id', 'snapshot_type'], 'list_snapshots': ['context', 'page', 'snapshot_type']}.items()
    }
)

ALLOWS_NONE_BY_METHOD = MappingProxyType(
    {'get_latest_snapshot': True, 'list_snapshots': False}
)


@dataclass(
    frozen=True,
    slots=True,
)
class SnapshotQueryResult:
    method: str
    capability_id: str
    snapshot: NormalizedSnapshot

    def to_json(
        self,
    ) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "method": self.method,
            "snapshot": self.snapshot.to_json(),
        }


async def execute_snapshot_query(
    *,
    repository: Any,
    authorize: ReadAuthorizationCallable,
    method: str,
    arguments: Mapping[str, Any],
) -> SnapshotQueryResult | None:
    if (
        not isinstance(
            method,
            str,
        )
        or method
        not in CAPABILITY_BY_METHOD
    ):
        raise SnapshotQueryContractError(
            "shopping.snapshot.query.unknown_method"
        )

    if not isinstance(
        arguments,
        Mapping,
    ):
        raise SnapshotQueryContractError(
            "shopping.snapshot.query.arguments_mapping_required"
        )

    supplied = set(arguments)

    if not all(
        isinstance(
            key,
            str,
        )
        for key in supplied
    ):
        raise SnapshotQueryContractError(
            "shopping.snapshot.query.invalid_argument_name"
        )

    allowed = set(
        ARGUMENTS_BY_METHOD[
            method
        ]
    )

    if supplied - allowed:
        raise SnapshotQueryContractError(
            "shopping.snapshot.query.unknown_argument"
        )

    if (
        REQUIRED_ARGUMENTS_BY_METHOD[
            method
        ]
        - supplied
    ):
        raise SnapshotQueryContractError(
            "shopping.snapshot.query.required_argument_missing"
        )

    capability_id = CAPABILITY_BY_METHOD[
        method
    ]

    try:
        authorized = await authorize(
            capability_id
        )
    except Exception:
        raise SnapshotQueryDenied(
            "shopping.snapshot.authorization_error"
        ) from None

    if authorized is not True:
        raise SnapshotQueryDenied(
            "shopping.snapshot.authorization_denied"
        )

    repository_method = getattr(
        repository,
        method,
        None,
    )

    if not callable(
        repository_method
    ):
        raise SnapshotQueryContractError(
            "shopping.snapshot.query.repository_method_unavailable"
        )

    try:
        payload = await repository_method(
            **dict(arguments)
        )
    except Exception:
        raise SnapshotQueryContractError(
            "shopping.snapshot.query.repository_error"
        ) from None

    if payload is None:
        if ALLOWS_NONE_BY_METHOD[
            method
        ]:
            return None

        raise SnapshotQueryContractError(
            "shopping.snapshot.query.unexpected_none"
        )

    if not isinstance(
        payload,
        Mapping,
    ):
        raise SnapshotQueryContractError(
            "shopping.snapshot.query.canonical_object_required"
        )

    snapshot = normalize_snapshot(
        contract=CONTRACT_BY_METHOD[
            method
        ],
        payload=payload,
    )

    return SnapshotQueryResult(
        method=method,
        capability_id=capability_id,
        snapshot=snapshot,
    )


def snapshot_query_contract_manifest(
) -> dict[str, Any]:
    return {
        "allows_none_by_method": dict(
            ALLOWS_NONE_BY_METHOD
        ),
        "arguments_by_method": {
            key: list(value)
            for key, value
            in ARGUMENTS_BY_METHOD.items()
        },
        "authorization_before_repository": True,
        "authorization_boundary": (
            "injected existing read_authorization adapter"
        ),
        "capability_by_method": dict(
            CAPABILITY_BY_METHOD
        ),
        "contract_by_method": dict(
            CONTRACT_BY_METHOD
        ),
        "duplicate_authorization_framework": False,
        "network": False,
        "persistence": False,
        "production_registration": False,
        "repository_injected": True,
        "repository_owns_authorization": False,
        "required_arguments_by_method": {
            key: sorted(value)
            for key, value
            in REQUIRED_ARGUMENTS_BY_METHOD.items()
        },
        "snapshot_creation": False,
        "vendor_refresh": False,
        "write_methods_allowed": False,
    }


__all__ = (
    "ALLOWS_NONE_BY_METHOD",
    "ARGUMENTS_BY_METHOD",
    "CAPABILITY_BY_METHOD",
    "CONTRACT_BY_METHOD",
    "REQUIRED_ARGUMENTS_BY_METHOD",
    "ReadAuthorizationCallable",
    "SnapshotQueryContractError",
    "SnapshotQueryDenied",
    "SnapshotQueryResult",
    "execute_snapshot_query",
    "snapshot_query_contract_manifest",
)

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any

from jsonschema import Draft202012Validator


class DriftStatus(
    str,
    Enum,
):
    NO_DRIFT = "NO_DRIFT"
    COMPATIBLE_DRIFT = "COMPATIBLE_DRIFT"
    BREAKING_DRIFT = "BREAKING_DRIFT"
    UNKNOWN_DRIFT = "UNKNOWN_DRIFT"


@dataclass(
    frozen=True,
    slots=True,
)
class DriftChange:
    code: str
    direction: str
    schema_path: tuple[
        str | int,
        ...,
    ]

    def to_json(
        self,
    ) -> dict[str, Any]:
        return {
            "code": self.code,
            "direction": self.direction,
            "schema_path": list(
                self.schema_path
            ),
        }


@dataclass(
    frozen=True,
    slots=True,
)
class DriftResult:
    status: DriftStatus
    changes: tuple[
        DriftChange,
        ...,
    ]

    @property
    def auto_adopt(
        self,
    ) -> bool:
        return False

    def to_json(
        self,
    ) -> dict[str, Any]:
        return {
            "auto_adopt": False,
            "changes": [
                change.to_json()
                for change
                in self.changes
            ],
            "status": self.status.value,
        }


_METADATA_KEYS = frozenset(
    {
        "$comment",
        "default",
        "deprecated",
        "description",
        "examples",
        "readOnly",
        "title",
        "writeOnly",
    }
)

_MINIMUM_KEYS = frozenset(
    {
        "exclusiveMinimum",
        "minContains",
        "minItems",
        "minLength",
        "minProperties",
        "minimum",
    }
)

_MAXIMUM_KEYS = frozenset(
    {
        "exclusiveMaximum",
        "maxContains",
        "maxItems",
        "maxLength",
        "maxProperties",
        "maximum",
    }
)

_COMPLEX_KEYS = frozenset(
    {
        "$defs",
        "$dynamicAnchor",
        "$dynamicRef",
        "$recursiveAnchor",
        "$recursiveRef",
        "allOf",
        "anyOf",
        "contains",
        "contentEncoding",
        "contentMediaType",
        "contentSchema",
        "dependentRequired",
        "dependentSchemas",
        "else",
        "format",
        "if",
        "multipleOf",
        "not",
        "oneOf",
        "pattern",
        "patternProperties",
        "prefixItems",
        "propertyNames",
        "then",
        "unevaluatedItems",
        "unevaluatedProperties",
    }
)

_RECOGNIZED_KEYS = frozenset(
    {
        "$id",
        "$schema",
        "additionalProperties",
        "const",
        "enum",
        "items",
        "properties",
        "required",
        "type",
        "uniqueItems",
    }
) | _METADATA_KEYS | _MINIMUM_KEYS | _MAXIMUM_KEYS | _COMPLEX_KEYS


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
    ) and not isinstance(
        value,
        bool,
    ):
        return value

    if isinstance(
        value,
        float,
    ):
        if not math.isfinite(
            value
        ):
            raise ValueError(
                "shopping.schema.drift.non_json_value"
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
                raise ValueError(
                    "shopping.schema.drift.non_json_value"
                )

            copied[
                key
            ] = _copy_json_value(
                child
            )

        return copied

    if isinstance(
        value,
        (
            list,
            tuple,
        ),
    ):
        return [
            _copy_json_value(
                child
            )
            for child
            in value
        ]

    raise ValueError(
        "shopping.schema.drift.non_json_value"
    )


def _canonical_bytes(
    value: Any,
) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(
            ",",
            ":",
        ),
        sort_keys=True,
    ).encode(
        "utf-8"
    )


def _collect_refs(
    node: Any,
) -> tuple[str, ...]:
    refs: list[str] = []

    def walk(
        value: Any,
    ) -> None:
        if isinstance(
            value,
            Mapping,
        ):
            for key, child in value.items():
                if (
                    key == "$ref"
                    and isinstance(
                        child,
                        str,
                    )
                ):
                    refs.append(
                        child
                    )
                else:
                    walk(
                        child
                    )

        elif isinstance(
            value,
            list,
        ):
            for child in value:
                walk(
                    child
                )

    walk(
        node
    )

    return tuple(
        refs
    )


def _has_remote_ref(
    node: Any,
) -> bool:
    return any(
        ref.startswith(
            "http://"
        )
        or ref.startswith(
            "https://"
        )
        for ref
        in _collect_refs(
            node
        )
    )


def _change(
    changes: list[
        DriftChange
    ],
    *,
    code: str,
    direction: str,
    path: tuple[
        str | int,
        ...,
    ],
) -> None:
    changes.append(
        DriftChange(
            code=code,
            direction=direction,
            schema_path=path,
        )
    )


def _type_set(
    value: Any,
) -> set[str] | None:
    if isinstance(
        value,
        str,
    ):
        return {
            value,
        }

    if (
        isinstance(
            value,
            list,
        )
        and all(
            isinstance(
                item,
                str,
            )
            for item
            in value
        )
    ):
        return set(
            value
        )

    return None


def _compare_bound(
    *,
    canonical_present: bool,
    candidate_present: bool,
    canonical_value: Any,
    candidate_value: Any,
    minimum: bool,
    path: tuple[
        str | int,
        ...,
    ],
    code: str,
    changes: list[
        DriftChange
    ],
) -> None:
    if (
        not canonical_present
        and not candidate_present
    ):
        return

    if (
        canonical_present
        and candidate_present
        and canonical_value
        == candidate_value
    ):
        return

    if (
        not canonical_present
        and candidate_present
    ):
        _change(
            changes,
            code=code,
            direction="compatible",
            path=path,
        )
        return

    if (
        canonical_present
        and not candidate_present
    ):
        _change(
            changes,
            code=code,
            direction="breaking",
            path=path,
        )
        return

    if (
        isinstance(
            canonical_value,
            (
                int,
                float,
            ),
        )
        and not isinstance(
            canonical_value,
            bool,
        )
        and isinstance(
            candidate_value,
            (
                int,
                float,
            ),
        )
        and not isinstance(
            candidate_value,
            bool,
        )
    ):
        if minimum:
            direction = (
                "compatible"
                if candidate_value
                > canonical_value
                else "breaking"
            )
        else:
            direction = (
                "compatible"
                if candidate_value
                < canonical_value
                else "breaking"
            )

        _change(
            changes,
            code=code,
            direction=direction,
            path=path,
        )
        return

    _change(
        changes,
        code=code,
        direction="unknown",
        path=path,
    )


def _compare_subschema(
    canonical: Any,
    candidate: Any,
    *,
    path: tuple[
        str | int,
        ...,
    ],
    changes: list[
        DriftChange
    ],
) -> None:
    if canonical == candidate:
        return

    if isinstance(
        canonical,
        bool,
    ) or isinstance(
        candidate,
        bool,
    ):
        if canonical is True:
            _change(
                changes,
                code=(
                    "shopping.schema.drift.subschema_narrowed"
                ),
                direction="compatible",
                path=path,
            )
            return

        if candidate is True:
            _change(
                changes,
                code=(
                    "shopping.schema.drift.subschema_widened"
                ),
                direction="breaking",
                path=path,
            )
            return

        if candidate is False:
            _change(
                changes,
                code=(
                    "shopping.schema.drift.subschema_narrowed"
                ),
                direction="compatible",
                path=path,
            )
            return

        if canonical is False:
            _change(
                changes,
                code=(
                    "shopping.schema.drift.subschema_widened"
                ),
                direction="breaking",
                path=path,
            )
            return

    if (
        not isinstance(
            canonical,
            Mapping,
        )
        or not isinstance(
            candidate,
            Mapping,
        )
    ):
        _change(
            changes,
            code=(
                "shopping.schema.drift.unsupported_subschema"
            ),
            direction="unknown",
            path=path,
        )
        return

    _compare_mapping(
        canonical,
        candidate,
        path=path,
        changes=changes,
    )


def _compare_mapping(
    canonical: Mapping[
        str,
        Any,
    ],
    candidate: Mapping[
        str,
        Any,
    ],
    *,
    path: tuple[
        str | int,
        ...,
    ],
    changes: list[
        DriftChange
    ],
) -> None:
    if canonical == candidate:
        return

    changed_keys = {
        key
        for key
        in (
            set(
                canonical
            )
            | set(
                candidate
            )
        )
        if canonical.get(
            key,
            object(),
        )
        != candidate.get(
            key,
            object(),
        )
    }

    if (
        changed_keys
        and changed_keys
        <= _METADATA_KEYS
    ):
        _change(
            changes,
            code=(
                "shopping.schema.drift.metadata_only"
            ),
            direction="compatible",
            path=path,
        )
        return

    unsupported = sorted(
        key
        for key
        in changed_keys
        if key
        not in _RECOGNIZED_KEYS
    )

    for key in unsupported:
        _change(
            changes,
            code=(
                "shopping.schema.drift.unsupported_keyword"
            ),
            direction="unknown",
            path=path
            + (
                key,
            ),
        )

    for key in sorted(
        changed_keys
        & _COMPLEX_KEYS
    ):
        _change(
            changes,
            code=(
                "shopping.schema.drift.complex_keyword_change"
            ),
            direction="unknown",
            path=path
            + (
                key,
            ),
        )

    for key in sorted(
        changed_keys
        & _METADATA_KEYS
    ):
        _change(
            changes,
            code=(
                "shopping.schema.drift.metadata_only"
            ),
            direction="compatible",
            path=path
            + (
                key,
            ),
        )

    if "$id" in changed_keys:
        _change(
            changes,
            code=(
                "shopping.schema.drift.schema_id_change"
            ),
            direction="unknown",
            path=path
            + (
                "$id",
            ),
        )

    if "$schema" in changed_keys:
        _change(
            changes,
            code=(
                "shopping.schema.drift.schema_draft_change"
            ),
            direction="unknown",
            path=path
            + (
                "$schema",
            ),
        )

    if "type" in changed_keys:
        canonical_type = _type_set(
            canonical.get(
                "type"
            )
        )

        candidate_type = _type_set(
            candidate.get(
                "type"
            )
        )

        if (
            canonical_type is None
            and candidate_type
        ):
            direction = "compatible"

        elif (
            canonical_type
            and candidate_type is None
        ):
            direction = "breaking"

        elif (
            canonical_type
            and candidate_type
            and candidate_type
            <= canonical_type
        ):
            direction = "compatible"

        elif (
            canonical_type
            and candidate_type
        ):
            direction = "breaking"

        else:
            direction = "unknown"

        _change(
            changes,
            code=(
                "shopping.schema.drift.type_change"
            ),
            direction=direction,
            path=path
            + (
                "type",
            ),
        )

    if "enum" in changed_keys:
        canonical_enum = canonical.get(
            "enum"
        )

        candidate_enum = candidate.get(
            "enum"
        )

        if (
            "enum"
            not in canonical
            and isinstance(
                candidate_enum,
                list,
            )
        ):
            direction = "compatible"

        elif (
            isinstance(
                canonical_enum,
                list,
            )
            and "enum"
            not in candidate
        ):
            direction = "breaking"

        elif (
            isinstance(
                canonical_enum,
                list,
            )
            and isinstance(
                candidate_enum,
                list,
            )
        ):
            canonical_values = {
                _canonical_bytes(
                    item
                )
                for item
                in canonical_enum
            }

            candidate_values = {
                _canonical_bytes(
                    item
                )
                for item
                in candidate_enum
            }

            direction = (
                "compatible"
                if candidate_values
                <= canonical_values
                else "breaking"
            )

        else:
            direction = "unknown"

        _change(
            changes,
            code=(
                "shopping.schema.drift.enum_change"
            ),
            direction=direction,
            path=path
            + (
                "enum",
            ),
        )

    if "const" in changed_keys:
        if (
            "const"
            not in canonical
            and "const"
            in candidate
        ):
            direction = "compatible"

        elif (
            "const"
            in canonical
            and "const"
            not in candidate
        ):
            direction = "breaking"

        else:
            direction = "breaking"

        _change(
            changes,
            code=(
                "shopping.schema.drift.const_change"
            ),
            direction=direction,
            path=path
            + (
                "const",
            ),
        )

    canonical_required = set(
        canonical.get(
            "required",
            [],
        )
        if isinstance(
            canonical.get(
                "required",
                [],
            ),
            list,
        )
        else []
    )

    candidate_required = set(
        candidate.get(
            "required",
            [],
        )
        if isinstance(
            candidate.get(
                "required",
                [],
            ),
            list,
        )
        else []
    )

    canonical_properties = (
        canonical.get(
            "properties",
            {},
        )
    )

    candidate_properties = (
        candidate.get(
            "properties",
            {},
        )
    )

    if not isinstance(
        canonical_properties,
        Mapping,
    ):
        canonical_properties = {}

    if not isinstance(
        candidate_properties,
        Mapping,
    ):
        candidate_properties = {}

    if "required" in changed_keys:
        removed_required = (
            canonical_required
            - candidate_required
        )

        added_required = (
            candidate_required
            - canonical_required
        )

        for name in sorted(
            removed_required
        ):
            _change(
                changes,
                code=(
                    "shopping.schema.drift.required_removed"
                ),
                direction="breaking",
                path=path
                + (
                    "required",
                    name,
                ),
            )

        for name in sorted(
            added_required
        ):
            direction = (
                "compatible"
                if name
                in canonical_properties
                else "breaking"
            )

            code = (
                "shopping.schema.drift.optional_became_required"
                if direction
                == "compatible"
                else "shopping.schema.drift.new_required_property"
            )

            _change(
                changes,
                code=code,
                direction=direction,
                path=path
                + (
                    "required",
                    name,
                ),
            )

    if "additionalProperties" in changed_keys:
        canonical_additional = canonical.get(
            "additionalProperties",
            True,
        )

        candidate_additional = candidate.get(
            "additionalProperties",
            True,
        )

        if (
            canonical_additional
            is True
            and candidate_additional
            is False
        ):
            direction = "compatible"

        elif (
            canonical_additional
            is False
            and candidate_additional
            is True
        ):
            direction = "breaking"

        else:
            direction = "unknown"

        _change(
            changes,
            code=(
                "shopping.schema.drift.additional_properties_change"
            ),
            direction=direction,
            path=path
            + (
                "additionalProperties",
            ),
        )

    if "properties" in changed_keys:
        canonical_names = set(
            canonical_properties
        )

        candidate_names = set(
            candidate_properties
        )

        for name in sorted(
            canonical_names
            - candidate_names
        ):
            _change(
                changes,
                code=(
                    "shopping.schema.drift.optional_property_removed"
                ),
                direction=(
                    "breaking"
                    if name
                    in canonical_required
                    else "compatible"
                ),
                path=path
                + (
                    "properties",
                    name,
                ),
            )

        canonical_additional = canonical.get(
            "additionalProperties",
            True,
        )

        for name in sorted(
            candidate_names
            - canonical_names
        ):
            direction = (
                "breaking"
                if canonical_additional
                is False
                else "compatible"
            )

            _change(
                changes,
                code=(
                    "shopping.schema.drift.property_added"
                ),
                direction=direction,
                path=path
                + (
                    "properties",
                    name,
                ),
            )

        for name in sorted(
            canonical_names
            & candidate_names
        ):
            _compare_subschema(
                canonical_properties[
                    name
                ],
                candidate_properties[
                    name
                ],
                path=path
                + (
                    "properties",
                    name,
                ),
                changes=changes,
            )

    if "items" in changed_keys:
        if (
            "items"
            not in canonical
            and "items"
            in candidate
        ):
            _change(
                changes,
                code=(
                    "shopping.schema.drift.items_constraint_added"
                ),
                direction="compatible",
                path=path
                + (
                    "items",
                ),
            )

        elif (
            "items"
            in canonical
            and "items"
            not in candidate
        ):
            _change(
                changes,
                code=(
                    "shopping.schema.drift.items_constraint_removed"
                ),
                direction="breaking",
                path=path
                + (
                    "items",
                ),
            )

        else:
            _compare_subschema(
                canonical.get(
                    "items"
                ),
                candidate.get(
                    "items"
                ),
                path=path
                + (
                    "items",
                ),
                changes=changes,
            )

    if "uniqueItems" in changed_keys:
        canonical_unique = canonical.get(
            "uniqueItems",
            False,
        )

        candidate_unique = candidate.get(
            "uniqueItems",
            False,
        )

        if (
            canonical_unique
            is False
            and candidate_unique
            is True
        ):
            direction = "compatible"

        elif (
            canonical_unique
            is True
            and candidate_unique
            is False
        ):
            direction = "breaking"

        else:
            direction = "unknown"

        _change(
            changes,
            code=(
                "shopping.schema.drift.unique_items_change"
            ),
            direction=direction,
            path=path
            + (
                "uniqueItems",
            ),
        )

    for key in sorted(
        _MINIMUM_KEYS
    ):
        if (
            canonical.get(
                key,
                object(),
            )
            != candidate.get(
                key,
                object(),
            )
        ):
            _compare_bound(
                canonical_present=(
                    key in canonical
                ),
                candidate_present=(
                    key in candidate
                ),
                canonical_value=canonical.get(
                    key
                ),
                candidate_value=candidate.get(
                    key
                ),
                minimum=True,
                path=path
                + (
                    key,
                ),
                code=(
                    "shopping.schema.drift.constraint_change"
                ),
                changes=changes,
            )

    for key in sorted(
        _MAXIMUM_KEYS
    ):
        if (
            canonical.get(
                key,
                object(),
            )
            != candidate.get(
                key,
                object(),
            )
        ):
            _compare_bound(
                canonical_present=(
                    key in canonical
                ),
                candidate_present=(
                    key in candidate
                ),
                canonical_value=canonical.get(
                    key
                ),
                candidate_value=candidate.get(
                    key
                ),
                minimum=False,
                path=path
                + (
                    key,
                ),
                code=(
                    "shopping.schema.drift.constraint_change"
                ),
                changes=changes,
            )


def _result_from_changes(
    changes: list[
        DriftChange
    ],
) -> DriftResult:
    ordered = tuple(
        sorted(
            changes,
            key=lambda change: (
                tuple(
                    str(
                        part
                    )
                    for part
                    in change.schema_path
                ),
                change.direction,
                change.code,
            ),
        )
    )

    directions = {
        change.direction
        for change
        in ordered
    }

    if "breaking" in directions:
        status = (
            DriftStatus.BREAKING_DRIFT
        )

    elif "unknown" in directions:
        status = (
            DriftStatus.UNKNOWN_DRIFT
        )

    elif "compatible" in directions:
        status = (
            DriftStatus.COMPATIBLE_DRIFT
        )

    else:
        status = (
            DriftStatus.NO_DRIFT
        )

    return DriftResult(
        status=status,
        changes=ordered,
    )


def classify_schema_drift(
    *,
    canonical_schema: Mapping[
        str,
        Any,
    ],
    candidate_schema: Mapping[
        str,
        Any,
    ],
) -> DriftResult:
    try:
        canonical = _copy_json_value(
            canonical_schema
        )

        candidate = _copy_json_value(
            candidate_schema
        )
    except Exception:
        return _result_from_changes(
            [
                DriftChange(
                    code=(
                        "shopping.schema.drift.invalid_input"
                    ),
                    direction="unknown",
                    schema_path=(),
                )
            ]
        )

    if (
        not isinstance(
            canonical,
            dict,
        )
        or not isinstance(
            candidate,
            dict,
        )
    ):
        return _result_from_changes(
            [
                DriftChange(
                    code=(
                        "shopping.schema.drift.invalid_input"
                    ),
                    direction="unknown",
                    schema_path=(),
                )
            ]
        )

    try:
        Draft202012Validator.check_schema(
            canonical
        )

        Draft202012Validator.check_schema(
            candidate
        )
    except Exception:
        return _result_from_changes(
            [
                DriftChange(
                    code=(
                        "shopping.schema.drift.invalid_schema"
                    ),
                    direction="unknown",
                    schema_path=(),
                )
            ]
        )

    if (
        _has_remote_ref(
            canonical
        )
        or _has_remote_ref(
            candidate
        )
    ):
        return _result_from_changes(
            [
                DriftChange(
                    code=(
                        "shopping.schema.drift.remote_ref"
                    ),
                    direction="unknown",
                    schema_path=(),
                )
            ]
        )

    if (
        _canonical_bytes(
            canonical
        )
        == _canonical_bytes(
            candidate
        )
    ):
        return DriftResult(
            status=DriftStatus.NO_DRIFT,
            changes=(),
        )

    changes: list[
        DriftChange
    ] = []

    _compare_mapping(
        canonical,
        candidate,
        path=(),
        changes=changes,
    )

    if not changes:
        _change(
            changes,
            code=(
                "shopping.schema.drift.unclassified_change"
            ),
            direction="unknown",
            path=(),
        )

    return _result_from_changes(
        changes
    )


def schema_drift_contract_manifest(
) -> dict[str, Any]:
    return {
        "automatic_adoption": False,
        "automatic_migration": False,
        "automatic_schema_rewrite": False,
        "authorization_owned": False,
        "canonical_consumer_safety": True,
        "classifier_pure": True,
        "database_write": False,
        "filesystem": False,
        "machine_readable": True,
        "network": False,
        "persistence": False,
        "production_registration": False,
        "raw_vendor_payload": False,
        "schema_discovery_owned": False,
        "statuses": [
            status.value
            for status
            in DriftStatus
        ],
        "unknown_fail_closed": True,
        "ubuntu_application_state": False,
        "vendor_write": False,
        "write_methods_allowed": False,
    }


__all__ = (
    "DriftChange",
    "DriftResult",
    "DriftStatus",
    "classify_schema_drift",
    "schema_drift_contract_manifest",
)

from __future__ import annotations

from copy import deepcopy

from core.shopping.contracts.schema_drift import (
    DriftStatus,
    classify_schema_drift,
    schema_drift_contract_manifest,
)


DRAFT = (
    "https://json-schema.org/draft/2020-12/schema"
)

SCHEMA_ID = "urn:test:drift"

BASE = {
    "$id": SCHEMA_ID,
    "$schema": DRAFT,
    "additionalProperties": False,
    "properties": {
        "age": {
            "type": [
                "integer",
                "number",
            ],
        },
        "name": {
            "type": "string",
        },
    },
    "required": [
        "name",
    ],
    "type": "object",
}


def _candidate():
    return deepcopy(
        BASE
    )


def test_manifest_is_pure_read_only_and_fail_closed():
    manifest = (
        schema_drift_contract_manifest()
    )

    assert manifest[
        "classifier_pure"
    ] is True
    assert manifest[
        "canonical_consumer_safety"
    ] is True
    assert manifest[
        "unknown_fail_closed"
    ] is True
    assert manifest[
        "authorization_owned"
    ] is False
    assert manifest[
        "schema_discovery_owned"
    ] is False
    assert manifest[
        "automatic_adoption"
    ] is False
    assert manifest[
        "automatic_schema_rewrite"
    ] is False
    assert manifest[
        "automatic_migration"
    ] is False
    assert manifest[
        "network"
    ] is False
    assert manifest[
        "filesystem"
    ] is False
    assert manifest[
        "database_write"
    ] is False
    assert manifest[
        "write_methods_allowed"
    ] is False


def test_exact_schema_has_no_drift():
    result = classify_schema_drift(
        canonical_schema=BASE,
        candidate_schema=_candidate(),
    )

    assert result.status is (
        DriftStatus.NO_DRIFT
    )
    assert result.changes == ()


def test_metadata_only_change_is_compatible():
    candidate = _candidate()
    candidate[
        "description"
    ] = "changed"

    result = classify_schema_drift(
        canonical_schema=BASE,
        candidate_schema=candidate,
    )

    assert result.status is (
        DriftStatus.COMPATIBLE_DRIFT
    )


def test_existing_optional_property_becoming_required_is_compatible():
    candidate = _candidate()
    candidate[
        "required"
    ].append(
        "age"
    )

    result = classify_schema_drift(
        canonical_schema=BASE,
        candidate_schema=candidate,
    )

    assert result.status is (
        DriftStatus.COMPATIBLE_DRIFT
    )


def test_optional_property_removal_is_compatible():
    candidate = _candidate()
    del candidate[
        "properties"
    ][
        "age"
    ]

    result = classify_schema_drift(
        canonical_schema=BASE,
        candidate_schema=candidate,
    )

    assert result.status is (
        DriftStatus.COMPATIBLE_DRIFT
    )


def test_type_narrowing_is_compatible():
    candidate = _candidate()
    candidate[
        "properties"
    ][
        "age"
    ][
        "type"
    ] = "integer"

    result = classify_schema_drift(
        canonical_schema=BASE,
        candidate_schema=candidate,
    )

    assert result.status is (
        DriftStatus.COMPATIBLE_DRIFT
    )


def test_enum_narrowing_is_compatible():
    canonical = _candidate()
    canonical[
        "properties"
    ][
        "name"
    ][
        "enum"
    ] = [
        "a",
        "b",
    ]

    candidate = deepcopy(
        canonical
    )

    candidate[
        "properties"
    ][
        "name"
    ][
        "enum"
    ] = [
        "a",
    ]

    result = classify_schema_drift(
        canonical_schema=canonical,
        candidate_schema=candidate,
    )

    assert result.status is (
        DriftStatus.COMPATIBLE_DRIFT
    )


def test_additional_properties_tightening_is_compatible():
    canonical = _candidate()
    canonical[
        "additionalProperties"
    ] = True

    candidate = deepcopy(
        canonical
    )

    candidate[
        "additionalProperties"
    ] = False

    result = classify_schema_drift(
        canonical_schema=canonical,
        candidate_schema=candidate,
    )

    assert result.status is (
        DriftStatus.COMPATIBLE_DRIFT
    )


def test_required_property_removal_is_breaking():
    candidate = _candidate()
    candidate[
        "required"
    ] = []

    result = classify_schema_drift(
        canonical_schema=BASE,
        candidate_schema=candidate,
    )

    assert result.status is (
        DriftStatus.BREAKING_DRIFT
    )


def test_new_required_property_is_breaking():
    candidate = _candidate()

    candidate[
        "properties"
    ][
        "external"
    ] = {
        "type": "string",
    }

    candidate[
        "required"
    ].append(
        "external"
    )

    result = classify_schema_drift(
        canonical_schema=BASE,
        candidate_schema=candidate,
    )

    assert result.status is (
        DriftStatus.BREAKING_DRIFT
    )


def test_new_optional_property_is_breaking_when_canonical_is_closed():
    candidate = _candidate()

    candidate[
        "properties"
    ][
        "external"
    ] = {
        "type": "string",
    }

    result = classify_schema_drift(
        canonical_schema=BASE,
        candidate_schema=candidate,
    )

    assert result.status is (
        DriftStatus.BREAKING_DRIFT
    )


def test_type_widening_is_breaking():
    canonical = _candidate()

    canonical[
        "properties"
    ][
        "age"
    ][
        "type"
    ] = "integer"

    candidate = deepcopy(
        canonical
    )

    candidate[
        "properties"
    ][
        "age"
    ][
        "type"
    ] = [
        "integer",
        "number",
    ]

    result = classify_schema_drift(
        canonical_schema=canonical,
        candidate_schema=candidate,
    )

    assert result.status is (
        DriftStatus.BREAKING_DRIFT
    )


def test_enum_expansion_is_breaking():
    canonical = _candidate()

    canonical[
        "properties"
    ][
        "name"
    ][
        "enum"
    ] = [
        "a",
    ]

    candidate = deepcopy(
        canonical
    )

    candidate[
        "properties"
    ][
        "name"
    ][
        "enum"
    ] = [
        "a",
        "b",
    ]

    result = classify_schema_drift(
        canonical_schema=canonical,
        candidate_schema=candidate,
    )

    assert result.status is (
        DriftStatus.BREAKING_DRIFT
    )


def test_additional_properties_widening_is_breaking():
    candidate = _candidate()
    candidate[
        "additionalProperties"
    ] = True

    result = classify_schema_drift(
        canonical_schema=BASE,
        candidate_schema=candidate,
    )

    assert result.status is (
        DriftStatus.BREAKING_DRIFT
    )


def test_schema_id_change_is_unknown():
    candidate = _candidate()
    candidate[
        "$id"
    ] = "urn:test:other"

    result = classify_schema_drift(
        canonical_schema=BASE,
        candidate_schema=candidate,
    )

    assert result.status is (
        DriftStatus.UNKNOWN_DRIFT
    )


def test_complex_combinator_change_is_unknown():
    candidate = _candidate()
    candidate[
        "allOf"
    ] = [
        {
            "type": "object",
        }
    ]

    result = classify_schema_drift(
        canonical_schema=BASE,
        candidate_schema=candidate,
    )

    assert result.status is (
        DriftStatus.UNKNOWN_DRIFT
    )


def test_remote_reference_is_unknown():
    candidate = _candidate()
    candidate[
        "$ref"
    ] = (
        "https://example.invalid/schema.json"
    )

    result = classify_schema_drift(
        canonical_schema=BASE,
        candidate_schema=candidate,
    )

    assert result.status is (
        DriftStatus.UNKNOWN_DRIFT
    )


def test_result_is_deterministic_json_safe_and_never_auto_adopts():
    candidate = _candidate()
    candidate[
        "description"
    ] = "changed"

    first = classify_schema_drift(
        canonical_schema=BASE,
        candidate_schema=candidate,
    )

    second = classify_schema_drift(
        canonical_schema=BASE,
        candidate_schema=candidate,
    )

    assert first.to_json() == (
        second.to_json()
    )
    assert first.to_json()[
        "auto_adopt"
    ] is False

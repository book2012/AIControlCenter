from __future__ import annotations

import json

import pytest

from core.shopping.contracts.schema_validation import (
    CANONICAL_SCHEMA_ID_PREFIX,
    MAX_VALIDATION_ERRORS,
    SchemaCatalog,
    SchemaCatalogError,
    ValidationStatus,
    load_canonical_schema_catalog,
    schema_validation_contract_manifest,
    validate_canonical_instance,
    validate_instance,
)


DRAFT = (
    "https://json-schema.org/draft/2020-12/schema"
)

SIMPLE_ID = "urn:test:simple"

SIMPLE_SCHEMA = {
    "$id": SIMPLE_ID,
    "$schema": DRAFT,
    "additionalProperties": False,
    "properties": {
        "name": {
            "type": "string",
        },
    },
    "required": [
        "name",
    ],
    "type": "object",
}


def _simple_catalog():
    return SchemaCatalog.from_documents(
        documents={
            SIMPLE_ID: SIMPLE_SCHEMA,
        }
    )


def test_manifest_is_validation_only_and_read_only():
    manifest = (
        schema_validation_contract_manifest()
    )

    assert manifest[
        "validation_only"
    ] is True
    assert manifest[
        "canonical_resource_count"
    ] == 17
    assert manifest[
        "registry_is_schema_resource"
    ] is False
    assert manifest[
        "network_resolution"
    ] is False
    assert manifest[
        "schema_mutation"
    ] is False
    assert manifest[
        "automatic_schema_rewrite"
    ] is False
    assert manifest[
        "automatic_migration"
    ] is False
    assert manifest[
        "write_methods_allowed"
    ] is False
    assert manifest[
        "production_registration"
    ] is False


def test_canonical_catalog_loads_seventeen_resources():
    catalog = (
        load_canonical_schema_catalog()
    )

    assert len(
        catalog.schema_ids
    ) == 17


def test_canonical_schema_ids_use_v1_prefix():
    catalog = (
        load_canonical_schema_catalog()
    )

    assert all(
        schema_id.startswith(
            CANONICAL_SCHEMA_ID_PREFIX
        )
        for schema_id
        in catalog.schema_ids
    )


def test_catalog_get_schema_returns_detached_copy():
    catalog = _simple_catalog()

    first = catalog.get_schema(
        SIMPLE_ID
    )

    first[
        "required"
    ].append(
        "other"
    )

    second = catalog.get_schema(
        SIMPLE_ID
    )

    assert second[
        "required"
    ] == [
        "name",
    ]


def test_valid_instance_returns_valid_and_accepted():
    result = validate_instance(
        catalog=_simple_catalog(),
        schema_id=SIMPLE_ID,
        instance={
            "name": "valid",
        },
    )

    assert result.status is (
        ValidationStatus.VALID
    )
    assert result.accepted is True
    assert result.issues == ()


def test_invalid_instance_returns_deterministic_invalid_result():
    result = validate_instance(
        catalog=_simple_catalog(),
        schema_id=SIMPLE_ID,
        instance={},
    )

    assert result.status is (
        ValidationStatus.INVALID
    )
    assert result.accepted is False
    assert result.issues
    assert result.issues[
        0
    ].keyword == "required"


def test_unknown_schema_returns_fail_closed_error():
    result = validate_instance(
        catalog=_simple_catalog(),
        schema_id="urn:test:unknown",
        instance={},
    )

    assert result.status is (
        ValidationStatus.ERROR
    )
    assert result.accepted is False
    assert result.issues[
        0
    ].code == (
        "shopping.schema.validation.unknown_schema"
    )


def test_invalid_schema_is_rejected_by_catalog():
    bad = {
        "$id": "urn:test:bad",
        "$schema": DRAFT,
        "type": 123,
    }

    with pytest.raises(
        SchemaCatalogError,
        match=(
            "shopping.schema.catalog.invalid_schema"
        ),
    ):
        SchemaCatalog.from_documents(
            documents={
                "urn:test:bad": bad,
            }
        )


def test_remote_reference_is_rejected_by_catalog():
    remote = {
        "$id": "urn:test:remote",
        "$schema": DRAFT,
        "$ref": "https://example.invalid/schema.json",
    }

    with pytest.raises(
        SchemaCatalogError,
        match=(
            "shopping.schema.catalog.remote_ref"
        ),
    ):
        SchemaCatalog.from_documents(
            documents={
                "urn:test:remote": remote,
            }
        )


def test_local_alias_reference_validates():
    child_id = "urn:test:child"
    root_id = "urn:test:root"

    child = {
        "$id": child_id,
        "$schema": DRAFT,
        "type": "string",
    }

    root = {
        "$id": root_id,
        "$schema": DRAFT,
        "$ref": "child.json",
    }

    catalog = SchemaCatalog.from_documents(
        documents={
            child_id: child,
            root_id: root,
        },
        aliases={
            "child.json": child_id,
        },
    )

    result = validate_instance(
        catalog=catalog,
        schema_id=root_id,
        instance="ok",
    )

    assert result.status is (
        ValidationStatus.VALID
    )


def test_local_alias_reference_rejects_invalid_instance():
    child_id = "urn:test:child"
    root_id = "urn:test:root"

    child = {
        "$id": child_id,
        "$schema": DRAFT,
        "type": "string",
    }

    root = {
        "$id": root_id,
        "$schema": DRAFT,
        "$ref": "child.json",
    }

    catalog = SchemaCatalog.from_documents(
        documents={
            child_id: child,
            root_id: root,
        },
        aliases={
            "child.json": child_id,
        },
    )

    result = validate_instance(
        catalog=catalog,
        schema_id=root_id,
        instance=123,
    )

    assert result.status is (
        ValidationStatus.INVALID
    )


def test_validation_issue_order_is_deterministic():
    schema_id = "urn:test:order"

    schema = {
        "$id": schema_id,
        "$schema": DRAFT,
        "additionalProperties": False,
        "properties": {
            "a": {
                "type": "string",
            },
            "b": {
                "type": "integer",
            },
        },
        "required": [
            "a",
            "b",
        ],
        "type": "object",
    }

    catalog = SchemaCatalog.from_documents(
        documents={
            schema_id: schema,
        }
    )

    first = validate_instance(
        catalog=catalog,
        schema_id=schema_id,
        instance={},
    ).to_json()

    second = validate_instance(
        catalog=catalog,
        schema_id=schema_id,
        instance={},
    ).to_json()

    assert first == second


def test_validation_errors_are_capped_at_one_hundred():
    schema_id = "urn:test:many"

    required = [
        "f"
        + str(
            index
        )
        for index
        in range(
            150
        )
    ]

    schema = {
        "$id": schema_id,
        "$schema": DRAFT,
        "required": required,
        "type": "object",
    }

    catalog = SchemaCatalog.from_documents(
        documents={
            schema_id: schema,
        }
    )

    result = validate_instance(
        catalog=catalog,
        schema_id=schema_id,
        instance={},
    )

    assert result.status is (
        ValidationStatus.INVALID
    )
    assert len(
        result.issues
    ) <= MAX_VALIDATION_ERRORS
    assert len(
        result.issues
    ) == 100


def test_result_to_json_is_json_safe_and_contains_no_raw_exception():
    result = validate_instance(
        catalog=_simple_catalog(),
        schema_id=SIMPLE_ID,
        instance={},
    )

    encoded = json.dumps(
        result.to_json(),
        sort_keys=True,
    )

    assert "Traceback" not in encoded
    assert "exception" not in encoded.lower()


def test_canonical_unknown_schema_fails_closed_without_mutation():
    result = validate_canonical_instance(
        schema_id=(
            "urn:aicontrolcenter:shopping:contract:v1:not-real"
        ),
        instance={},
    )

    assert result.status is (
        ValidationStatus.ERROR
    )
    assert result.accepted is False
    assert result.issues[
        0
    ].code == (
        "shopping.schema.validation.unknown_schema"
    )

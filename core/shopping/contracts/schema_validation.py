from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


CANONICAL_SCHEMA_ID_PREFIX = (
    "urn:aicontrolcenter:shopping:contract:v1:"
)

CANONICAL_SCHEMA_ROOT = (
    Path(__file__).resolve().parent
    / "schemas"
    / "v1"
)

CANONICAL_SUPPORT_DOCUMENT = "registry.json"

MAX_VALIDATION_ERRORS = 100

_SAFE_KEYWORD = re.compile(
    r"[^A-Za-z0-9_.-]+"
)


class ValidationStatus(
    str,
    Enum,
):
    VALID = "VALID"
    INVALID = "INVALID"
    ERROR = "ERROR"


class SchemaCatalogError(
    ValueError
):
    pass


@dataclass(
    frozen=True,
    slots=True,
)
class ValidationIssue:
    code: str
    keyword: str
    instance_path: tuple[str | int, ...]
    schema_path: tuple[str | int, ...]

    def to_json(
        self,
    ) -> dict[str, Any]:
        return {
            "code": self.code,
            "instance_path": list(
                self.instance_path
            ),
            "keyword": self.keyword,
            "schema_path": list(
                self.schema_path
            ),
        }


@dataclass(
    frozen=True,
    slots=True,
)
class ValidationResult:
    schema_id: str
    status: ValidationStatus
    issues: tuple[
        ValidationIssue,
        ...,
    ]

    @property
    def accepted(
        self,
    ) -> bool:
        return (
            self.status
            is ValidationStatus.VALID
        )

    def to_json(
        self,
    ) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "issues": [
                issue.to_json()
                for issue
                in self.issues
            ],
            "schema_id": self.schema_id,
            "status": self.status.value,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class SchemaCatalog:
    _schema_bytes: Mapping[
        str,
        bytes,
    ]
    _aliases: Mapping[
        str,
        str,
    ]
    _registry: Registry

    @classmethod
    def from_documents(
        cls,
        *,
        documents: Mapping[
            str,
            Mapping[str, Any],
        ],
        aliases: Mapping[
            str,
            str,
        ]
        | None = None,
    ) -> "SchemaCatalog":
        if not isinstance(
            documents,
            Mapping,
        ) or not documents:
            raise SchemaCatalogError(
                "shopping.schema.catalog.empty"
            )

        canonical_bytes: dict[
            str,
            bytes,
        ] = {}

        resources: dict[
            str,
            Resource,
        ] = {}

        for schema_id, document in sorted(
            documents.items()
        ):
            if (
                not isinstance(
                    schema_id,
                    str,
                )
                or not schema_id
                or not isinstance(
                    document,
                    Mapping,
                )
            ):
                raise SchemaCatalogError(
                    "shopping.schema.catalog.invalid_resource"
                )

            copied = _copy_json_value(
                document
            )

            if not isinstance(
                copied,
                dict,
            ):
                raise SchemaCatalogError(
                    "shopping.schema.catalog.invalid_resource"
                )

            if copied.get(
                "$id"
            ) != schema_id:
                raise SchemaCatalogError(
                    "shopping.schema.catalog.id_mismatch"
                )

            schema_keyword = copied.get(
                "$schema"
            )

            if (
                not isinstance(
                    schema_keyword,
                    str,
                )
                or "2020-12"
                not in schema_keyword
            ):
                raise SchemaCatalogError(
                    "shopping.schema.catalog.unsupported_draft"
                )

            if _contains_remote_ref(
                copied
            ):
                raise SchemaCatalogError(
                    "shopping.schema.catalog.remote_ref"
                )

            try:
                Draft202012Validator.check_schema(
                    copied
                )

                resource = (
                    Resource.from_contents(
                        copied
                    )
                )
            except Exception:
                raise SchemaCatalogError(
                    "shopping.schema.catalog.invalid_schema"
                ) from None

            canonical_bytes[
                schema_id
            ] = _canonical_bytes(
                copied
            )

            resources[
                schema_id
            ] = resource

        alias_map = dict(
            aliases or {}
        )

        for alias, schema_id in sorted(
            alias_map.items()
        ):
            if (
                not isinstance(
                    alias,
                    str,
                )
                or not alias
                or schema_id
                not in resources
            ):
                raise SchemaCatalogError(
                    "shopping.schema.catalog.invalid_alias"
                )

        registry = Registry()

        for schema_id, resource in sorted(
            resources.items()
        ):
            registry = (
                registry.with_resource(
                    schema_id,
                    resource,
                )
            )

        for alias, schema_id in sorted(
            alias_map.items()
        ):
            registry = (
                registry.with_resource(
                    alias,
                    resources[
                        schema_id
                    ],
                )
            )

        return cls(
            _schema_bytes=MappingProxyType(
                dict(
                    canonical_bytes
                )
            ),
            _aliases=MappingProxyType(
                dict(
                    alias_map
                )
            ),
            _registry=registry,
        )

    @property
    def schema_ids(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            sorted(
                self._schema_bytes
            )
        )

    @property
    def aliases(
        self,
    ) -> Mapping[
        str,
        str,
    ]:
        return MappingProxyType(
            dict(
                self._aliases
            )
        )

    def has_schema(
        self,
        schema_id: str,
    ) -> bool:
        return (
            isinstance(
                schema_id,
                str,
            )
            and schema_id
            in self._schema_bytes
        )

    def get_schema(
        self,
        schema_id: str,
    ) -> dict[str, Any]:
        if not self.has_schema(
            schema_id
        ):
            raise SchemaCatalogError(
                "shopping.schema.catalog.unknown_schema"
            )

        value = json.loads(
            self._schema_bytes[
                schema_id
            ].decode(
                "utf-8"
            )
        )

        if not isinstance(
            value,
            dict,
        ):
            raise SchemaCatalogError(
                "shopping.schema.catalog.invalid_resource"
            )

        return value


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
            raise SchemaCatalogError(
                "shopping.schema.catalog.non_finite_number"
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
                raise SchemaCatalogError(
                    "shopping.schema.catalog.non_string_key"
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

    raise SchemaCatalogError(
        "shopping.schema.catalog.non_json_value"
    )


def _canonical_bytes(
    value: Mapping[
        str,
        Any,
    ],
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


def _contains_remote_ref(
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


def _safe_keyword(
    value: Any,
) -> str:
    if not isinstance(
        value,
        str,
    ) or not value:
        return "unknown"

    cleaned = _SAFE_KEYWORD.sub(
        "_",
        value
    ).strip(
        "_"
    )

    return (
        cleaned[:80]
        if cleaned
        else "unknown"
    )


def _safe_path(
    value: Any,
) -> tuple[str | int, ...]:
    result: list[
        str | int
    ] = []

    for part in value:
        if isinstance(
            part,
            bool,
        ):
            result.append(
                str(
                    part
                ).lower()
            )

        elif isinstance(
            part,
            int,
        ):
            result.append(
                part
            )

        else:
            result.append(
                str(
                    part
                )[:160]
            )

    return tuple(
        result
    )


def _error_result(
    *,
    schema_id: str,
    code: str,
) -> ValidationResult:
    return ValidationResult(
        schema_id=schema_id,
        status=ValidationStatus.ERROR,
        issues=(
            ValidationIssue(
                code=code,
                keyword="runtime",
                instance_path=(),
                schema_path=(),
            ),
        ),
    )


def load_canonical_schema_catalog(
    *,
    schema_root: Path | None = None,
) -> SchemaCatalog:
    root = (
        CANONICAL_SCHEMA_ROOT
        if schema_root is None
        else Path(
            schema_root
        )
    )

    if (
        not root.is_dir()
        or root.is_symlink()
    ):
        raise SchemaCatalogError(
            "shopping.schema.catalog.root_unavailable"
        )

    support_path = (
        root
        / CANONICAL_SUPPORT_DOCUMENT
    )

    if not support_path.is_file():
        raise SchemaCatalogError(
            "shopping.schema.catalog.registry_missing"
        )

    try:
        support = json.loads(
            support_path.read_text(
                encoding="utf-8"
            )
        )
    except Exception:
        raise SchemaCatalogError(
            "shopping.schema.catalog.registry_invalid"
        ) from None

    if (
        not isinstance(
            support,
            dict,
        )
        or "$id"
        in support
        or "$schema"
        in support
    ):
        raise SchemaCatalogError(
            "shopping.schema.catalog.registry_invalid"
        )

    documents: dict[
        str,
        dict[str, Any],
    ] = {}

    aliases: dict[
        str,
        str,
    ] = {}

    for path in sorted(
        root.glob(
            "*.json"
        )
    ):
        if path.name == (
            CANONICAL_SUPPORT_DOCUMENT
        ):
            continue

        try:
            document = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )
        except Exception:
            raise SchemaCatalogError(
                "shopping.schema.catalog.resource_unreadable"
            ) from None

        if not isinstance(
            document,
            dict,
        ):
            raise SchemaCatalogError(
                "shopping.schema.catalog.invalid_resource"
            )

        schema_id = document.get(
            "$id"
        )

        if (
            not isinstance(
                schema_id,
                str,
            )
            or not schema_id.startswith(
                CANONICAL_SCHEMA_ID_PREFIX
            )
        ):
            raise SchemaCatalogError(
                "shopping.schema.catalog.invalid_canonical_id"
            )

        if schema_id in documents:
            raise SchemaCatalogError(
                "shopping.schema.catalog.duplicate_id"
            )

        documents[
            schema_id
        ] = document

        aliases[
            path.name
        ] = schema_id

    if len(
        documents
    ) != 17:
        raise SchemaCatalogError(
            "shopping.schema.catalog.resource_count"
        )

    return SchemaCatalog.from_documents(
        documents=documents,
        aliases=aliases,
    )


def validate_instance(
    *,
    catalog: SchemaCatalog,
    schema_id: str,
    instance: Any,
) -> ValidationResult:
    if not isinstance(
        catalog,
        SchemaCatalog,
    ):
        return _error_result(
            schema_id=(
                schema_id
                if isinstance(
                    schema_id,
                    str,
                )
                else ""
            ),
            code=(
                "shopping.schema.validation.catalog_error"
            ),
        )

    if (
        not isinstance(
            schema_id,
            str,
        )
        or not schema_id
    ):
        return _error_result(
            schema_id="",
            code=(
                "shopping.schema.validation.schema_id_required"
            ),
        )

    if not catalog.has_schema(
        schema_id
    ):
        return _error_result(
            schema_id=schema_id,
            code=(
                "shopping.schema.validation.unknown_schema"
            ),
        )

    try:
        schema = catalog.get_schema(
            schema_id
        )

        validator = Draft202012Validator(
            schema,
            registry=catalog._registry,
        )

        errors = list(
            validator.iter_errors(
                instance
            )
        )
    except Exception:
        return _error_result(
            schema_id=schema_id,
            code=(
                "shopping.schema.validation.engine_error"
            ),
        )

    if not errors:
        return ValidationResult(
            schema_id=schema_id,
            status=ValidationStatus.VALID,
            issues=(),
        )

    issues = []

    for error in errors:
        keyword = _safe_keyword(
            error.validator
        )

        issues.append(
            ValidationIssue(
                code=(
                    "shopping.schema.validation."
                    + keyword
                ),
                keyword=keyword,
                instance_path=_safe_path(
                    error.absolute_path
                ),
                schema_path=_safe_path(
                    error.absolute_schema_path
                ),
            )
        )

    issues.sort(
        key=lambda issue: (
            tuple(
                str(
                    part
                )
                for part
                in issue.instance_path
            ),
            tuple(
                str(
                    part
                )
                for part
                in issue.schema_path
            ),
            issue.keyword,
            issue.code,
        )
    )

    return ValidationResult(
        schema_id=schema_id,
        status=ValidationStatus.INVALID,
        issues=tuple(
            issues[
                :MAX_VALIDATION_ERRORS
            ]
        ),
    )


def validate_canonical_instance(
    *,
    schema_id: str,
    instance: Any,
    schema_root: Path | None = None,
) -> ValidationResult:
    try:
        catalog = (
            load_canonical_schema_catalog(
                schema_root=schema_root
            )
        )
    except SchemaCatalogError:
        return _error_result(
            schema_id=(
                schema_id
                if isinstance(
                    schema_id,
                    str,
                )
                else ""
            ),
            code=(
                "shopping.schema.validation.catalog_error"
            ),
        )

    return validate_instance(
        catalog=catalog,
        schema_id=schema_id,
        instance=instance,
    )


def schema_validation_contract_manifest(
) -> dict[str, Any]:
    return {
        "automatic_migration": False,
        "automatic_schema_rewrite": False,
        "canonical_resource_count": 17,
        "canonical_schema_draft": "2020-12",
        "canonical_schema_source": (
            "core/shopping/contracts/schemas/v1"
        ),
        "drift_classification": (
            "deferred_to_SPF-009-04"
        ),
        "filesystem_application_state_write": False,
        "filesystem_read": (
            "explicit_loader_call_only"
        ),
        "import_side_effects": False,
        "local_resources_only": True,
        "machine_readable": True,
        "max_error_records": (
            MAX_VALIDATION_ERRORS
        ),
        "network_resolution": False,
        "production_registration": False,
        "raw_exception_message": False,
        "raw_vendor_payload": False,
        "registry_is_schema_resource": False,
        "schema_mutation": False,
        "statuses": [
            status.value
            for status
            in ValidationStatus
        ],
        "support_document": (
            CANONICAL_SUPPORT_DOCUMENT
        ),
        "ubuntu_application_state": False,
        "validation_only": True,
        "vendor_write": False,
        "write_methods_allowed": False,
    }


__all__ = (
    "CANONICAL_SCHEMA_ID_PREFIX",
    "CANONICAL_SCHEMA_ROOT",
    "CANONICAL_SUPPORT_DOCUMENT",
    "MAX_VALIDATION_ERRORS",
    "SchemaCatalog",
    "SchemaCatalogError",
    "ValidationIssue",
    "ValidationResult",
    "ValidationStatus",
    "load_canonical_schema_catalog",
    "schema_validation_contract_manifest",
    "validate_canonical_instance",
    "validate_instance",
)

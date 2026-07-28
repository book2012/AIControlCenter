"""Pure, local validation for DPL v1 payloads."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import isfinite
from pathlib import PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .registry import DeploymentSchemaRegistry, UnknownDeploymentContractError

_SECRET_NAMES = {"password", "token", "secret", "private_key", "credential"}
_FORBIDDEN_OPERATIONS = {"apply", "execute", "install", "restart", "bootstrap"}
_PATH_NAMES = {"relative_path", "artifact_path"}


@dataclass(frozen=True, slots=True)
class ContractValidationIssue:
    path: str
    validator: str
    message: str


class DeploymentContractValidationError(ValueError):
    def __init__(
        self, *, contract_name: str, issues: tuple[ContractValidationIssue, ...]
    ) -> None:
        self.contract_name = contract_name
        self.issues = issues
        super().__init__(
            f"Contract validation failed for {contract_name} "
            f"with {len(issues)} issue(s)."
        )


def _pointer(parts: tuple[str | int, ...]) -> str:
    return "" if not parts else "/" + "/".join(
        str(part).replace("~", "~0").replace("/", "~1") for part in parts
    )


def _pure_issues(
    value: Any, path: tuple[str | int, ...] = ()
) -> list[ContractValidationIssue]:
    issues: list[ContractValidationIssue] = []
    if value is None or isinstance(value, (str, bool, int)):
        return issues
    if isinstance(value, float):
        if not isfinite(value):
            issues.append(
                ContractValidationIssue(
                    _pointer(path), "json_value", "Non-finite number is prohibited."
                )
            )
        return issues
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                issues.append(
                    ContractValidationIssue(
                        _pointer(path), "json_key", "Object keys must be strings."
                    )
                )
                continue
            child_path = (*path, key)
            normalized = key.lower()
            if normalized in _SECRET_NAMES and child not in (None, "", [], {}):
                issues.append(
                    ContractValidationIssue(
                        _pointer(child_path),
                        "secret_field",
                        "Embedded secret values are prohibited.",
                    )
                )
            if (
                normalized in {"operation", "action"}
                and isinstance(child, str)
                and child.lower() in _FORBIDDEN_OPERATIONS
            ):
                issues.append(
                    ContractValidationIssue(
                        _pointer(child_path),
                        "forbidden_operation",
                        "Write or execution operation is prohibited.",
                    )
                )
            if normalized in _PATH_NAMES and isinstance(child, str):
                pure = PurePosixPath(child)
                if pure.is_absolute() or ".." in pure.parts:
                    issues.append(
                        ContractValidationIssue(
                            _pointer(child_path),
                            "path_traversal",
                            "Package-relative path is unsafe.",
                        )
                    )
            issues.extend(_pure_issues(child, child_path))
        return issues
    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        for index, child in enumerate(value):
            issues.extend(_pure_issues(child, (*path, index)))
        return issues
    return [
        ContractValidationIssue(
            _pointer(path), "json_type", "Value is not JSON-compatible."
        )
    ]


def validate_contract_payload(
    *,
    registry: DeploymentSchemaRegistry,
    contract_name: str,
    payload: Mapping[str, Any],
) -> None:
    issues = _pure_issues(payload)
    try:
        schema = registry.contract_schema(contract_name)
    except UnknownDeploymentContractError:
        issues.append(
            ContractValidationIssue("", "contract", "Unknown deployment contract.")
        )
        schema = None
    if schema is not None:
        validator = Draft202012Validator(
            schema,
            registry=registry.reference_registry,
            format_checker=FormatChecker(),
        )
        for error in sorted(
            validator.iter_errors(payload),
            key=lambda item: (
                tuple(str(part) for part in item.absolute_path),
                str(item.validator),
            ),
        ):
            issues.append(
                ContractValidationIssue(
                    _pointer(tuple(error.absolute_path)),
                    str(error.validator or "schema"),
                    error.message,
                )
            )
    if issues:
        raise DeploymentContractValidationError(
            contract_name=contract_name, issues=tuple(issues)
        )


__all__ = (
    "ContractValidationIssue",
    "DeploymentContractValidationError",
    "validate_contract_payload",
)

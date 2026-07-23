from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite
from typing import Any

from jsonschema import (
    Draft202012Validator,
    FormatChecker,
)

from .schema_registry import (
    ShoppingSchemaRegistry,
    UnknownShoppingContractError,
)


@dataclass(frozen=True, slots=True)
class ContractValidationIssue:
    path: str
    validator: str
    message: str


class ShoppingContractValidationError(
    ValueError
):
    def __init__(
        self,
        *,
        contract_name: str,
        issues: tuple[
            ContractValidationIssue,
            ...,
        ],
    ) -> None:
        self.contract_name = (
            contract_name
        )
        self.issues = issues

        super().__init__(
            "Contract validation failed for "
            + contract_name
            + " with "
            + str(
                len(issues)
            )
            + " issue(s)."
        )


def _pointer(
    parts: tuple[
        str | int,
        ...,
    ],
) -> str:
    if not parts:
        return ""

    return (
        "/"
        + "/".join(
            str(
                part
            )
            .replace(
                "~",
                "~0",
            )
            .replace(
                "/",
                "~1",
            )
            for part in parts
        )
    )


def _json_issues(
    value: Any,
    *,
    path: tuple[
        str | int,
        ...,
    ] = (),
) -> list[
    ContractValidationIssue
]:
    if (
        value is None
        or isinstance(
            value,
            (
                str,
                bool,
                int,
            ),
        )
    ):
        return []

    if isinstance(
        value,
        float,
    ):
        if isfinite(
            value
        ):
            return []

        return [
            ContractValidationIssue(
                path=_pointer(
                    path
                ),
                validator=(
                    "json_value"
                ),
                message=(
                    "Non-finite numbers are not allowed."
                ),
            )
        ]

    if isinstance(
        value,
        Mapping,
    ):
        issues: list[
            ContractValidationIssue
        ] = []

        for key, child in value.items():
            if not isinstance(
                key,
                str,
            ):
                issues.append(
                    ContractValidationIssue(
                        path=_pointer(
                            path
                        ),
                        validator=(
                            "json_key"
                        ),
                        message=(
                            "Object keys must be strings."
                        ),
                    )
                )
                continue

            issues.extend(
                _json_issues(
                    child,
                    path=(
                        *path,
                        key,
                    ),
                )
            )

        return issues

    if isinstance(
        value,
        list,
    ):
        issues = []

        for index, child in enumerate(
            value
        ):
            issues.extend(
                _json_issues(
                    child,
                    path=(
                        *path,
                        index,
                    ),
                )
            )

        return issues

    return [
        ContractValidationIssue(
            path=_pointer(
                path
            ),
            validator=(
                "json_type"
            ),
            message=(
                "Value is not JSON-compatible."
            ),
        )
    ]


def validate_contract_payload(
    *,
    registry: ShoppingSchemaRegistry,
    contract_name: str,
    payload: Mapping[str, Any],
) -> None:
    compatibility_issues = (
        _json_issues(
            payload
        )
    )

    if compatibility_issues:
        raise ShoppingContractValidationError(
            contract_name=(
                contract_name
            ),
            issues=tuple(
                compatibility_issues
            ),
        )

    try:
        schema = registry.contract_schema(
            contract_name
        )
    except UnknownShoppingContractError:
        raise ShoppingContractValidationError(
            contract_name=(
                contract_name
            ),
            issues=(
                ContractValidationIssue(
                    path="",
                    validator=(
                        "contract"
                    ),
                    message=(
                        "Unknown contract."
                    ),
                ),
            ),
        ) from None

    validator = Draft202012Validator(
        schema,
        registry=(
            registry.reference_registry
        ),
        format_checker=(
            FormatChecker()
        ),
    )

    errors = sorted(
        validator.iter_errors(
            payload
        ),
        key=lambda error: (
            tuple(
                str(
                    part
                )
                for part
                in error.absolute_path
            ),
            str(
                error.validator
            ),
        ),
    )

    if not errors:
        return

    issues = tuple(
        ContractValidationIssue(
            path=_pointer(
                tuple(
                    error.absolute_path
                )
            ),
            validator=(
                str(
                    error.validator
                )
                if error.validator
                is not None
                else "schema"
            ),
            message=(
                "Payload failed "
                + (
                    str(
                        error.validator
                    )
                    if error.validator
                    is not None
                    else "schema"
                )
                + " validation."
            ),
        )
        for error in errors
    )

    raise ShoppingContractValidationError(
        contract_name=(
            contract_name
        ),
        issues=issues,
    )


__all__ = (
    "ContractValidationIssue",
    "ShoppingContractValidationError",
    "validate_contract_payload",
)

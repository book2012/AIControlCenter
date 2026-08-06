from __future__ import annotations

from typing import Any

from core.deployment.contracts import (
    load_schema_registry,
    sha256_digest,
    validate_contract_payload,
)

from .models import (
    CheckObservation,
    InspectionEvaluation,
    InspectionEvaluationRequest,
    SanitizedError,
    thaw_json,
)


POLICY_CONTRACT = "ActivationInspectionPolicy"
MANIFEST_CONTRACT = "ActivationRouteManifest"
REPORT_CONTRACT = "ActivationInspectionReport"

READY = "READY_FOR_AUTHORIZATION_REVIEW"
BLOCKED = "BLOCKED"
ERROR = "ERROR"


class ActivationInspectionEvaluationError(
    ValueError
):
    pass


def _sorted_checks(
    checks: tuple[CheckObservation, ...],
) -> tuple[CheckObservation, ...]:
    ordered = tuple(
        sorted(
            checks,
            key=lambda check: check.check_id,
        )
    )

    identifiers = [
        check.check_id
        for check in ordered
    ]

    if len(identifiers) != len(set(identifiers)):
        raise ActivationInspectionEvaluationError(
            "DUPLICATE_CHECK_ID"
        )

    return ordered


def _normalized_errors(
    checks: tuple[CheckObservation, ...],
    supplied: tuple[SanitizedError, ...],
) -> tuple[SanitizedError, ...]:
    errors = list(supplied)

    if not supplied:
        for check in checks:
            if check.result == "ERROR":
                errors.append(
                    SanitizedError(
                        code="CHECK_ERROR",
                        component="evaluator",
                        message=check.check_id,
                    )
                )

    unique = {
        (
            error.code,
            error.component,
            error.message,
        ): error
        for error in errors
    }

    return tuple(
        unique[key]
        for key in sorted(unique)
    )


def evaluate_activation_inspection(
    request: InspectionEvaluationRequest,
) -> InspectionEvaluation:
    registry = load_schema_registry()

    policy = thaw_json(request.policy)
    route_manifest = thaw_json(
        request.route_manifest
    )

    validate_contract_payload(
        registry=registry,
        contract_name=POLICY_CONTRACT,
        payload=policy,
    )

    validate_contract_payload(
        registry=registry,
        contract_name=MANIFEST_CONTRACT,
        payload=route_manifest,
    )

    manifest_digest = sha256_digest(
        route_manifest
    )

    expected_manifest_digest = (
        policy["route_manifest"][
            "manifest_digest"
        ]
    )

    if expected_manifest_digest != manifest_digest:
        raise ActivationInspectionEvaluationError(
            "ROUTE_MANIFEST_DIGEST_MISMATCH"
        )

    checks = _sorted_checks(
        request.checks
    )

    errors = _normalized_errors(
        checks,
        request.errors,
    )

    blocking_reasons = tuple(
        sorted(
            {
                check.check_id
                for check in checks
                if (
                    check.blocking
                    and check.result
                    in {"FAIL", "ERROR"}
                )
            }
        )
    )

    if errors or any(
        check.result == "ERROR"
        for check in checks
    ):
        overall_status = ERROR

    elif blocking_reasons:
        overall_status = BLOCKED

    else:
        overall_status = READY

    warnings = tuple(
        sorted(
            {
                warning
                for warning in request.warnings
                if warning
            }
        )
    )

    report: dict[str, Any] = {
        "schema_version": "dpl/v1",
        "inspection_id": request.inspection_id,
        "inspection_mode": "READ_ONLY",
        "read_only": True,
        "started_at": request.started_at,
        "completed_at": request.completed_at,
        "overall_status": overall_status,
        "policy_version": (
            policy["policy_version"]
        ),
        "policy_digest": sha256_digest(
            policy
        ),
        "route_manifest_version": (
            route_manifest["manifest_version"]
        ),
        "route_manifest_digest": (
            manifest_digest
        ),
        "git": thaw_json(request.git),
        "runtime": thaw_json(
            request.runtime
        ),
        "launchd": thaw_json(
            request.launchd
        ),
        "process": thaw_json(
            request.process
        ),
        "listener": thaw_json(
            request.listener
        ),
        "http": thaw_json(request.http),
        "checks": [
            check.to_payload()
            for check in checks
        ],
        "blocking_reasons": list(
            blocking_reasons
        ),
        "warnings": list(warnings),
        "sanitized_errors": [
            error.to_payload()
            for error in errors
        ],
        "production_writes": 0,
        "ubuntu_changes": 0,
        "production_authorized": False,
    }

    report["report_digest"] = sha256_digest(
        report
    )

    validate_contract_payload(
        registry=registry,
        contract_name=REPORT_CONTRACT,
        payload=report,
    )

    return InspectionEvaluation(
        report=report
    )


__all__ = (
    "ActivationInspectionEvaluationError",
    "BLOCKED",
    "ERROR",
    "READY",
    "evaluate_activation_inspection",
)

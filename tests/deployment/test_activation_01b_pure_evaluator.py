from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
import copy
import json

import pytest

from core.deployment.activation_inspector import (
    ActivationInspectionEvaluationError,
    CheckObservation,
    InspectionEvaluationRequest,
    SanitizedError,
    evaluate_activation_inspection,
    thaw_json,
)
from core.deployment.contracts import (
    canonical_json_bytes,
    load_schema_registry,
    sha256_digest,
    validate_contract_payload,
)


FIXTURE_ROOT = (
    Path(__file__).parents[1]
    / "fixtures"
    / "deployment"
)


def load_fixture(name: str) -> dict:
    return json.loads(
        (
            FIXTURE_ROOT
            / name
        ).read_text(encoding="utf-8")
    )


def make_request(
    *,
    checks: list[dict] | None = None,
    errors: tuple[SanitizedError, ...] = (),
) -> InspectionEvaluationRequest:
    policy = load_fixture(
        "activation-inspection-policy.json"
    )

    manifest = load_fixture(
        "activation-route-manifest.json"
    )

    report = load_fixture(
        "activation-inspection-report.json"
    )

    source_checks = (
        report["checks"]
        if checks is None
        else checks
    )

    observations = tuple(
        CheckObservation(
            check_id=item["check_id"],
            expected=item["expected"],
            actual=item["actual"],
            result=item["result"],
            blocking=item["blocking"],
            evidence_reference=(
                item["evidence_reference"]
            ),
            timestamp=item["timestamp"],
        )
        for item in source_checks
    )

    return InspectionEvaluationRequest(
        policy=policy,
        route_manifest=manifest,
        inspection_id=report[
            "inspection_id"
        ],
        started_at=report["started_at"],
        completed_at=report[
            "completed_at"
        ],
        git=report["git"],
        runtime=report["runtime"],
        launchd=report["launchd"],
        process=report["process"],
        listener=report["listener"],
        http=report["http"],
        checks=observations,
        warnings=tuple(
            report["warnings"]
        ),
        errors=errors,
    )


def test_ready_report_is_valid_and_deterministic() -> None:
    first = evaluate_activation_inspection(
        make_request()
    )

    fixture = load_fixture(
        "activation-inspection-report.json"
    )

    reversed_checks = list(
        reversed(fixture["checks"])
    )

    second = evaluate_activation_inspection(
        make_request(
            checks=reversed_checks
        )
    )

    first_payload = first.to_payload()
    second_payload = second.to_payload()

    assert (
        first_payload["overall_status"]
        == "READY_FOR_AUTHORIZATION_REVIEW"
    )

    assert first_payload["blocking_reasons"] == []
    assert first_payload["sanitized_errors"] == []
    assert first_payload["production_writes"] == 0
    assert first_payload["ubuntu_changes"] == 0
    assert (
        first_payload["production_authorized"]
        is False
    )

    assert canonical_json_bytes(
        first_payload
    ) == canonical_json_bytes(
        second_payload
    )

    semantic = copy.deepcopy(first_payload)
    supplied_digest = semantic.pop(
        "report_digest"
    )

    assert supplied_digest == sha256_digest(
        semantic
    )

    validate_contract_payload(
        registry=load_schema_registry(),
        contract_name=(
            "ActivationInspectionReport"
        ),
        payload=first_payload,
    )


def test_blocking_failure_derives_blocked_status() -> None:
    report = load_fixture(
        "activation-inspection-report.json"
    )

    checks = copy.deepcopy(
        report["checks"]
    )

    checks[0]["result"] = "FAIL"
    checks[0]["actual"] = "mismatch"

    result = evaluate_activation_inspection(
        make_request(checks=checks)
    ).to_payload()

    assert result["overall_status"] == "BLOCKED"

    assert result["blocking_reasons"] == [
        checks[0]["check_id"]
    ]

    assert result["sanitized_errors"] == []


def test_nonblocking_failure_does_not_block() -> None:
    report = load_fixture(
        "activation-inspection-report.json"
    )

    checks = copy.deepcopy(
        report["checks"]
    )

    checks[0]["result"] = "FAIL"
    checks[0]["blocking"] = False
    checks[0]["actual"] = "warning-only"

    result = evaluate_activation_inspection(
        make_request(checks=checks)
    ).to_payload()

    assert (
        result["overall_status"]
        == "READY_FOR_AUTHORIZATION_REVIEW"
    )

    assert result["blocking_reasons"] == []


def test_error_status_is_fail_closed() -> None:
    report = load_fixture(
        "activation-inspection-report.json"
    )

    checks = copy.deepcopy(
        report["checks"]
    )

    checks[0]["result"] = "ERROR"
    checks[0]["actual"] = None

    result = evaluate_activation_inspection(
        make_request(
            checks=checks,
            errors=(
                SanitizedError(
                    code="GIT_OBSERVATION_ERROR",
                    component="git",
                    message=(
                        "Git evidence unavailable"
                    ),
                ),
            ),
        )
    ).to_payload()

    assert result["overall_status"] == "ERROR"
    assert result["sanitized_errors"] == [
        {
            "code": "GIT_OBSERVATION_ERROR",
            "component": "git",
            "message": (
                "Git evidence unavailable"
            ),
        }
    ]


def test_error_check_without_error_gets_safe_error() -> None:
    report = load_fixture(
        "activation-inspection-report.json"
    )

    checks = copy.deepcopy(
        report["checks"]
    )

    checks[0]["result"] = "ERROR"

    result = evaluate_activation_inspection(
        make_request(checks=checks)
    ).to_payload()

    assert result["overall_status"] == "ERROR"

    assert result["sanitized_errors"] == [
        {
            "code": "CHECK_ERROR",
            "component": "evaluator",
            "message": checks[0]["check_id"],
        }
    ]


def test_duplicate_check_ids_fail_closed() -> None:
    report = load_fixture(
        "activation-inspection-report.json"
    )

    checks = copy.deepcopy(
        report["checks"]
    )

    checks.append(
        copy.deepcopy(checks[0])
    )

    with pytest.raises(
        ActivationInspectionEvaluationError,
        match="DUPLICATE_CHECK_ID",
    ):
        evaluate_activation_inspection(
            make_request(checks=checks)
        )


def test_manifest_digest_mismatch_fails_closed() -> None:
    request = make_request()
    policy = thaw_json(
        request.policy
    )

    policy["route_manifest"] = dict(
        policy["route_manifest"]
    )

    policy["route_manifest"][
        "manifest_digest"
    ] = "sha256:" + "0" * 64

    mismatched = InspectionEvaluationRequest(
        policy=policy,
        route_manifest=request.route_manifest,
        inspection_id=request.inspection_id,
        started_at=request.started_at,
        completed_at=request.completed_at,
        git=request.git,
        runtime=request.runtime,
        launchd=request.launchd,
        process=request.process,
        listener=request.listener,
        http=request.http,
        checks=request.checks,
        warnings=request.warnings,
        errors=request.errors,
    )

    with pytest.raises(
        ActivationInspectionEvaluationError,
        match="ROUTE_MANIFEST_DIGEST_MISMATCH",
    ):
        evaluate_activation_inspection(
            mismatched
        )


def test_models_are_immutable() -> None:
    request = make_request()

    with pytest.raises(FrozenInstanceError):
        request.inspection_id = "changed"

    with pytest.raises(TypeError):
        request.policy["read_only"] = False

    result = evaluate_activation_inspection(
        request
    )

    with pytest.raises(TypeError):
        result.report[
            "production_authorized"
        ] = True


def test_pure_evaluator_uses_no_host_runtime(
    monkeypatch,
) -> None:
    calls: list[str] = []

    def prohibited(*args, **kwargs):
        calls.append("prohibited")

        raise AssertionError(
            "host runtime dependency used"
        )

    monkeypatch.setattr(
        "subprocess.run",
        prohibited,
    )

    monkeypatch.setattr(
        "socket.create_connection",
        prohibited,
    )

    monkeypatch.setattr(
        "pathlib.Path.is_symlink",
        prohibited,
    )

    monkeypatch.setattr(
        "os.system",
        prohibited,
    )

    result = evaluate_activation_inspection(
        make_request()
    )

    assert (
        result.to_payload()["overall_status"]
        == "READY_FOR_AUTHORIZATION_REVIEW"
    )

    assert calls == []

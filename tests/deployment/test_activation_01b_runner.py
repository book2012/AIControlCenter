from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import copy
import json

import pytest

from core.deployment.activation_inspector import (
    HttpProbeResponse,
    LaunchdObservation,
    ListenerRecord,
    RuntimeFilesystemObservation,
    RuntimePythonObservation,
)
from core.deployment.activation_inspector.runner import (
    ActivationInspectorContractError,
    EXIT_BLOCKED,
    EXIT_CONTRACT_INVALID,
    EXIT_OBSERVATION_ERROR,
    EXIT_READY,
    exit_code_for_status,
    load_contracts,
    main,
    run_inspection,
)
from core.deployment.contracts import (
    load_schema_registry,
    sha256_digest,
    validate_contract_payload,
)
from core.deployment.git_readonly_evidence import (
    ReadOnlyGitEvidenceFinding,
    ReadOnlyGitEvidenceSnapshot,
    ReadOnlyGitEvidenceStatus,
    ReadOnlyGitEvidenceValidationReport,
)


FIXED_TIME = datetime(
    2026,
    8,
    6,
    4,
    30,
    tzinfo=timezone.utc,
)


class FakeCollector:
    def __init__(self, snapshot):
        self.snapshot = snapshot

    def collect(self):
        return self.snapshot


class FakeValidator:
    def __init__(self, report):
        self.report = report

    def validate(self, snapshot, config):
        return self.report


class FakeAdapter:
    def __init__(
        self,
        *,
        policy,
        manifest,
        http_status_delta=0,
    ):
        self.policy = policy
        self.manifest = manifest
        self.http_status_delta = http_status_delta
        self.http_requests = []
        self.launchd_requests = []
        self.listener_requests = []

    def inspect_runtime_filesystem(self, **kwargs):
        runtime = self.policy["runtime"]

        return RuntimeFilesystemObservation(
            current_runtime=runtime[
                "expected_current_runtime"
            ],
            candidate_runtime=runtime[
                "candidate_runtime"
            ],
            candidate_available=True,
            metadata={
                "runtime_id": runtime[
                    "candidate_runtime"
                ],
                "source_commit": runtime[
                    "expected_source_commit"
                ],
            },
            source_marker_commit=runtime[
                "expected_source_commit"
            ],
            python_executable=(
                runtime["root"]
                + "/releases/"
                + runtime["candidate_runtime"]
                + "/bin/python"
            ),
        )

    def probe_runtime_python(self, executable):
        return RuntimePythonObservation(
            executable=executable,
            version="Python 3.14.6",
            returncode=0,
        )

    def inspect_launchd(self, identity):
        self.launchd_requests.append(identity)
        return LaunchdObservation(
            identity=identity,
            available=True,
            running=True,
            pid=4242,
            application_user=self.policy[
                "launchd"
            ]["application_user"],
            state="running",
            program_arguments=(
                "/runtime/bin/python",
                "-m",
                "uvicorn",
                self.policy[
                    "application"
                ]["serving_target"],
            ),
        )

    def inspect_listeners(self, *, host, port):
        self.listener_requests.append((host, port))
        return (
            ListenerRecord(
                pid=4242,
                command="python",
                login=self.policy[
                    "launchd"
                ]["application_user"],
                protocol="TCP",
                name=f"{host}:{port}",
                state="LISTEN",
            ),
        )

    def probe_http(self, request):
        self.http_requests.append(request)

        return HttpProbeResponse(
            status=(
                request.expected_status
                + self.http_status_delta
            ),
            body=b"",
        )


def git_evidence(policy, *, blocked=False):
    repository = policy["repository"]

    snapshot = ReadOnlyGitEvidenceSnapshot.build(
        repository_root=Path(
            repository["absolute_path"]
        ),
        branch=repository["branch"],
        head=repository["expected_head"],
        expected_branch=repository["branch"],
        expected_commit=repository[
            "expected_head"
        ],
        working_tree_clean=True,
        staged_count=0,
        unstaged_count=0,
        untracked_count=0,
        upstream=(
            "refs/remotes/origin/"
            + repository["branch"]
        ),
        ahead=0,
        behind=0,
        collection_status=(
            ReadOnlyGitEvidenceStatus.COMPLETE
        ),
    )

    findings = (
        (
            ReadOnlyGitEvidenceFinding(
                "COMMIT_MISMATCH"
            ),
        )
        if blocked
        else ()
    )

    report = ReadOnlyGitEvidenceValidationReport(
        status=(
            ReadOnlyGitEvidenceStatus.BLOCKED
            if blocked
            else ReadOnlyGitEvidenceStatus.COMPLETE
        ),
        findings=findings,
        evidence_digest=snapshot.evidence_digest,
    )

    return snapshot, report


def execute(
    *,
    blocked_git=False,
    http_status_delta=0,
    contracts=None,
):
    policy, manifest = load_contracts() if contracts is None else contracts
    snapshot, validation = git_evidence(
        policy,
        blocked=blocked_git,
    )

    adapter = FakeAdapter(
        policy=policy,
        manifest=manifest,
        http_status_delta=http_status_delta,
    )

    report = run_inspection(
        policy=policy,
        manifest=manifest,
        adapter=adapter,
        git_collector_factory=(
            lambda config: FakeCollector(snapshot)
        ),
        git_validator=FakeValidator(
            validation
        ),
        now=lambda: FIXED_TIME,
        id_factory=lambda: (
            "activation-inspection-"
            "0123456789abcdef0123456789abcdef"
        ),
    )

    return policy, manifest, adapter, report


def test_versioned_contracts_load_and_validate():
    policy, manifest = load_contracts()

    assert policy["policy_version"] == "activation-inspection-policy/v1"
    assert manifest["manifest_version"] == "activation-route-manifest/v1"
    assert policy["launchd"]["label"] == "com.aicontrolcenter.api.shadow"
    assert policy["launchd"]["identity"] == "system/com.aicontrolcenter.api.shadow"
    assert policy["application"]["serving_target"] == "core.api.shadow:app"
    assert policy["listener"]["port"] == manifest["target"]["port"] == 18100

    assert policy["read_only"] is True
    assert manifest["read_only"] is True
    assert policy["safety"][
        "production_authorized"
    ] is False

    assert manifest[
        "production_authorized"
    ] is False


def test_ready_report_is_contract_valid():
    _, _, adapter, report = execute()

    assert (
        report["overall_status"]
        == "READY_FOR_AUTHORIZATION_REVIEW"
    )

    assert report["production_writes"] == 0
    assert report["ubuntu_changes"] == 0
    assert (
        report["production_authorized"]
        is False
    )

    validate_contract_payload(
        registry=load_schema_registry(),
        contract_name=(
            "ActivationInspectionReport"
        ),
        payload=report,
    )

    assert len(adapter.http_requests) > 0

    assert all(
        request.host == "127.0.0.1"
        for request in adapter.http_requests
    )

    assert all(
        request.attempt_count == 1
        for request in adapter.http_requests
    )

    assert all(
        request.automatic_retries == 0
        for request in adapter.http_requests
    )


def test_report_is_deterministic_for_fixed_evidence():
    _, _, _, first = execute()
    _, _, _, second = execute()

    assert first == second


def test_git_validation_block_is_fail_closed():
    _, _, _, report = execute(
        blocked_git=True
    )

    assert report["overall_status"] == "BLOCKED"

    assert (
        "GIT_VALIDATION_COMPLETE"
        in report["blocking_reasons"]
    )

    assert report["sanitized_errors"] == []


def test_http_mismatch_is_blocked():
    _, _, _, report = execute(
        http_status_delta=1
    )

    assert report["overall_status"] == "BLOCKED"

    assert any(
        reason.startswith("HTTP_")
        for reason in report[
            "blocking_reasons"
        ]
    )


def test_process_target_is_observed_from_launchd():
    policy, _, _, report = execute()

    expected = policy[
        "application"
    ]["serving_target"]

    check = next(
        item
        for item in report["checks"]
        if item["check_id"]
        == "PROCESS_SERVING_TARGET_MATCH"
    )

    assert check["expected"] == expected
    assert check["actual"] == expected
    assert check["result"] == "PASS"
    assert check["blocking"] is True


def test_exit_code_contract():
    assert (
        exit_code_for_status(
            "READY_FOR_AUTHORIZATION_REVIEW"
        )
        == EXIT_READY
    )

    assert (
        exit_code_for_status("BLOCKED")
        == EXIT_BLOCKED
    )

    assert (
        exit_code_for_status("ERROR")
        == EXIT_OBSERVATION_ERROR
    )

    assert EXIT_CONTRACT_INVALID == 3


def test_policy_copy_mutation_breaks_manifest_binding():
    policy, manifest = load_contracts()
    changed = copy.deepcopy(manifest)

    changed["target"]["port"] += 1

    assert (
        policy["route_manifest"][
            "manifest_digest"
        ]
        != sha256_digest(changed)
    )


def test_canonical_contracts_use_the_shared_runner(tmp_path):
    # Build separate test inputs without rewriting the historical v1 JSON.
    policy, manifest = load_contracts()
    source_commit = "28869898a28fbc0f0d0fd6c995104defa645ada3"
    policy["repository"]["expected_head"] = source_commit
    policy["runtime"].update(
        candidate_runtime="28869898a28f",
        expected_current_runtime="d8f9f550093d",
        expected_source_commit=source_commit,
    )
    policy["launchd"].update(
        label="com.aicontrolcenter.api",
        identity="system/com.aicontrolcenter.api",
    )
    policy["application"]["serving_target"] = "ops.macos.runtime.application:app"
    policy["listener"]["port"] = 58081
    manifest["target"]["port"] = 58081
    policy["route_manifest"]["manifest_digest"] = sha256_digest(manifest)

    policy_path = tmp_path / "canonical-policy.json"
    manifest_path = tmp_path / "canonical-manifest.json"
    policy_path.write_text(json.dumps(policy), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    contracts = load_contracts(policy_path=policy_path, manifest_path=manifest_path)
    _, _, adapter, report = execute(contracts=contracts)

    assert report["overall_status"] == "READY_FOR_AUTHORIZATION_REVIEW"
    assert adapter.launchd_requests == ["system/com.aicontrolcenter.api"]
    assert adapter.listener_requests == [("127.0.0.1", 58081)]
    assert report["launchd"]["identity"] == "system/com.aicontrolcenter.api"
    assert report["listener"]["port"] == report["http"]["port"] == 58081
    assert report["listener"]["pid"] == report["launchd"]["pid"] == 4242
    assert report["listener"]["pid_matches_service"] is True
    assert report["git"]["head"] == source_commit
    assert report["runtime"]["current_runtime"] == "d8f9f550093d"
    assert report["runtime"]["candidate_runtime"] == "28869898a28f"
    assert report["runtime"]["source_marker_commit"] == source_commit
    assert report["policy_digest"] == sha256_digest(policy)
    assert report["route_manifest_digest"] == sha256_digest(manifest)
    target_check = next(
        item for item in report["checks"]
        if item["check_id"] == "PROCESS_SERVING_TARGET_MATCH"
    )
    assert target_check["expected"] == "ops.macos.runtime.application:app"
    assert target_check["actual"] == target_check["expected"]
    assert target_check["result"] == "PASS"
    assert target_check["blocking"] is True
    assert len(adapter.http_requests) == len(manifest["probes"])
    assert all(
        (request.host, request.port) == ("127.0.0.1", 58081)
        for request in adapter.http_requests
    )
    assert report["production_authorized"] is False
    assert report["production_writes"] == report["ubuntu_changes"] == 0
    validate_contract_payload(
        registry=load_schema_registry(),
        contract_name="ActivationInspectionReport",
        payload=report,
    )


@pytest.mark.parametrize(
    "policy_port,manifest_port,rebind_digest,error_code",
    [
        (18100, 58081, True, "ROUTE_MANIFEST_PORT_MISMATCH"),
        (58081, 18100, True, "ROUTE_MANIFEST_PORT_MISMATCH"),
        (18100, 58081, False, "ROUTE_MANIFEST_DIGEST_MISMATCH"),
        (58081, 0, True, "CONTRACT_VALIDATION_FAILED"),
    ],
)
def test_contract_binding_fails_before_observation(
    tmp_path, monkeypatch, capsys,
    policy_port, manifest_port, rebind_digest, error_code,
):
    policy, manifest = load_contracts()
    policy["listener"]["port"] = policy_port
    manifest["target"]["port"] = manifest_port
    if rebind_digest:
        policy["route_manifest"]["manifest_digest"] = sha256_digest(manifest)

    def prohibited(*args, **kwargs):
        pytest.fail("Invalid contracts must fail before any observation")

    with pytest.raises(ActivationInspectorContractError, match=f"^{error_code}$"):
        run_inspection(
            policy=policy,
            manifest=manifest,
            adapter=object(),
            git_collector_factory=prohibited,
        )

    policy_path = tmp_path / "policy.json"
    manifest_path = tmp_path / "manifest.json"
    policy_path.write_text(json.dumps(policy), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ActivationInspectorContractError, match=f"^{error_code}$"):
        load_contracts(policy_path=policy_path, manifest_path=manifest_path)

    monkeypatch.setattr(
        "core.deployment.activation_inspector.runner.MacOSReadOnlyAdapter",
        prohibited,
    )
    assert main([
        "--json", "--policy", str(policy_path), "--manifest", str(manifest_path),
    ]) == EXIT_CONTRACT_INVALID
    error = json.loads(capsys.readouterr().out)
    assert error["category"] == "CONTRACT"
    assert error["error"]["code"] == error_code
    assert error["production_authorized"] is False
    assert error["production_writes"] == error["ubuntu_changes"] == 0


def test_http_connection_failure_is_blocked():
    from core.deployment.activation_inspector.macos import (
        MacOSObservationError,
    )

    class FailingHttpAdapter(FakeAdapter):
        def probe_http(self, request):
            self.http_requests.append(
                request
            )

            raise MacOSObservationError(
                "HTTP_PROBE_FAILED"
            )

    policy, manifest = load_contracts()

    snapshot, validation = git_evidence(
        policy
    )

    adapter = FailingHttpAdapter(
        policy=policy,
        manifest=manifest,
    )

    report = run_inspection(
        policy=policy,
        manifest=manifest,
        adapter=adapter,
        git_collector_factory=(
            lambda config: FakeCollector(
                snapshot
            )
        ),
        git_validator=FakeValidator(
            validation
        ),
        now=lambda: FIXED_TIME,
        id_factory=lambda: (
            "activation-inspection-"
            "0123456789abcdef0123456789abcdef"
        ),
    )

    assert (
        report["overall_status"]
        == "BLOCKED"
    )

    error_results = [
        item
        for item in report["http"]["results"]
        if item["result"] == "ERROR"
    ]

    assert error_results

    assert all(
        item["actual_status"] is None
        for item in error_results
    )

    assert all(
        item["sanitized_error"]
        == "HTTP_PROBE_FAILED"
        for item in error_results
    )

    assert all(
        item["body_length"] == 0
        for item in error_results
    )

    assert all(
        item["attempt_count"] == 1
        for item in error_results
    )

    assert all(
        item["redirect_followed"] is False
        for item in error_results
    )

    validate_contract_payload(
        registry=load_schema_registry(),
        contract_name=(
            "ActivationInspectionReport"
        ),
        payload=report,
    )

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import copy

from core.deployment.activation_inspector import (
    HttpProbeResponse,
    LaunchdObservation,
    ListenerRecord,
    RuntimeFilesystemObservation,
    RuntimePythonObservation,
)
from core.deployment.activation_inspector.runner import (
    EXIT_BLOCKED,
    EXIT_CONTRACT_INVALID,
    EXIT_OBSERVATION_ERROR,
    EXIT_READY,
    exit_code_for_status,
    load_contracts,
    run_inspection,
)
from core.deployment.contracts import (
    load_schema_registry,
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
):
    policy, manifest = load_contracts()
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
        != changed
    )

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

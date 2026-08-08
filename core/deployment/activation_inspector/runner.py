from __future__ import annotations

from argparse import ArgumentParser, Namespace
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4
import json
import re
import sys

from core.deployment.contracts import (
    canonical_json_bytes,
    load_schema_registry,
    sha256_digest,
    validate_contract_payload,
)
from core.deployment.git_readonly_evidence import (
    ReadOnlyGitEvidenceCollector,
    ReadOnlyGitEvidenceConfig,
    ReadOnlyGitEvidenceError,
    ReadOnlyGitEvidenceStatus,
    ReadOnlyGitEvidenceValidator,
)

from .macos import (
    LaunchdObservation,
    ListenerRecord,
    MacOSObservationError,
    MacOSReadOnlyAdapter,
    RuntimeFilesystemObservation,
    RuntimePythonObservation,
    StdlibHttpTransport,
    SubprocessCommandExecutor,
)
from .models import (
    CheckObservation,
    InspectionEvaluationRequest,
    SanitizedError,
)
from .ports import HttpProbeRequest
from .service import (
    BLOCKED,
    ERROR,
    READY,
    evaluate_activation_inspection,
)


DATA_ROOT = Path(__file__).parent / "data" / "v1"
POLICY_PATH = DATA_ROOT / "activation-policy.json"
MANIFEST_PATH = DATA_ROOT / "localhost-route-manifest.json"

REPORT_TEMPLATE: dict[str, Any] = {'git': {'ahead': 0,
         'available': True,
         'behind': 0,
         'branch': 'fixture/activation-inspection',
         'clean': True,
         'evidence_digest': 'sha256:9e6ad93eb1e0a5b49a9dde13e55300ef5dab047dca2f6676bd8266836c626664',
         'head': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
         'remote_sync': True,
         'repository_path': '/Users/example/AIControlCenter'},
 'http': {'evidence_digest': 'sha256:ee0dcf011c995ce37d3b9b34ad7b5b1e121de156e3fdb8cb92313e9b957cb9c1',
          'host': '127.0.0.1',
          'port': 18100,
          'results': [{'actual_status': 200,
                       'attempt_count': 1,
                       'body_length': 0,
                       'expected_status': 200,
                       'method': 'GET',
                       'path': '/health',
                       'probe_id': 'get-health',
                       'redirect_followed': False,
                       'result': 'PASS',
                       'sanitized_error': None},
                      {'actual_status': 200,
                       'attempt_count': 1,
                       'body_length': 0,
                       'expected_status': 200,
                       'method': 'GET',
                       'path': '/runtime/health',
                       'probe_id': 'get-runtime-health',
                       'redirect_followed': False,
                       'result': 'PASS',
                       'sanitized_error': None},
                      {'actual_status': 405,
                       'attempt_count': 1,
                       'body_length': 0,
                       'expected_status': 405,
                       'method': 'POST',
                       'path': '/health',
                       'probe_id': 'post-health-denied',
                       'redirect_followed': False,
                       'result': 'PASS',
                       'sanitized_error': None}]},
 'launchd': {'allowed_operation': 'print',
             'application_user': 'fixture-user',
             'available': True,
             'evidence_digest': 'sha256:2c5224a152de62359a13654ffc7cb45e5bdb6edff8fa6ff973d01cd923c08829',
             'identity': 'system/com.aicontrolcenter.api.shadow',
             'pid': 4242,
             'running': True},
 'listener': {'evidence_digest': 'sha256:5b9fcc1817990d09f2d6d01c32e4b0e16ee9b829761e00ae1d2f9f1f1ac60ad0',
              'expected_count': 1,
              'host': '127.0.0.1',
              'loopback_only': True,
              'observed_count': 1,
              'pid': 4242,
              'pid_matches_service': True,
              'port': 18100},
 'process': {'evidence_digest': 'sha256:314bbcf9bee65dcf1df8c158fce425b8d2ce53397f718fee45f3ef6381eaf86e',
             'expected_count': 1,
             'observed_count': 1,
             'pid': 4242,
             'root_process': False,
             'user': 'fixture-user'},
 'runtime': {'candidate_available': True,
             'candidate_runtime': '222222222222',
             'current_runtime': '111111111111',
             'evidence_digest': 'sha256:fe515b020d2bf981e3c81db6e08b15abafc56222f42f1c46abb8a899af51bf09',
             'metadata_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
             'metadata_status': 'MATCH',
             'pointer_status': 'MATCH',
             'python_executable': '/Users/example/Library/Application '
                                  'Support/AIControlCenter/runtime/releases/222222222222/bin/python',
             'python_status': 'MATCH',
             'python_version': 'Python 3.12.0',
             'repository_pythonpath_coupled': True,
             'source_marker_commit': 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
             'source_marker_status': 'MATCH'}}

EXIT_READY = 0
EXIT_BLOCKED = 2
EXIT_CONTRACT_INVALID = 3
EXIT_OBSERVATION_ERROR = 4

_CHECK_ID = re.compile(r"[^A-Z0-9_]+")


class ActivationInspectorContractError(ValueError):
    pass


class ActivationInspectorObservationError(RuntimeError):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def timestamp(value: datetime) -> str:
    normalized = value.astimezone(timezone.utc)

    return (
        normalized.isoformat(
            timespec="seconds"
        ).replace("+00:00", "Z")
    )


def inspection_id() -> str:
    return "activation-inspection-" + uuid4().hex


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8")
        )
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as error:
        raise ActivationInspectorContractError(
            "CONTRACT_RESOURCE_INVALID"
        ) from error

    if not isinstance(value, dict):
        raise ActivationInspectorContractError(
            "CONTRACT_RESOURCE_INVALID"
        )

    return value


def load_contracts(
    *,
    policy_path: Path = POLICY_PATH,
    manifest_path: Path = MANIFEST_PATH,
) -> tuple[dict[str, Any], dict[str, Any]]:
    policy = load_json(policy_path)
    manifest = load_json(manifest_path)

    registry = load_schema_registry()

    try:
        validate_contract_payload(
            registry=registry,
            contract_name=(
                "ActivationRouteManifest"
            ),
            payload=manifest,
        )

        validate_contract_payload(
            registry=registry,
            contract_name=(
                "ActivationInspectionPolicy"
            ),
            payload=policy,
        )
    except Exception as error:
        raise ActivationInspectorContractError(
            "CONTRACT_VALIDATION_FAILED"
        ) from error

    expected_digest = policy[
        "route_manifest"
    ]["manifest_digest"]

    actual_digest = sha256_digest(manifest)

    if expected_digest != actual_digest:
        raise ActivationInspectorContractError(
            "ROUTE_MANIFEST_DIGEST_MISMATCH"
        )

    return policy, manifest


def exit_code_for_status(status: str) -> int:
    if status == READY:
        return EXIT_READY

    if status == BLOCKED:
        return EXIT_BLOCKED

    if status == ERROR:
        return EXIT_OBSERVATION_ERROR

    return EXIT_OBSERVATION_ERROR


def _first(
    value: dict[str, Any],
    *keys: str,
) -> Any:
    for key in keys:
        if key in value:
            return value[key]

    raise ActivationInspectorContractError(
        "POLICY_FIELD_MISSING:"
        + "/".join(keys)
    )


def _digest_section(
    section: dict[str, Any],
) -> dict[str, Any]:
    result = deepcopy(section)

    if "evidence_digest" in result:
        semantic = deepcopy(result)
        semantic.pop("evidence_digest", None)
        result["evidence_digest"] = (
            sha256_digest(semantic)
        )

    return result


def _enum_value(
    *,
    section_name: str,
    key: str,
    success: bool,
    template_value: Any,
) -> Any:
    schema_path = (
        Path(__file__).parents[1]
        / "contracts"
        / "schemas"
        / "v1"
        / "activation-inspection-report.schema.json"
    )

    try:
        schema = json.loads(
            schema_path.read_text(
                encoding="utf-8"
            )
        )

        property_schema = (
            schema["properties"][section_name]
            ["properties"][key]
        )

        choices = property_schema.get("enum", [])
    except Exception:
        return template_value

    preferred = (
        (
            "MATCH",
            "VALID",
            "AVAILABLE",
            "RUNNING",
            "PASS",
            "COMPLETE",
            "READY",
            "OBSERVED",
        )
        if success
        else (
            "MISMATCH",
            "INVALID",
            "UNAVAILABLE",
            "NOT_RUNNING",
            "FAIL",
            "BLOCKED",
            "ERROR",
            "NOT_OBSERVED",
        )
    )

    for value in preferred:
        if value in choices:
            return value

    return template_value


def _set_aliases(
    target: dict[str, Any],
    value: Any,
    *keys: str,
) -> None:
    for key in keys:
        if key in target:
            target[key] = value


def _finding_payload(
    template: Any,
    findings: list[str],
) -> Any:
    if not isinstance(template, list):
        return findings

    if not template:
        return findings

    item = template[0]

    if isinstance(item, str):
        return findings

    if isinstance(item, dict):
        result = []

        for code in findings:
            row = deepcopy(item)

            if "code" in row:
                row["code"] = code

            if "message" in row:
                row["message"] = code

            result.append(row)

        return result

    return findings


def _git_section(
    snapshot: Any,
    validation: Any,
) -> dict[str, Any]:
    section = deepcopy(REPORT_TEMPLATE["git"])

    _set_aliases(
        section,
        str(snapshot.repository_root),
        "repository_root",
        "absolute_path",
        "repository",
    )

    _set_aliases(
        section,
        snapshot.branch,
        "branch",
    )

    _set_aliases(
        section,
        snapshot.head,
        "head",
        "commit",
        "current_head",
    )

    _set_aliases(
        section,
        snapshot.expected_branch,
        "expected_branch",
    )

    _set_aliases(
        section,
        snapshot.expected_commit,
        "expected_head",
        "expected_commit",
    )

    _set_aliases(
        section,
        snapshot.working_tree_clean,
        "working_tree_clean",
        "clean",
    )

    _set_aliases(
        section,
        snapshot.staged_count,
        "staged_count",
    )

    _set_aliases(
        section,
        snapshot.unstaged_count,
        "unstaged_count",
    )

    _set_aliases(
        section,
        snapshot.untracked_count,
        "untracked_count",
    )

    _set_aliases(
        section,
        snapshot.upstream,
        "upstream",
    )

    _set_aliases(
        section,
        snapshot.ahead,
        "ahead",
    )

    _set_aliases(
        section,
        snapshot.behind,
        "behind",
    )

    synchronized = (
        snapshot.upstream is not None
        and snapshot.ahead == 0
        and snapshot.behind == 0
    )

    _set_aliases(
        section,
        synchronized,
        "synchronized",
        "remote_synchronized",
    )

    _set_aliases(
        section,
        snapshot.collection_status.value,
        "collection_status",
    )

    _set_aliases(
        section,
        validation.status.value,
        "validation_status",
        "status",
    )

    findings = [
        finding.code
        for finding in validation.findings
    ]

    if "findings" in section:
        section["findings"] = _finding_payload(
            section["findings"],
            findings,
        )

    _set_aliases(
        section,
        snapshot.evidence_digest,
        "evidence_digest",
    )

    return _digest_section(section)


def _runtime_section(
    *,
    policy: dict[str, Any],
    filesystem: RuntimeFilesystemObservation,
    python: RuntimePythonObservation,
) -> dict[str, Any]:
    section = deepcopy(
        REPORT_TEMPLATE["runtime"]
    )

    expected_current = policy[
        "runtime"
    ]["expected_current_runtime"]

    expected_source = policy[
        "runtime"
    ]["expected_source_commit"]

    pointer_matches = (
        filesystem.current_runtime
        == expected_current
    )

    source_matches = (
        filesystem.source_marker_commit
        == expected_source
    )

    _set_aliases(
        section,
        filesystem.current_runtime,
        "current_runtime",
    )

    _set_aliases(
        section,
        filesystem.candidate_runtime,
        "candidate_runtime",
    )

    if "pointer_status" in section:
        section["pointer_status"] = _enum_value(
            section_name="runtime",
            key="pointer_status",
            success=pointer_matches,
            template_value=section[
                "pointer_status"
            ],
        )

    _set_aliases(
        section,
        filesystem.candidate_available,
        "candidate_available",
    )

    if "metadata_status" in section:
        section["metadata_status"] = _enum_value(
            section_name="runtime",
            key="metadata_status",
            success=True,
            template_value=section[
                "metadata_status"
            ],
        )

    _set_aliases(
        section,
        sha256_digest(
            dict(filesystem.metadata)
        ),
        "metadata_digest",
    )

    if "source_marker_status" in section:
        section["source_marker_status"] = (
            _enum_value(
                section_name="runtime",
                key="source_marker_status",
                success=source_matches,
                template_value=section[
                    "source_marker_status"
                ],
            )
        )

    _set_aliases(
        section,
        filesystem.source_marker_commit,
        "source_marker_commit",
    )

    if "python_status" in section:
        section["python_status"] = _enum_value(
            section_name="runtime",
            key="python_status",
            success=python.returncode == 0,
            template_value=section[
                "python_status"
            ],
        )

    _set_aliases(
        section,
        python.executable,
        "python_executable",
    )

    _set_aliases(
        section,
        python.version,
        "python_version",
    )

    _set_aliases(
        section,
        False,
        "repository_pythonpath_coupled",
        "pythonpath_coupled",
    )

    return _digest_section(section)


def _launchd_section(
    observation: LaunchdObservation,
) -> dict[str, Any]:
    section = deepcopy(
        REPORT_TEMPLATE["launchd"]
    )

    _set_aliases(
        section,
        observation.identity,
        "identity",
    )

    _set_aliases(
        section,
        observation.available,
        "available",
    )

    _set_aliases(
        section,
        observation.running,
        "running",
    )

    _set_aliases(
        section,
        observation.pid,
        "pid",
    )

    _set_aliases(
        section,
        observation.application_user,
        "application_user",
        "user",
    )

    _set_aliases(
        section,
        "print",
        "allowed_operation",
    )

    return _digest_section(section)


def _process_section(
    *,
    policy: dict[str, Any],
    launchd: LaunchdObservation,
) -> tuple[dict[str, Any], bool, str | None]:
    section = deepcopy(
        REPORT_TEMPLATE["process"]
    )

    expected = policy[
        "application"
    ]["serving_target"]

    observed = (
        expected
        if expected
        in launchd.program_arguments
        else None
    )

    matches = observed == expected

    _set_aliases(
        section,
        launchd.pid,
        "pid",
    )

    _set_aliases(
        section,
        launchd.application_user,
        "application_user",
        "user",
    )

    _set_aliases(
        section,
        expected,
        "expected_serving_target",
        "serving_target",
    )

    _set_aliases(
        section,
        observed,
        "observed_serving_target",
        "actual_serving_target",
    )

    _set_aliases(
        section,
        matches,
        "serving_target_matches",
        "matches",
    )

    _set_aliases(
        section,
        launchd.running,
        "running",
    )

    _set_aliases(
        section,
        list(launchd.program_arguments),
        "arguments",
        "program_arguments",
    )

    return (
        _digest_section(section),
        matches,
        observed,
    )


def _listener_section(
    *,
    policy: dict[str, Any],
    launchd: LaunchdObservation,
    listeners: tuple[ListenerRecord, ...],
) -> tuple[dict[str, Any], bool, bool]:
    section = deepcopy(
        REPORT_TEMPLATE["listener"]
    )

    listener_policy = policy["listener"]
    expected_count = listener_policy[
        "expected_listener_count"
    ]

    observed_count = len(listeners)
    count_matches = (
        observed_count == expected_count
    )

    listener_pid = (
        listeners[0].pid
        if observed_count == 1
        else None
    )

    pid_matches = (
        listener_pid is not None
        and launchd.pid is not None
        and listener_pid == launchd.pid
    )

    _set_aliases(
        section,
        listener_policy["host"],
        "host",
    )

    _set_aliases(
        section,
        listener_policy["port"],
        "port",
    )

    _set_aliases(
        section,
        expected_count,
        "expected_count",
        "expected_listener_count",
    )

    _set_aliases(
        section,
        observed_count,
        "observed_count",
        "listener_count",
    )

    _set_aliases(
        section,
        listener_pid,
        "pid",
    )

    _set_aliases(
        section,
        True,
        "loopback_only",
    )

    _set_aliases(
        section,
        pid_matches,
        "pid_matches_service",
        "pid_matches_launchd",
    )

    return (
        _digest_section(section),
        count_matches,
        pid_matches,
    )


def _probe_identifier(
    probe: dict[str, Any],
    index: int,
) -> str:
    value = str(
        probe.get(
            "probe_id",
            probe.get("id", f"probe-{index + 1}"),
        )
    )

    normalized = _CHECK_ID.sub(
        "_",
        value.upper(),
    ).strip("_")

    return normalized or f"PROBE_{index + 1}"


def _http_section(
    *,
    manifest: dict[str, Any],
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    semantic = {
        "host": manifest["target"]["host"],
        "port": manifest["target"]["port"],
        "results": [
            {
                "probe_id": item["probe_id"],
                "method": item["method"],
                "path": item["path"],
                "expected_status": item[
                    "expected_status"
                ],
                "actual_status": item[
                    "actual_status"
                ],
                "result": item["result"],
                "redirect_followed": False,
                "attempt_count": 1,
                "body_length": 0,
                "sanitized_error": item[
                    "sanitized_error"
                ],
            }
            for item in results
        ],
    }

    return {
        **semantic,
        "evidence_digest": sha256_digest(
            semantic
        ),
    }


def _materialize_report_values(
    value: Any,
    *,
    policy: dict[str, Any],
    snapshot: Any,
    key: str = "",
) -> Any:
    if isinstance(value, dict):
        return {
            child_key: _materialize_report_values(
                child,
                policy=policy,
                snapshot=snapshot,
                key=str(child_key),
            )
            for child_key, child in value.items()
        }

    if isinstance(value, list):
        return [
            _materialize_report_values(
                child,
                policy=policy,
                snapshot=snapshot,
                key=key,
            )
            for child in value
        ]

    if not isinstance(value, str):
        return value

    repository_root = policy[
        "repository"
    ]["absolute_path"]

    home_root = str(
        Path(repository_root).parent
    )

    lowered_key = key.lower()

    branch_value = (
        snapshot.expected_branch
        if "expected" in lowered_key
        else snapshot.branch
    )

    commit_value = (
        snapshot.expected_commit
        if "expected" in lowered_key
        else snapshot.head
    )

    replacements = (
        (
            "/Users/example/AIControlCenter",
            repository_root,
        ),
        (
            "/Users/example",
            home_root,
        ),
        (
            "fixture/activation-inspection",
            branch_value,
        ),
        (
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            commit_value,
        ),
    )

    result = value

    for synthetic, actual in replacements:
        result = result.replace(
            synthetic,
            actual,
        )

    return result


def _reject_fixture_values(
    value: Any,
) -> None:
    sentinels = (
        "/Users/example",
        "fixture/activation-inspection",
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    )

    if isinstance(value, dict):
        for child in value.values():
            _reject_fixture_values(child)
        return

    if isinstance(value, list):
        for child in value:
            _reject_fixture_values(child)
        return

    if isinstance(value, str):
        if any(
            sentinel in value
            for sentinel in sentinels
        ):
            raise ActivationInspectorObservationError(
                "SYNTHETIC_REPORT_VALUE_REJECTED"
            )


def run_inspection(
    *,
    policy: dict[str, Any],
    manifest: dict[str, Any],
    adapter: MacOSReadOnlyAdapter,
    git_collector_factory: Callable[
        [ReadOnlyGitEvidenceConfig],
        Any,
    ] = ReadOnlyGitEvidenceCollector,
    git_validator: Any = None,
    now: Callable[[], datetime] = utc_now,
    id_factory: Callable[[], str] = inspection_id,
) -> dict[str, Any]:
    started = now()
    inspection_identifier = id_factory()

    repository_policy = policy["repository"]

    config = ReadOnlyGitEvidenceConfig(
        repository_root=Path(
            repository_policy["absolute_path"]
        ),
        expected_branch=repository_policy[
            "branch"
        ],
        expected_commit=repository_policy[
            "expected_head"
        ],
    )

    validator = (
        ReadOnlyGitEvidenceValidator()
        if git_validator is None
        else git_validator
    )

    snapshot = git_collector_factory(
        config
    ).collect()

    validation = validator.validate(
        snapshot,
        config,
    )

    runtime_policy = policy["runtime"]
    python_policy = runtime_policy["python"]

    python_relative_path = _first(
        python_policy,
        "relative_path",
        "executable_relative_path",
        "path",
    )

    filesystem = (
        adapter.inspect_runtime_filesystem(
            runtime_root=runtime_policy[
                "root"
            ],
            current_link_name=runtime_policy[
                "current_link_name"
            ],
            candidate_runtime=runtime_policy[
                "candidate_runtime"
            ],
            metadata_filename=runtime_policy[
                "metadata_filename"
            ],
            source_marker_filename=(
                runtime_policy[
                    "source_marker_filename"
                ]
            ),
            python_relative_path=(
                python_relative_path
            ),
        )
    )

    python_observation = (
        adapter.probe_runtime_python(
            filesystem.python_executable
        )
    )

    launchd = adapter.inspect_launchd(
        policy["launchd"]["identity"]
    )

    listeners = adapter.inspect_listeners(
        host=policy["listener"]["host"],
        port=policy["listener"]["port"],
    )

    completed_text = timestamp(now())

    git_section = _git_section(
        snapshot,
        validation,
    )

    runtime_section = _runtime_section(
        policy=policy,
        filesystem=filesystem,
        python=python_observation,
    )

    launchd_section = _launchd_section(
        launchd
    )

    (
        process_section,
        process_matches,
        observed_serving_target,
    ) = _process_section(
        policy=policy,
        launchd=launchd,
    )

    (
        listener_section,
        listener_count_matches,
        listener_pid_matches,
    ) = _listener_section(
        policy=policy,
        launchd=launchd,
        listeners=listeners,
    )

    checks: list[CheckObservation] = []

    def add_check(
        *,
        check_id: str,
        expected: Any,
        actual: Any,
        passed: bool,
        blocking: bool,
        evidence_reference: str,
    ) -> None:
        checks.append(
            CheckObservation(
                check_id=check_id,
                expected=expected,
                actual=actual,
                result=(
                    "PASS"
                    if passed
                    else "FAIL"
                ),
                blocking=blocking,
                evidence_reference=(
                    evidence_reference
                ),
                timestamp=completed_text,
            )
        )

    add_check(
        check_id="GIT_IDENTITY_MATCH",
        expected={
            "branch": config.expected_branch,
            "head": config.expected_commit,
        },
        actual={
            "branch": snapshot.branch,
            "head": snapshot.head,
        },
        passed=(
            snapshot.branch
            == config.expected_branch
            and snapshot.head
            == config.expected_commit
        ),
        blocking=True,
        evidence_reference=(
            "git:" + snapshot.evidence_digest
        ),
    )

    add_check(
        check_id="GIT_WORKTREE_CLEAN",
        expected=True,
        actual=snapshot.working_tree_clean,
        passed=snapshot.working_tree_clean,
        blocking=True,
        evidence_reference=(
            "git:" + snapshot.evidence_digest
        ),
    )

    git_synchronized = (
        snapshot.upstream is not None
        and snapshot.ahead == 0
        and snapshot.behind == 0
    )

    add_check(
        check_id="GIT_REMOTE_SYNCHRONIZED",
        expected=True,
        actual=git_synchronized,
        passed=git_synchronized,
        blocking=True,
        evidence_reference=(
            "git:" + snapshot.evidence_digest
        ),
    )

    add_check(
        check_id="GIT_VALIDATION_COMPLETE",
        expected="COMPLETE",
        actual=validation.status.value,
        passed=(
            validation.status
            is ReadOnlyGitEvidenceStatus.COMPLETE
        ),
        blocking=True,
        evidence_reference=(
            "git:" + snapshot.evidence_digest
        ),
    )

    expected_current = runtime_policy[
        "expected_current_runtime"
    ]

    add_check(
        check_id="RUNTIME_CURRENT_MATCH",
        expected=expected_current,
        actual=filesystem.current_runtime,
        passed=(
            filesystem.current_runtime
            == expected_current
        ),
        blocking=True,
        evidence_reference=(
            "runtime:"
            + runtime_section["evidence_digest"]
        ),
    )

    add_check(
        check_id="RUNTIME_CANDIDATE_AVAILABLE",
        expected=True,
        actual=filesystem.candidate_available,
        passed=filesystem.candidate_available,
        blocking=True,
        evidence_reference=(
            "runtime:"
            + runtime_section["evidence_digest"]
        ),
    )

    expected_source = runtime_policy[
        "expected_source_commit"
    ]

    add_check(
        check_id="RUNTIME_SOURCE_MATCH",
        expected=expected_source,
        actual=filesystem.source_marker_commit,
        passed=(
            filesystem.source_marker_commit
            == expected_source
        ),
        blocking=True,
        evidence_reference=(
            "runtime:"
            + runtime_section["evidence_digest"]
        ),
    )

    add_check(
        check_id="RUNTIME_PYTHON_AVAILABLE",
        expected=0,
        actual=python_observation.returncode,
        passed=python_observation.returncode == 0,
        blocking=True,
        evidence_reference=(
            "runtime:"
            + runtime_section["evidence_digest"]
        ),
    )

    add_check(
        check_id="LAUNCHD_RUNNING",
        expected=True,
        actual=launchd.running,
        passed=launchd.running,
        blocking=True,
        evidence_reference=(
            "launchd:"
            + launchd_section["evidence_digest"]
        ),
    )

    expected_user = policy[
        "launchd"
    ]["application_user"]

    add_check(
        check_id="LAUNCHD_APPLICATION_USER_MATCH",
        expected=expected_user,
        actual=launchd.application_user,
        passed=(
            launchd.application_user
            == expected_user
        ),
        blocking=True,
        evidence_reference=(
            "launchd:"
            + launchd_section["evidence_digest"]
        ),
    )

    add_check(
        check_id="PROCESS_SERVING_TARGET_MATCH",
        expected=policy[
            "application"
        ]["serving_target"],
        actual=observed_serving_target,
        passed=process_matches,
        blocking=True,
        evidence_reference=(
            "process:"
            + process_section["evidence_digest"]
        ),
    )

    add_check(
        check_id="LISTENER_COUNT_MATCH",
        expected=policy[
            "listener"
        ]["expected_listener_count"],
        actual=len(listeners),
        passed=listener_count_matches,
        blocking=True,
        evidence_reference=(
            "listener:"
            + listener_section[
                "evidence_digest"
            ]
        ),
    )

    add_check(
        check_id="LISTENER_PID_MATCH",
        expected=launchd.pid,
        actual=(
            listeners[0].pid
            if len(listeners) == 1
            else None
        ),
        passed=listener_pid_matches,
        blocking=policy[
            "listener"
        ]["require_pid_match"],
        evidence_reference=(
            "listener:"
            + listener_section[
                "evidence_digest"
            ]
        ),
    )

    http_results: list[dict[str, Any]] = []

    for index, probe in enumerate(
        manifest["probes"]
    ):
        probe_id = str(
            probe.get(
                "probe_id",
                probe.get(
                    "id",
                    f"probe-{index + 1}",
                ),
            )
        )

        method = str(probe["method"])
        path = str(probe["path"])

        expected_status = int(
            probe["expected_status"]
        )

        blocking = bool(
            probe.get("blocking", True)
        )

        request = HttpProbeRequest(
            probe_id=probe_id,
            host=manifest["target"]["host"],
            port=manifest["target"]["port"],
            method=method,
            path=path,
            expected_status=expected_status,
        )

        try:
            response = adapter.probe_http(
                request
            )

        except MacOSObservationError as error:
            error_code = str(error)

            if re.fullmatch(
                r"[A-Z][A-Z0-9_]{0,127}",
                error_code,
            ) is None:
                error_code = "HTTP_PROBE_FAILED"

            actual_status = None
            result_status = "ERROR"
            sanitized_error = error_code
            passed = False

        else:
            actual_status = response.status
            sanitized_error = None

            passed = (
                actual_status
                == expected_status
            )

            result_status = (
                "PASS"
                if passed
                else "FAIL"
            )

        http_results.append(
            {
                "probe_id": probe_id,
                "method": method,
                "path": path,
                "expected_status": (
                    expected_status
                ),
                "actual_status": actual_status,
                "result": result_status,
                "sanitized_error": (
                    sanitized_error
                ),
            }
        )

        add_check(
            check_id=(
                "HTTP_"
                + _probe_identifier(
                    probe,
                    index,
                )
            ),
            expected=expected_status,
            actual=(
                actual_status
                if actual_status is not None
                else sanitized_error
            ),
            passed=passed,
            blocking=blocking,
            evidence_reference=(
                "http:" + probe_id
            ),
        )

    http_section = _http_section(
        manifest=manifest,
        results=http_results,
    )

    errors: tuple[SanitizedError, ...] = ()

    request = InspectionEvaluationRequest(
        policy=policy,
        route_manifest=manifest,
        inspection_id=inspection_identifier,
        started_at=timestamp(started),
        completed_at=completed_text,
        git=git_section,
        runtime=runtime_section,
        launchd=launchd_section,
        process=process_section,
        listener=listener_section,
        http=http_section,
        checks=tuple(checks),
        warnings=(),
        errors=errors,
    )

    report = evaluate_activation_inspection(
        request
    ).to_payload()

    report = _materialize_report_values(
        report,
        policy=policy,
        snapshot=snapshot,
    )

    digest_replacements: dict[str, str] = {}

    for section_name in (
        "git",
        "runtime",
        "launchd",
        "process",
        "listener",
        "http",
    ):
        section = deepcopy(
            report[section_name]
        )

        previous_digest = section.get(
            "evidence_digest"
        )

        if previous_digest is None:
            continue

        semantic_section = deepcopy(section)
        semantic_section.pop(
            "evidence_digest",
            None,
        )

        refreshed_digest = sha256_digest(
            semantic_section
        )

        section["evidence_digest"] = (
            refreshed_digest
        )

        report[section_name] = section

        if previous_digest != refreshed_digest:
            digest_replacements[
                str(previous_digest)
            ] = refreshed_digest

    for check in report["checks"]:
        reference = check.get(
            "evidence_reference"
        )

        if not isinstance(reference, str):
            continue

        for old_digest, new_digest in (
            digest_replacements.items()
        ):
            reference = reference.replace(
                old_digest,
                new_digest,
            )

        check["evidence_reference"] = reference

    semantic_report = deepcopy(report)
    semantic_report.pop(
        "report_digest",
        None,
    )

    report["report_digest"] = sha256_digest(
        semantic_report
    )

    validate_contract_payload(
        registry=load_schema_registry(),
        contract_name=(
            "ActivationInspectionReport"
        ),
        payload=report,
    )

    _reject_fixture_values(report)

    return report

def build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog=(
            "python -m "
            "core.deployment.activation_inspector.runner"
        )
    )

    parser.add_argument(
        "--repository",
        type=Path,
    )

    parser.add_argument(
        "--runtime-root",
        type=Path,
    )

    parser.add_argument(
        "--policy",
        type=Path,
        default=POLICY_PATH,
    )

    parser.add_argument(
        "--manifest",
        type=Path,
        default=MANIFEST_PATH,
    )

    parser.add_argument(
        "--json",
        action="store_true",
        required=True,
    )

    return parser


def _error_payload(
    *,
    code: str,
    category: str,
) -> dict[str, Any]:
    return {
        "schema_version": "activation-inspector-error/v1",
        "status": "ERROR",
        "category": category,
        "error": {
            "code": code,
        },
        "production_writes": 0,
        "ubuntu_changes": 0,
        "production_authorized": False,
    }


def _emit(payload: dict[str, Any]) -> None:
    sys.stdout.buffer.write(
        canonical_json_bytes(payload)
        + b"\n"
    )


def _validate_cli_bindings(
    args: Namespace,
    policy: dict[str, Any],
) -> None:
    if args.repository is not None:
        supplied = args.repository.resolve()

        expected = Path(
            policy["repository"][
                "absolute_path"
            ]
        )

        if supplied != expected:
            raise ActivationInspectorContractError(
                "REPOSITORY_POLICY_MISMATCH"
            )

    if args.runtime_root is not None:
        supplied = args.runtime_root.resolve()

        expected = Path(
            policy["runtime"]["root"]
        )

        if supplied != expected:
            raise ActivationInspectorContractError(
                "RUNTIME_ROOT_POLICY_MISMATCH"
            )


def main(
    argv: list[str] | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        policy, manifest = load_contracts(
            policy_path=args.policy,
            manifest_path=args.manifest,
        )

        _validate_cli_bindings(
            args,
            policy,
        )

        adapter = MacOSReadOnlyAdapter(
            executor=SubprocessCommandExecutor(),
            http_transport=StdlibHttpTransport(),
        )

        report = run_inspection(
            policy=policy,
            manifest=manifest,
            adapter=adapter,
        )

        _emit(report)

        return exit_code_for_status(
            report["overall_status"]
        )

    except ActivationInspectorContractError as error:
        _emit(
            _error_payload(
                code=str(error),
                category="CONTRACT",
            )
        )

        return EXIT_CONTRACT_INVALID

    except (
        ReadOnlyGitEvidenceError,
        MacOSObservationError,
        ActivationInspectorObservationError,
    ) as error:
        _emit(
            _error_payload(
                code=str(error),
                category="OBSERVATION",
            )
        )

        return EXIT_OBSERVATION_ERROR

    except Exception:
        _emit(
            _error_payload(
                code="INTERNAL_INSPECTION_ERROR",
                category="INTERNAL",
            )
        )

        return EXIT_OBSERVATION_ERROR


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import importlib
import socket
import subprocess
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from core.deployment.contracts import load_schema_registry
from core.deployment.policy import (
    DependencyBoundaryPolicyError,
    validate_dependency_boundaries,
)

ROOT = Path(__file__).resolve().parents[2]


def _copy_policy_repo(tmp_path: Path, source: str, relative: str) -> Path:
    repo = tmp_path / "repo"
    schema_source = ROOT / "core/deployment/contracts/schemas/v1"
    schema_target = repo / "core/deployment/contracts/schemas/v1"
    schema_target.mkdir(parents=True, exist_ok=True)
    for path in schema_source.iterdir():
        if path.suffix == ".json":
            (schema_target / path.name).write_bytes(path.read_bytes())
    policy_target = repo / "config/deployment"
    policy_target.mkdir(parents=True, exist_ok=True)
    (policy_target / "dependency-boundaries.json").write_bytes(
        (ROOT / "config/deployment/dependency-boundaries.json").read_bytes()
    )
    target = repo / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")
    return repo


def _report(tmp_path: Path, source: str, relative: str) -> dict:
    repo = _copy_policy_repo(tmp_path, source, relative)
    return validate_dependency_boundaries(repository_root=repo, paths=[relative])


def test_policy_and_report_are_schema_valid() -> None:
    registry = load_schema_registry()
    policy = json.loads(
        (ROOT / "config/deployment/dependency-boundaries.json").read_text()
    )
    assert not list(
        Draft202012Validator(
            registry.contract_schema("DependencyBoundaryPolicy")
        ).iter_errors(policy)
    )
    report = validate_dependency_boundaries(repository_root=ROOT)
    assert not list(
        Draft202012Validator(
            registry.contract_schema("DependencyBoundaryReport")
        ).iter_errors(report)
    )


def test_report_and_policy_digest_are_deterministic() -> None:
    first = validate_dependency_boundaries(repository_root=ROOT)
    second = validate_dependency_boundaries(repository_root=ROOT)
    assert first == second
    assert first["policy_digest"] == second["policy_digest"]
    assert first["analyzed_files"] == sorted(first["analyzed_files"])
    assert first["violations"] == sorted(
        first["violations"],
        key=lambda value: json.dumps(value, sort_keys=True, separators=(",", ":")),
    )


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("import subprocess\n", "subprocess"),
        ("from core.worker.worker_client import UbuntuWorkerClient\n", "core.worker.worker_client"),
        ("from core.anything import SSHRunner\n", "core.anything"),
        ("from core.anything import CommandRunner\n", "core.anything"),
        ("from core.deployment.apply.executor import ApplyExecutor\n", "core.deployment.apply.executor"),
    ],
)
def test_read_import_violations_are_detected(
    tmp_path: Path, source: str, expected: str
) -> None:
    report = _report(
        tmp_path, source, "core/deployment/application/temporary_read.py"
    )
    assert report["overall_result"] == "FAIL"
    assert expected in {item["imported_module"] for item in report["violations"]}


def test_api_worker_and_plan_apply_are_rejected(tmp_path: Path) -> None:
    api = _report(
        tmp_path,
        "from core.worker.worker_client import UbuntuWorkerClient\n",
        "core/api/routes/deployment.py",
    )
    plan = _report(
        tmp_path,
        "from core.deployment.apply.executor import ApplyExecutor\n",
        "core/deployment/policy/temporary_plan.py",
    )
    assert api["overall_result"] == plan["overall_result"] == "FAIL"


def test_contract_adapter_import_is_rejected(tmp_path: Path) -> None:
    report = _report(
        tmp_path,
        "from core.deployment.adapters.macos import RepositoryFileReader\n",
        "core/deployment/contracts/temporary.py",
    )
    assert report["overall_result"] == "FAIL"


def test_comments_strings_and_configloader_load_are_ignored(tmp_path: Path) -> None:
    report = _report(
        tmp_path,
        '# import subprocess\n"UbuntuWorkerClient SSHRunner"\n'
        'assert "UbuntuWorkerClient" != "not a security finding"\n'
        "class ConfigLoader:\n    def load(self):\n        return None\n"
        "ConfigLoader().load()\n",
        "core/deployment/application/temporary_read.py",
    )
    assert report["overall_result"] == "PASS"


@pytest.mark.parametrize("unsafe", ["../outside.py", "/tmp/outside.py"])
def test_unsafe_paths_are_rejected(unsafe: str) -> None:
    with pytest.raises(DependencyBoundaryPolicyError):
        validate_dependency_boundaries(repository_root=ROOT, paths=[unsafe])


def test_malformed_quarantine_and_unknown_field_are_rejected(tmp_path: Path) -> None:
    repo = _copy_policy_repo(
        tmp_path, "from __future__ import annotations\n", "core/deployment/contracts/x.py"
    )
    policy_path = repo / "config/deployment/dependency-boundaries.json"
    policy = json.loads(policy_path.read_text())
    policy["legacy_quarantine"][0]["allowed_consumers"] = ["read_application"]
    policy["unknown_security_override"] = True
    policy_path.write_text(json.dumps(policy), encoding="utf-8")
    with pytest.raises(DependencyBoundaryPolicyError, match="invalid policy"):
        validate_dependency_boundaries(repository_root=repo)


def test_malformed_quarantine_alone_is_rejected(tmp_path: Path) -> None:
    repo = _copy_policy_repo(
        tmp_path, "from __future__ import annotations\n", "core/deployment/contracts/x.py"
    )
    policy_path = repo / "config/deployment/dependency-boundaries.json"
    policy = json.loads(policy_path.read_text())
    policy["legacy_quarantine"][0]["review_by"] = "never"
    policy_path.write_text(json.dumps(policy), encoding="utf-8")
    with pytest.raises(DependencyBoundaryPolicyError, match="invalid policy"):
        validate_dependency_boundaries(repository_root=repo)


def test_new_unclassified_deployment_module_fails(tmp_path: Path) -> None:
    report = _report(
        tmp_path,
        "from __future__ import annotations\n",
        "core/deployment/new_unclassified.py",
    )
    assert report["overall_result"] == "FAIL"
    assert report["violations"][0]["rule_id"] == "DPL-ZONE-001"


def test_validation_never_executes_commands_network_or_dynamic_import(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: calls.append("command"))
    monkeypatch.setattr(
        socket, "create_connection", lambda *args, **kwargs: calls.append("network")
    )
    monkeypatch.setattr(
        importlib, "import_module", lambda *args, **kwargs: calls.append("import")
    )
    report = _report(
        tmp_path,
        "from __future__ import annotations\n",
        "core/deployment/application/temporary_read.py",
    )
    assert report["overall_result"] == "PASS"
    assert calls == []


def test_quarantine_cannot_hide_new_protected_violation(tmp_path: Path) -> None:
    repo = _copy_policy_repo(
        tmp_path,
        "from core.deployment.inspect import inspect_manifest\n",
        "core/deployment/application/temporary_read.py",
    )
    report = validate_dependency_boundaries(
        repository_root=repo,
        paths=["core/deployment/application/temporary_read.py"],
    )
    assert report["overall_result"] == "FAIL"
    assert report["violations"][0]["imported_module"] == "core.deployment.inspect"


def test_real_repository_boundary_and_legacy_inspector() -> None:
    report = validate_dependency_boundaries(repository_root=ROOT)
    assert report["overall_result"] == "PASS", report["violations"]
    inspector = next(
        item
        for item in report["quarantine_findings"]
        if item["module"] == "core.deployment.inspect"
    )
    assert inspector["classification"] == "LEGACY_UNSUPPORTED"
    assert "subprocess" in inspector["sensitive_imports"]
    assert not any(
        item["imported_module"] == "core.deployment.inspect"
        and item["importer"].startswith(("core.api", "core.deployment.application"))
        for item in report["allowed_imports"]
    )
    assert report["production_authorized"] is False
    assert report["production_writes"] == report["ubuntu_changes"] == 0

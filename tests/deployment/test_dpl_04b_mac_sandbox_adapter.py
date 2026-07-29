from __future__ import annotations

import ast
import json
import os
from pathlib import Path

import pytest

from core.deployment.contracts import (
    DeploymentContractValidationError,
    load_schema_registry,
    validate_contract_payload,
)
from core.deployment.executor_contracts import (
    ExecutorContractError,
    create_executor_request,
)
from core.deployment.executor_ports import NonProductionExecutorPort
from core.deployment.policy import validate_dependency_boundaries
from core.deployment.sandbox_adapter import MacSandboxAdapter, SandboxAdapterError

ROOT = Path(__file__).resolve().parents[2]
STAMP = "2026-07-29T05:00:00Z"
OPS = [
    "VERIFY_SANDBOX_TARGET",
    "PREPARE_SANDBOX",
    "COLLECT_EXECUTION_EVIDENCE",
]


def _authorization(environment: str = "staging") -> dict:
    return {
        "schema_version": "dpl/v1",
        "authorization_id": "exa-" + "1" * 32,
        "request_id": "apr-" + "2" * 32,
        "decision_id": "apd-" + "3" * 32,
        "package_digest": "sha256:" + "4" * 64,
        "plan_digest": "sha256:" + "5" * 64,
        "target_identity": "mac-mini-m4",
        "environment": environment,
        "action_scope": ["act-" + "6" * 24],
        "requester_identity": "actor-a",
        "approver_identity": "actor-b",
        "nonce": "authorization-nonce-04b",
        "issued_timestamp": "2026-07-29T04:00:00Z",
        "expiry_timestamp": "2026-07-29T06:00:00Z",
        "maximum_uses": 1,
        "execution_authorized": True,
        "production_authorized": False,
        "executor_invoked": False,
        "production_writes": 0,
        "ubuntu_changes": 0,
    }


def _adapter(root: Path | None, environment: str = "staging") -> MacSandboxAdapter:
    return MacSandboxAdapter(
        sandbox_root=root,
        authorization=_authorization(environment),
        environment=environment,
        capability_timestamp=STAMP,
        repository_root=ROOT,
    )


def _request(adapter: MacSandboxAdapter, operations=OPS, **overrides) -> dict:
    values = {
        "authorization": _authorization(adapter.capability()["environment"]),
        "capability": adapter.capability(),
        "operation_scope": operations,
        "actor_identity": "actor-a",
        "nonce_reference": "sandbox-nonce-reference",
        "request_timestamp": STAMP,
    }
    values.update(overrides)
    return create_executor_request(**values)


def test_adapter_implements_port_and_requires_explicit_root(tmp_path: Path) -> None:
    adapter: NonProductionExecutorPort = _adapter(tmp_path)
    assert callable(adapter.execute)
    missing = _adapter(None)
    result = missing.execute(_request(missing), result_timestamp=STAMP)
    assert result["status"] == "DENIED"
    assert result["reason_codes"] == ["SANDBOX_ROOT_DENIED"]
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("environment", ["development", "test", "staging"])
def test_nonproduction_environments_and_mac_owner(
    tmp_path: Path, environment: str
) -> None:
    adapter = _adapter(tmp_path, environment)
    assert adapter.capability()["target_owner"] == "mac-control-plane"
    assert adapter.execute(
        _request(adapter, ["VERIFY_SANDBOX_TARGET"]), result_timestamp=STAMP
    )["status"] == "ALLOWED"


@pytest.mark.parametrize(
    "environment",
    ["production", "prod", "live", "customer-production", "sandbox", "unknown"],
)
def test_production_variants_denied(tmp_path: Path, environment: str) -> None:
    with pytest.raises(DeploymentContractValidationError):
        _adapter(tmp_path, environment)


def test_safe_canonical_atomic_deterministic_idempotent_materialization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    adapter = _adapter(tmp_path)
    request = _request(adapter)
    replacements: list[tuple[Path, Path]] = []
    original_replace = Path.replace

    def track_replace(source: Path, target: Path):
        replacements.append((source, target))
        return original_replace(source, target)

    monkeypatch.setattr(Path, "replace", track_replace)
    before_env = dict(os.environ)
    first = adapter.execute(request, result_timestamp=STAMP)
    second = adapter.execute(request, result_timestamp=STAMP)
    artifact_dir = tmp_path / "artifacts" / request["request_id"]
    manifest_path = artifact_dir / "manifest.json"
    evidence_path = artifact_dir / "evidence.json"
    assert first == second
    assert first["status"] == "ALLOWED"
    assert first["adapter_type"] == first["executor_type"] == "mac-sandbox"
    assert first["evidence_digests"] == sorted(first["evidence_digests"])
    assert len(first["evidence_digests"]) == 2
    assert json.loads(manifest_path.read_text("utf-8"))["request_id"] == request["request_id"]
    assert evidence_path.is_file()
    assert len(replacements) == 2
    assert all(source.parent == target.parent for source, target in replacements)
    assert dict(os.environ) == before_env
    assert not any(path.stat().st_mode & 0o111 for path in artifact_dir.iterdir())
    assert set(path.name for path in artifact_dir.iterdir()) == {
        "manifest.json", "evidence.json"
    }
    validate_contract_payload(
        registry=load_schema_registry(), contract_name="ExecutorResult", payload=first
    )


def test_conflicting_immutable_content_is_denied(tmp_path: Path) -> None:
    adapter = _adapter(tmp_path)
    request = _request(adapter, ["PREPARE_SANDBOX"])
    assert adapter.execute(request, result_timestamp=STAMP)["status"] == "ALLOWED"
    manifest = tmp_path / "artifacts" / request["request_id"] / "manifest.json"
    manifest.write_text("conflict", encoding="utf-8")
    result = adapter.execute(request, result_timestamp=STAMP)
    assert result["status"] == "DENIED"
    assert manifest.read_text("utf-8") == "conflict"


def test_symlink_root_component_repository_and_protected_roots_denied(
    tmp_path: Path,
) -> None:
    real = tmp_path / "real"
    real.mkdir()
    linked = tmp_path / "linked"
    linked.symlink_to(real, target_is_directory=True)
    for root, repository in ((linked, ROOT), (ROOT, ROOT), (Path("/etc"), None)):
        adapter = MacSandboxAdapter(
            sandbox_root=root,
            authorization=_authorization(),
            environment="staging",
            capability_timestamp=STAMP,
            repository_root=repository,
        )
        assert adapter.execute(_request(adapter), result_timestamp=STAMP)["status"] == "DENIED"


def test_symlink_child_component_is_denied(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "artifacts").symlink_to(outside, target_is_directory=True)
    adapter = _adapter(tmp_path)
    assert adapter.execute(_request(adapter), result_timestamp=STAMP)["status"] == "DENIED"
    assert not list(outside.iterdir())


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("shell", "unsafe"),
        ("command", "unsafe"),
        ("argv", ["unsafe"]),
        ("script", "unsafe"),
        ("api_secret", "redacted"),
    ],
)
def test_secret_and_executable_fields_rejected(
    tmp_path: Path, field: str, value
) -> None:
    adapter = _adapter(tmp_path)
    request = _request(adapter)
    request[field] = value
    with pytest.raises(SandboxAdapterError):
        adapter.execute(request, result_timestamp=STAMP)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("value", ["/absolute/child", "../parent"])
def test_absolute_and_parent_traversal_rejected(tmp_path: Path, value: str) -> None:
    adapter = _adapter(tmp_path)
    with pytest.raises(ExecutorContractError):
        _request(adapter, actor_identity=value)


def test_authorization_actor_digest_target_and_scope_binding(tmp_path: Path) -> None:
    adapter = _adapter(tmp_path)
    for field, value in (
        ("execution_authorization_id", "exa-" + "0" * 32),
        ("package_digest", "sha256:" + "0" * 64),
        ("plan_digest", "sha256:" + "0" * 64),
        ("target_identity", "other-mac"),
        ("actor_identity", "actor-c"),
    ):
        request = _request(adapter)
        request[field] = value
        result = adapter.execute(request, result_timestamp=STAMP)
        assert result["status"] == "DENIED"
    unsupported = _request(adapter)
    unsupported["operation_scope"] = ["SIMULATE_EXECUTION"]
    result = adapter.execute(unsupported, result_timestamp=STAMP)
    assert result["status"] == "DENIED"


def test_no_forbidden_imports_and_dependency_policy_pass() -> None:
    forbidden = {
        "subprocess", "socket", "requests", "paramiko", "core.api", "core.worker"
    }
    for source in (ROOT / "core/deployment/sandbox_adapter").glob("*.py"):
        tree = ast.parse(source.read_text("utf-8"))
        imports = {
            node.names[0].name if isinstance(node, ast.Import) else (node.module or "")
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
        }
        assert not any(
            item == prefix or item.startswith(prefix + ".")
            for item in imports for prefix in forbidden
        )
        assert "unlink(" not in source.read_text("utf-8")
    report = validate_dependency_boundaries(repository_root=ROOT)
    assert report["overall_result"] == "PASS", report["violations"]
    assert report["production_authorized"] is False

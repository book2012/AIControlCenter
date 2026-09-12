from dataclasses import replace
from importlib import import_module
import json
from pathlib import Path

import pytest

from core.deployment.production_runtime_activation.artifact_verifier import (
    FilesystemProductionRuntimeActivationArtifactVerifier,
)
from core.runtime.metadata_generator import RuntimeMetadataGenerator
from tests.deployment.conftest import snapshot_state
from core.deployment.production_runtime_activation.authorization import (
    ProductionRuntimeActivationAuthorizationPermit,
    request_digest,
)
from core.deployment.production_runtime_activation.claim import (
    ProductionRuntimeActivationClaimRegistry,
    ProductionRuntimeActivationExecutionLaneRegistry,
)
from core.deployment.production_runtime_activation.coordinator import (
    ProductionRuntimeActivationCoordinator,
)
from core.deployment.production_runtime_activation.models import (
    ProductionRuntimeActivationError,
    ProductionRuntimeActivationRequest,
)
from core.deployment.production_runtime_activation.plan import (
    ProductionRuntimeActivationPlan,
    activation_plan_digest,
)


SOURCE_DIGEST = (
    "sha256:"
    "a2b40bf8efb889e2a1e4b0185b175859716809be9bcbe45d73b4bfb991fe0792"
)


def activation_plan() -> ProductionRuntimeActivationPlan:
    return ProductionRuntimeActivationPlan(
        candidate_runtime_id="28869898a28f",
        candidate_source_commit=(
            "28869898a28fbc0f0d0fd6c995104defa645ada3"
        ),
        source_artifact_content_digest=SOURCE_DIGEST,
        governance_commit="a" * 40,
        expected_current_runtime_id="d8f9f550093d",
        canonical_service_label="com.aicontrolcenter.api",
        canonical_runtime_target="ops.macos.runtime.application:app",
    )


def activation_request(
    plan: ProductionRuntimeActivationPlan,
) -> ProductionRuntimeActivationRequest:
    return ProductionRuntimeActivationRequest(
        request_id="activation-01c-artifact-verifier-test",
        candidate_runtime_id=plan.candidate_runtime_id,
        candidate_source_commit=plan.candidate_source_commit,
        governance_commit=plan.governance_commit,
        expected_current_runtime_id=plan.expected_current_runtime_id,
        canonical_service_label=plan.canonical_service_label,
        canonical_runtime_target=plan.canonical_runtime_target,
        human_authorization_id="production-human-authorization-test",
        human_authorization_digest="sha256:" + ("1" * 64),
        plan_digest=activation_plan_digest(plan),
    )


def activation_permit(
    request: ProductionRuntimeActivationRequest,
) -> ProductionRuntimeActivationAuthorizationPermit:
    return ProductionRuntimeActivationAuthorizationPermit(
        authorization_id="activation-01c-human-authorization",
        activation_request_digest=request_digest(request),
        candidate_runtime_id=request.candidate_runtime_id,
        candidate_source_commit=request.candidate_source_commit,
        governance_commit=request.governance_commit,
        expected_current_runtime_id=request.expected_current_runtime_id,
        plan_digest=request.plan_digest,
        operator_identity="mac-operator-01",
        independent_approver_identity="production-approver-01",
        authorized_at="2026-09-11T10:00:00+09:00",
        not_before="2026-09-11T10:00:00+09:00",
        expires_at="2026-09-11T10:10:00+09:00",
    )


class RecordingPrimitive:
    def __init__(self) -> None:
        self.calls = []

    def activate(
        self,
        request: ProductionRuntimeActivationRequest,
    ) -> None:
        self.calls.append(request)


class RejectingArtifactVerifier:
    def __init__(self) -> None:
        self.calls = []

    def verify(
        self,
        plan: ProductionRuntimeActivationPlan,
    ) -> None:
        self.calls.append(plan)
        raise ProductionRuntimeActivationError(
            "SOURCE_ARTIFACT_CONTENT_DIGEST_MISMATCH"
        )


def test_artifact_digest_mismatch_prevents_claim_and_primitive(
    tmp_path: Path,
) -> None:
    plan = activation_plan()
    request = activation_request(plan)
    permit = activation_permit(request)

    claim_root = tmp_path / "claims"
    claim_root.mkdir(mode=0o700)

    lane_root = tmp_path / "activation-lane"
    lane_root.mkdir(mode=0o700)

    primitive = RecordingPrimitive()
    verifier = RejectingArtifactVerifier()
    lane = ProductionRuntimeActivationExecutionLaneRegistry(lane_root)

    coordinator = ProductionRuntimeActivationCoordinator(
        claim_registry=ProductionRuntimeActivationClaimRegistry(
            claim_root
        ),
        execution_lane=lane,
        artifact_verifier=verifier,
        primitive=primitive,
    )

    with pytest.raises(
        ProductionRuntimeActivationError,
        match="SOURCE_ARTIFACT_CONTENT_DIGEST_MISMATCH",
    ):
        coordinator.execute(
            request=request,
            plan=plan,
            permit=permit,
            validated_at="2026-09-11T10:05:00+09:00",
            operator_identity="mac-operator-01",
        )

    assert verifier.calls == [plan]
    assert list(claim_root.iterdir()) == []
    assert list(lane_root.iterdir()) == [
        lane_root / "production-runtime-activation.lock"
    ]
    assert primitive.calls == []
    with lane.acquire():
        pass  # Verification failure releases the reusable lane.


# Use the producer's existing content contract; never synthesize another digest.
source_contract = import_module("ops.macos.runtime.runtime-source-artifact")


@pytest.fixture
def candidate(tmp_path):
    root = tmp_path / "runtime"
    plan = activation_plan()
    runtime = root / "venvs" / plan.candidate_runtime_id
    RuntimeMetadataGenerator(
        runtime_dir=runtime,
        commit=plan.candidate_source_commit,
        short_commit=plan.candidate_runtime_id,
        created_at="2026-09-11T01:00:00Z",
    ).write()
    source = root / "sources" / plan.candidate_runtime_id
    source.mkdir(parents=True)
    (source / source_contract.MARKER_NAME).write_bytes(
        (plan.candidate_source_commit + "\n").encode("ascii")
    )
    for name in (
        "core/api/shadow.py", "core/runtime/data_paths.py", "config/workers.yaml",
        "ops/macos/runtime/application.py",
    ):
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# fixture\n", encoding="utf-8")
    digest = source_contract.content_digest(source)
    (source / source_contract.MANIFEST_NAME).write_text(json.dumps({
        "schema_version": 1,
        "runtime_id": plan.candidate_runtime_id,
        "source_commit": plan.candidate_source_commit,
        "git_tree": "b" * 40,
        "archive_sha256": "c" * 64,
        "content_sha256": digest,
        "artifact_root": str(source),
        "build_status": "COMPLETE",
        "production_authorized": False,
    }), encoding="utf-8")
    source_contract.make_read_only(source)
    plan = replace(plan, source_artifact_content_digest="sha256:" + digest)
    yield root, runtime, source, plan
    # Restore only this fixture's source permissions for pytest cleanup.
    source_contract.make_writable_for_cleanup(root / "sources")


def rewrite(path, content):
    path.chmod(0o600)
    path.write_bytes(content)
    path.chmod(0o444)


def assert_rejected_before_mutation(root, plan, code, tmp_path):
    claim_root = tmp_path / "claims"
    lane_root = tmp_path / "lane"
    claim_root.mkdir(mode=0o700)
    lane_root.mkdir(mode=0o700)
    lane = ProductionRuntimeActivationExecutionLaneRegistry(lane_root)
    # Initialize the reusable lock before snapshotting all fixture state.
    with lane.acquire():
        pass
    primitive = RecordingPrimitive()
    coordinator = ProductionRuntimeActivationCoordinator(
        claim_registry=ProductionRuntimeActivationClaimRegistry(claim_root),
        execution_lane=lane,
        artifact_verifier=FilesystemProductionRuntimeActivationArtifactVerifier(root),
        primitive=primitive,
    )
    request = activation_request(plan)
    before = snapshot_state(tmp_path)
    with pytest.raises(ProductionRuntimeActivationError, match=code):
        coordinator.execute(
            request=request, plan=plan, permit=activation_permit(request),
            validated_at="2026-09-11T10:05:00+09:00",
            operator_identity="mac-operator-01",
        )
    assert snapshot_state(tmp_path) == before
    assert list(claim_root.iterdir()) == []
    assert list(lane_root.iterdir()) == [
        lane_root / "production-runtime-activation.lock"
    ]
    assert primitive.calls == []
    with lane.acquire():
        pass  # Every verification failure must release the lane.


def test_concrete_verifier_accepts_bootstrap_identity_read_only(candidate):
    root, _, _, plan = candidate
    before = snapshot_state(root)
    assert FilesystemProductionRuntimeActivationArtifactVerifier(root).verify(plan) is None
    assert snapshot_state(root) == before


@pytest.mark.parametrize("target", ["runtime", "source"])
def test_concrete_verifier_rejects_missing_candidate(candidate, tmp_path, target):
    root, runtime, source, plan = candidate
    path = runtime if target == "runtime" else source
    path.rename(path.with_name("unselected"))
    assert_rejected_before_mutation(root, plan, "CANDIDATE_.*_PATH_INVALID", tmp_path)


@pytest.mark.parametrize("target", ["root", "venvs", "sources", "runtime", "source"])
def test_concrete_verifier_rejects_symlink_paths(candidate, tmp_path, target):
    root, runtime, source, plan = candidate
    path = {"root": root, "venvs": runtime.parent, "sources": source.parent,
            "runtime": runtime, "source": source}[target]
    outside = tmp_path / "outside"
    path.chmod(0o700)
    path.rename(outside)
    path.symlink_to(outside, target_is_directory=True)
    try:
        assert_rejected_before_mutation(root, plan, "CANDIDATE_.*_PATH_INVALID", tmp_path)
    finally:
        path.unlink()
        outside.rename(path)


@pytest.mark.parametrize("kind", ["relative", "traversal", "file", "missing"])
def test_concrete_verifier_rejects_invalid_runtime_root(candidate, tmp_path, kind):
    root, _, _, plan = candidate
    if kind == "relative":
        root = Path("runtime")
    elif kind == "traversal":
        root = root / ".." / "runtime"
    elif kind == "file":
        root = tmp_path / "file"
        root.write_text("fixture")
    else:
        root = tmp_path / "missing"
    assert_rejected_before_mutation(root, plan, "CANDIDATE_.*_PATH_INVALID", tmp_path)


@pytest.mark.parametrize("target", ["runtime", "source"])
@pytest.mark.parametrize("marker", [None, b"", b"a" * 40, b"a" * 40 + b"\r\n",
                                    b"a" * 40 + b"\n\n", b"A" * 40 + b"\n",
                                    b"g" * 40 + b"\n", b"\xff\n", b"a" * 39 + b"\n"])
def test_concrete_verifier_rejects_missing_or_malformed_marker(
    candidate, tmp_path, target, marker,
):
    root, runtime, source, plan = candidate
    directory = runtime if target == "runtime" else source
    path = directory / source_contract.MARKER_NAME
    if marker is None:
        directory.chmod(0o700)
        path.unlink()
        directory.chmod(0o555)
    else:
        rewrite(path, marker)
    assert_rejected_before_mutation(root, plan, "CANDIDATE_SOURCE_MARKER_", tmp_path)


@pytest.mark.parametrize("target", ["runtime", "source"])
def test_concrete_verifier_rejects_commit_mismatch(candidate, tmp_path, target):
    root, runtime, source, plan = candidate
    directory = runtime if target == "runtime" else source
    # Keep the same short ID to prove comparison covers all 40 characters.
    mismatch = plan.candidate_runtime_id + "f" * 28
    rewrite(directory / source_contract.MARKER_NAME, (mismatch + "\n").encode())
    assert_rejected_before_mutation(root, plan, "CANDIDATE_SOURCE_COMMIT_MISMATCH", tmp_path)


@pytest.mark.parametrize("name", ["metadata.json", "runtime-marker", "source-marker",
                                  "manifest", "core/api/shadow.py"])
def test_concrete_verifier_rejects_symlink_escape_before_read(
    candidate, tmp_path, name,
):
    root, runtime, source, plan = candidate
    paths = {
        "metadata.json": runtime / "metadata.json",
        "runtime-marker": runtime / source_contract.MARKER_NAME,
        "source-marker": source / source_contract.MARKER_NAME,
        "manifest": source / source_contract.MANIFEST_NAME,
    }
    path = paths.get(name, source / name)
    outside = tmp_path / "outside"
    outside.write_bytes(path.read_bytes())
    path.parent.chmod(0o700)
    path.unlink()
    path.symlink_to(outside)
    path.parent.chmod(0o555)
    assert_rejected_before_mutation(root, plan, "CANDIDATE_.*INVALID", tmp_path)


@pytest.mark.parametrize("failure", ["missing", "invalid_json", "non_utf8", "shape",
                                     "schema", "commit", "short_commit", "runtime_mode"])
def test_concrete_verifier_rejects_invalid_metadata(candidate, tmp_path, failure):
    root, runtime, _, plan = candidate
    path = runtime / "metadata.json"
    data = json.loads(path.read_text())
    if failure == "missing":
        path.unlink()
    elif failure in {"invalid_json", "non_utf8", "shape"}:
        rewrite(path, {"invalid_json": b"{", "non_utf8": b"\xff", "shape": b"[]"}[failure])
    else:
        if failure == "schema":
            data["schema_version"] = 2
        elif failure == "commit":
            data["commit"] = plan.candidate_runtime_id + "f" * 28
        elif failure == "short_commit":
            data["short_commit"] = "f" * 12
        else:
            data["runtime_mode"] = []
        rewrite(path, json.dumps(data).encode())
    assert_rejected_before_mutation(root, plan, "CANDIDATE_RUNTIME_METADATA_", tmp_path)


@pytest.mark.parametrize("failure", ["missing_manifest", "invalid_manifest", "manifest_shape",
                                     "content", "rewritten_manifest", "plan_digest", "writable"])
def test_concrete_verifier_rejects_source_artifact_mismatch(candidate, tmp_path, failure):
    root, _, source, plan = candidate
    manifest = source / source_contract.MANIFEST_NAME
    if failure == "missing_manifest":
        source.chmod(0o700)
        manifest.unlink()
        source.chmod(0o555)
    elif failure in {"invalid_manifest", "manifest_shape"}:
        rewrite(manifest, b"{" if failure == "invalid_manifest" else b"null")
    elif failure in {"content", "rewritten_manifest"}:
        rewrite(source / "core/api/shadow.py", b"# tampered\n")
        if failure == "rewritten_manifest":
            data = json.loads(manifest.read_text())
            data["content_sha256"] = source_contract.content_digest(source)
            rewrite(manifest, json.dumps(data).encode())
    elif failure == "plan_digest":
        plan = replace(plan, source_artifact_content_digest="sha256:" + "0" * 64)
    else:
        (source / "core/api/shadow.py").chmod(0o644)
    code = ("SOURCE_ARTIFACT_CONTENT_DIGEST_MISMATCH"
            if failure in {"rewritten_manifest", "plan_digest"}
            else "CANDIDATE_SOURCE_ARTIFACT_INVALID")
    assert_rejected_before_mutation(root, plan, code, tmp_path)


@pytest.mark.parametrize("primitive_fails", [False, True])
def test_concrete_verifier_coordinator_claims_once_and_never_replays(
    candidate, tmp_path, primitive_fails,
):
    root, _, _, plan = candidate
    claim_root = tmp_path / "claims"
    lane_root = tmp_path / "lane"
    claim_root.mkdir(mode=0o700)
    lane_root.mkdir(mode=0o700)
    lane = ProductionRuntimeActivationExecutionLaneRegistry(lane_root)

    class CheckedPrimitive(RecordingPrimitive):
        def activate(self, request):
            assert len(list(claim_root.glob("*.claim.json"))) == 1
            with pytest.raises(ProductionRuntimeActivationError, match="ACTIVATION_EXECUTION_LANE_BUSY"):
                with lane.acquire():
                    pytest.fail("Execution lane was not held during mutation")
            super().activate(request)
            if primitive_fails:
                raise RuntimeError("synthetic primitive failure")

    primitive = CheckedPrimitive()
    coordinator = ProductionRuntimeActivationCoordinator(
        claim_registry=ProductionRuntimeActivationClaimRegistry(claim_root),
        execution_lane=lane,
        artifact_verifier=FilesystemProductionRuntimeActivationArtifactVerifier(root),
        primitive=primitive,
    )
    request = activation_request(plan)
    arguments = dict(
        request=request, plan=plan, permit=activation_permit(request),
        validated_at="2026-09-11T10:05:00+09:00",
        operator_identity="mac-operator-01",
    )
    before = snapshot_state(root)
    if primitive_fails:
        with pytest.raises(RuntimeError, match="synthetic primitive failure"):
            coordinator.execute(**arguments)
    else:
        receipt = coordinator.execute(**arguments)
        assert receipt.primitive_invocations == 1
        assert receipt.claim_receipt.claim_path.exists()
    with pytest.raises(ProductionRuntimeActivationError, match="ACTIVATION_ALREADY_CLAIMED"):
        coordinator.execute(**arguments)
    assert primitive.calls == [request]
    assert len(list(claim_root.glob("*.claim.json"))) == 1
    assert snapshot_state(root) == before
    with lane.acquire():
        pass  # The reusable lane is released even when the primitive fails.

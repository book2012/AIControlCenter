from __future__ import annotations

import ast
import inspect
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from core.governance.control_plane.domain import (
    ExecutionStatus,
    GovernanceExecutionRequest,
)
from core.governance.control_plane.ports.execution import ControlledExecutionPort
from ops.macos.shopping.secret_provisioning_adapters import (
    AGE_INSTALL_ENSURE,
    CONTROL_PLANE_IDENTITY_CREATE,
    CONTROL_PLANE_RECIPIENT_REGISTER_VALIDATE,
    OFFLINE_RECOVERY_RECIPIENT_REGISTER_VALIDATE,
    SHOPPING_SECRET_PROVISIONING,
    SOPS_INSTALL_ENSURE,
    AdapterRequestRejected,
    AgeInstallEnsureAdapter,
    ControlPlaneIdentityCreateAdapter,
    ControlPlaneRecipientRegisterValidateAdapter,
    MutationOutcome,
    OfflineRecoveryRecipientRegisterValidateAdapter,
    SopsInstallEnsureAdapter,
)

ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = ROOT / "ops/macos/shopping/secret_provisioning_adapters.py"
DEFINITION_PATH = ROOT / "config/shopping-secret-provisioning.json"
PAYLOAD_PATH = ROOT / "deploy/shopping/secrets/shopping.enc.yaml"
ACTIONS = (
    SOPS_INSTALL_ENSURE,
    AGE_INSTALL_ENSURE,
    CONTROL_PLANE_IDENTITY_CREATE,
    CONTROL_PLANE_RECIPIENT_REGISTER_VALIDATE,
    OFFLINE_RECOVERY_RECIPIENT_REGISTER_VALIDATE,
)


class FakeCapability:
    def __init__(self, outcome: MutationOutcome, *, raises: bool = False) -> None:
        self.outcome = outcome
        self.raises = raises
        self.invocation_count = 0

    def _call(self) -> MutationOutcome:
        self.invocation_count += 1
        if self.raises:
            raise RuntimeError("sensitive primitive diagnostic")
        return self.outcome


class FakeEnsureSopsTool(FakeCapability):
    ensure_sops_tool = FakeCapability._call


class FakeEnsureAgeTooling(FakeCapability):
    ensure_age_tooling = FakeCapability._call


class FakeCreateControlPlaneAgeIdentity(FakeCapability):
    create_control_plane_age_identity = FakeCapability._call


class FakeRegisterControlPlaneRecipientMetadata(FakeCapability):
    register_control_plane_recipient_metadata = FakeCapability._call


class FakeRegisterOfflineRecoveryPublicMetadata(FakeCapability):
    register_offline_recovery_public_metadata = FakeCapability._call


CASES = (
    (SOPS_INSTALL_ENSURE, SopsInstallEnsureAdapter, FakeEnsureSopsTool),
    (AGE_INSTALL_ENSURE, AgeInstallEnsureAdapter, FakeEnsureAgeTooling),
    (CONTROL_PLANE_IDENTITY_CREATE, ControlPlaneIdentityCreateAdapter, FakeCreateControlPlaneAgeIdentity),
    (CONTROL_PLANE_RECIPIENT_REGISTER_VALIDATE, ControlPlaneRecipientRegisterValidateAdapter, FakeRegisterControlPlaneRecipientMetadata),
    (OFFLINE_RECOVERY_RECIPIENT_REGISTER_VALIDATE, OfflineRecoveryRecipientRegisterValidateAdapter, FakeRegisterOfflineRecoveryPublicMetadata),
)


def request(
    action: str,
    *,
    target: str = SHOPPING_SECRET_PROVISIONING,
    execution_request_id: str = "execution-request-001",
) -> GovernanceExecutionRequest:
    return GovernanceExecutionRequest(
        schema_version="governance/v1",
        execution_request_id=execution_request_id,
        lifecycle_id="lifecycle-001",
        authorization_id="authorization-001",
        claim_id="claim-001",
        mutation_budget_id="budget-001",
        action_type=action,
        target=target,
        plan_digest="plan-digest-001",
        requested_at=datetime(2026, 8, 17, tzinfo=timezone.utc),
    )


def test_action_constants_and_adapter_actions_match_canonical_definition() -> None:
    definition = json.loads(DEFINITION_PATH.read_text(encoding="utf-8"))
    canonical_actions = tuple(item["action_id"] for item in definition["actions"])
    assert ACTIONS == canonical_actions
    assert tuple(adapter_type.ACTION for _, adapter_type, _ in CASES) == canonical_actions


@pytest.mark.parametrize(("action", "adapter_type", "fake_type"), CASES)
@pytest.mark.parametrize("outcome", tuple(MutationOutcome))
def test_each_exact_action_crosses_its_narrow_fake_once(action, adapter_type, fake_type, outcome) -> None:
    fake = fake_type(outcome)
    adapter: ControlledExecutionPort = adapter_type(fake)
    receipt = adapter.invoke_once(request(action))
    assert fake.invocation_count == 1
    assert receipt.action_type == action
    assert receipt.status is ExecutionStatus(outcome.value)
    assert receipt.actual_invocation_count == 1
    assert receipt.completed_count == int(outcome is MutationOutcome.COMPLETED)
    assert receipt.uncertain_count == int(outcome is MutationOutcome.UNCERTAIN)


@pytest.mark.parametrize(("action", "adapter_type", "fake_type"), CASES)
def test_every_wrong_action_is_rejected_before_invocation(action, adapter_type, fake_type) -> None:
    for wrong_action in ACTIONS:
        if wrong_action == action:
            continue
        fake = fake_type(MutationOutcome.COMPLETED)
        with pytest.raises(AdapterRequestRejected, match="^ACTION_NOT_SUPPORTED$"):
            adapter_type(fake).invoke_once(request(wrong_action))
        assert fake.invocation_count == 0


@pytest.mark.parametrize(("action", "adapter_type", "fake_type"), CASES)
def test_every_inexact_target_is_rejected_before_invocation(action, adapter_type, fake_type) -> None:
    wrong_targets = (
        "WRONG_TARGET",
        f"PREFIX:{SHOPPING_SECRET_PROVISIONING}",
        f"{SHOPPING_SECRET_PROVISIONING}:SUFFIX",
        "SECRET_PROVISIONING",
    )
    for wrong_target in wrong_targets:
        fake = fake_type(MutationOutcome.COMPLETED)
        with pytest.raises(AdapterRequestRejected, match="^TARGET_NOT_SUPPORTED$"):
            adapter_type(fake).invoke_once(request(action, target=wrong_target))
        assert fake.invocation_count == 0


@pytest.mark.parametrize(("action", "adapter_type", "fake_type"), CASES)
def test_bad_request_shape_is_rejected_before_invocation(action, adapter_type, fake_type) -> None:
    fake = fake_type(MutationOutcome.COMPLETED)
    with pytest.raises(AdapterRequestRejected, match="^INVALID_EXECUTION_REQUEST$"):
        adapter_type(fake).invoke_once(object())
    assert fake.invocation_count == 0


@pytest.mark.parametrize(("action", "adapter_type", "fake_type"), CASES)
def test_suffix_and_substring_actions_are_rejected_without_invocation(action, adapter_type, fake_type) -> None:
    for wrong_action in (f"PREFIX:{action}", f"{action}:SUFFIX"):
        fake = fake_type(MutationOutcome.COMPLETED)
        with pytest.raises(AdapterRequestRejected, match="^ACTION_NOT_SUPPORTED$"):
            adapter_type(fake).invoke_once(request(wrong_action))
        assert fake.invocation_count == 0


@pytest.mark.parametrize(("action", "adapter_type", "fake_type"), CASES)
def test_primitive_exception_is_one_uncertain_value_free_invocation(action, adapter_type, fake_type) -> None:
    fake = fake_type(MutationOutcome.COMPLETED, raises=True)
    receipt = adapter_type(fake).invoke_once(request(action))
    assert fake.invocation_count == 1
    assert receipt.status is ExecutionStatus.UNCERTAIN
    assert receipt.actual_invocation_count == 1
    assert receipt.uncertain_count == 1
    assert "sensitive" not in json.dumps(receipt.to_dict()).lower()


@pytest.mark.parametrize(("action", "adapter_type", "fake_type"), CASES)
def test_invalid_capability_outcome_is_one_uncertain_value_free_invocation(
    action, adapter_type, fake_type
) -> None:
    invalid_value = "raw-sensitive-invalid-capability-value"
    fake = fake_type(invalid_value)
    receipt = adapter_type(fake).invoke_once(request(action))
    rendered = json.dumps(receipt.to_dict()).lower()
    assert fake.invocation_count == 1
    assert receipt.status is ExecutionStatus.UNCERTAIN
    assert receipt.actual_invocation_count == 1
    assert receipt.completed_count == 0
    assert receipt.uncertain_count == 1
    assert invalid_value not in rendered


def test_receipt_identity_is_deterministic_injective_and_namespaced() -> None:
    action, adapter_type, fake_type = CASES[0]
    first = adapter_type(fake_type(MutationOutcome.COMPLETED)).invoke_once(
        request(action, execution_request_id="execution-request-001")
    )
    same = adapter_type(fake_type(MutationOutcome.COMPLETED)).invoke_once(
        request(action, execution_request_id="execution-request-001")
    )
    distinct = adapter_type(fake_type(MutationOutcome.COMPLETED)).invoke_once(
        request(action, execution_request_id="execution-request-002")
    )
    former_collision = adapter_type(fake_type(MutationOutcome.COMPLETED)).invoke_once(
        request(action, execution_request_id="execution-receipt-001")
    )
    assert first.receipt_id == same.receipt_id
    assert first.receipt_id == "execution-receipt:execution-request-001"
    assert distinct.receipt_id == "execution-receipt:execution-request-002"
    assert former_collision.receipt_id == "execution-receipt:execution-receipt-001"
    assert len({first.receipt_id, distinct.receipt_id, former_collision.receipt_id}) == 3
    assert all(
        receipt.receipt_id.startswith("execution-receipt:")
        for receipt in (first, same, distinct, former_collision)
    )


def test_primitive_result_values_never_influence_receipt_identity() -> None:
    action, adapter_type, fake_type = CASES[0]
    receipts = (
        adapter_type(fake_type(outcome)).invoke_once(
            request(action, execution_request_id="arbitrary-request-id")
        )
        for outcome in (*tuple(MutationOutcome), "raw-sensitive-invalid-capability-value")
    )
    assert {receipt.receipt_id for receipt in receipts} == {
        "execution-receipt:arbitrary-request-id"
    }


def test_receipts_and_errors_are_value_free() -> None:
    forbidden = (
        "AGE-SECRET-KEY", "public-recipient", "fingerprint", "stdout", "stderr",
        "HOMEBREW", "/Users/", "environment-value",
    )
    for action, adapter_type, fake_type in CASES:
        fake = fake_type(MutationOutcome.FAILED)
        rendered = json.dumps(adapter_type(fake).invoke_once(request(action)).to_dict())
        assert not [value for value in forbidden if value.lower() in rendered.lower()]
    error = AdapterRequestRejected("ACTION_NOT_SUPPORTED")
    assert str(error) == "ACTION_NOT_SUPPORTED"


def test_adapters_expose_no_authority_recovery_or_generic_execution_api() -> None:
    source = ADAPTER_PATH.read_text(encoding="utf-8").lower()
    prohibited = (
        "subprocess", "argv", "shell", "environ", "getenv", "stdout", "stderr",
        "homebrew", "age-keygen", "authorize", "consume_authorization", "retry",
        "rollback", "compensate", "widen_scope", "private key", "private_identity",
        "key_bytes", "decryption", "mariadb", "docker", "colima",
    )
    assert not [token for token in prohibited if token in source]
    tree = ast.parse(source)
    assert not any(isinstance(node, (ast.For, ast.While, ast.AsyncFor)) for node in ast.walk(tree))
    public_methods = {
        name for _, adapter_type, _ in CASES
        for name, _ in inspect.getmembers(adapter_type, inspect.isfunction)
        if not name.startswith("_")
    }
    assert public_methods == {"invoke_once"}


def test_offline_recovery_capability_accepts_no_private_identity_input() -> None:
    signature = inspect.signature(FakeRegisterOfflineRecoveryPublicMetadata.register_offline_recovery_public_metadata)
    assert tuple(signature.parameters) == ("self",)
    signature = inspect.signature(OfflineRecoveryRecipientRegisterValidateAdapter.__init__)
    assert tuple(signature.parameters) == ("self", "capability")


def test_dependency_direction_and_non_deployment_truth() -> None:
    imports: list[str] = []
    for path in (ROOT / "core").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
    assert not [name for name in imports if name == "ops" or name.startswith("ops.")]
    assert not [name for name in imports if name == "integrations" or name.startswith("integrations.")]
    definition = json.loads(DEFINITION_PATH.read_text(encoding="utf-8"))
    assert definition["production_status"] == "NOT_DEPLOYED"
    assert definition["materialization_implemented"] is False
    assert not PAYLOAD_PATH.exists()

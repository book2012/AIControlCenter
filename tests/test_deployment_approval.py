from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.deployment.approval import (
    build_approval_request,
    plan_hash,
    validate_approval,
)
from core.deployment.dry_run import build_ollama_dry_run


ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "config/services/designs/ollama-managed-service.json"


def future_timestamp() -> str:
    return (
        datetime.now(timezone.utc) + timedelta(hours=1)
    ).isoformat()


def test_plan_hash_is_deterministic():
    plan = build_ollama_dry_run(DESIGN)

    assert plan_hash(plan) == plan_hash(deepcopy(plan))
    assert len(plan_hash(plan)) == 64


def test_approval_request_remains_execution_disabled():
    plan = build_ollama_dry_run(DESIGN)
    approval = build_approval_request(
        plan,
        requested_by="kyouhan",
        expires_at=future_timestamp(),
    )

    assert approval["valid"] is True
    assert approval["approval_status"] == "PENDING"
    assert approval["execution_enabled"] is False
    assert approval["service_id"] == "ollama"
    assert approval["approved_by"] is None
    assert approval["rollback_required"] is True


def test_approval_contains_only_declared_write_actions():
    plan = build_ollama_dry_run(DESIGN)
    approval = build_approval_request(
        plan,
        requested_by="kyouhan",
        expires_at=future_timestamp(),
    )

    assert approval["allowed_actions"] == [
        "install-native-binary",
        "create-model-storage",
        "install-environment-contract",
        "install-launchdaemon",
        "start-service",
    ]


def test_plan_hash_mismatch_is_rejected():
    plan = build_ollama_dry_run(DESIGN)
    approval = build_approval_request(
        plan,
        requested_by="kyouhan",
        expires_at=future_timestamp(),
    )
    approval["plan_hash"] = "0" * 64

    errors = validate_approval(approval, plan)

    assert "plan hash mismatch" in errors


def test_expired_approval_is_rejected():
    plan = build_ollama_dry_run(DESIGN)
    expired = (
        datetime.now(timezone.utc) - timedelta(minutes=1)
    ).isoformat()
    approval = build_approval_request(
        plan,
        requested_by="kyouhan",
        expires_at=expired,
    )

    assert approval["valid"] is False
    assert "expires_at must be in the future" in approval["errors"]

def test_disallowed_action_is_rejected():
    plan = build_ollama_dry_run(DESIGN)
    approval = build_approval_request(
        plan,
        requested_by="kyouhan",
        expires_at=future_timestamp(),
    )
    approval["allowed_actions"].append("download-model")

    errors = validate_approval(approval, plan)

    assert any("disallowed actions" in error for error in errors)

from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.deployment.approval import build_approval_request
from core.deployment.dry_run import build_ollama_dry_run
from core.deployment.execution_gate import (
    approve_request,
    build_gate_result,
    create_execution_token,
)


ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "config/services/designs/ollama-managed-service.json"


def future_timestamp() -> str:
    return (
        datetime.now(timezone.utc) + timedelta(hours=1)
    ).isoformat()


def rollback_snapshot() -> dict:
    return {
        "read_only": True,
        "execution_enabled": False,
        "rollback": {"required": True},
    }


def approved_contract() -> tuple[dict, dict, str]:
    plan = build_ollama_dry_run(DESIGN)
    pending = build_approval_request(
        plan,
        requested_by="kyouhan",
        expires_at=future_timestamp(),
    )
    token = create_execution_token()
    approved = approve_request(
        pending,
        approved_by="kyouhan",
        execution_token=token,
    )
    return plan, approved, token


def test_approved_gate_remains_execution_disabled():
    plan, approved, token = approved_contract()
    result = build_gate_result(
        approved,
        plan,
        rollback_snapshot(),
        token,
    )

    assert result["valid"] is True
    assert result["gate_status"] == "AUTHORIZED"
    assert result["execution_enabled"] is False
    assert result["backup_required"] is True
    assert result["rollback_required"] is True


def test_pending_approval_is_blocked():
    plan = build_ollama_dry_run(DESIGN)
    pending = build_approval_request(
        plan,
        requested_by="kyouhan",
        expires_at=future_timestamp(),
    )
    token = create_execution_token()

    result = build_gate_result(
        pending,
        plan,
        rollback_snapshot(),
        token,
    )

    assert result["valid"] is False
    assert "approval status must be APPROVED" in result["errors"]


def test_wrong_execution_token_is_blocked():
    plan, approved, token = approved_contract()
    wrong_token = "0" * len(token)

    result = build_gate_result(
        approved,
        plan,
        rollback_snapshot(),
        wrong_token,
    )

    assert result["valid"] is False
    assert "execution token mismatch" in result["errors"]


def test_missing_rollback_snapshot_is_blocked():
    plan, approved, token = approved_contract()
    snapshot = {
        "read_only": True,
        "execution_enabled": False,
        "rollback": {"required": False},
    }

    result = build_gate_result(
        approved,
        plan,
        snapshot,
        token,
    )

    assert result["valid"] is False
    assert "rollback snapshot is required" in result["errors"]

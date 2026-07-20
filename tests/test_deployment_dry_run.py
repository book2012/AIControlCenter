from pathlib import Path

from core.deployment.dry_run import build_ollama_dry_run


ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "config/services/designs/ollama-managed-service.json"


def test_ollama_dry_run_is_read_only():
    result = build_ollama_dry_run(DESIGN)

    assert result["valid"] is True
    assert result["read_only"] is True
    assert result["execution_enabled"] is False
    assert result["approval_required"] is True
    assert result["service_id"] == "ollama"


def test_ollama_dry_run_contains_install_and_rollback():
    result = build_ollama_dry_run(DESIGN)

    install_actions = [
        step["action"]
        for step in result["steps"]
    ]
    rollback_actions = [
        step["action"]
        for step in result["rollback_steps"]
    ]

    assert "install-native-binary" in install_actions
    assert "install-launchdaemon" in install_actions
    assert "validate-health" in install_actions
    assert "stop-launchdaemon" in rollback_actions
    assert "restore-previous-plist" in rollback_actions
    assert "restore-previous-binary" in rollback_actions


def test_write_steps_require_approval():
    result = build_ollama_dry_run(DESIGN)

    write_steps = [
        step
        for step in result["steps"]
        if step["write"]
    ]

    assert write_steps
    assert all(
        step["approval_required"] is True
        for step in write_steps
    )


def test_model_download_is_not_enabled():
    result = build_ollama_dry_run(DESIGN)

    model_step = next(
        step
        for step in result["steps"]
        if step["action"] == "validate-model-inventory"
    )

    assert model_step["model_download_allowed"] is False


def test_missing_design_returns_structured_error(tmp_path: Path):
    result = build_ollama_dry_run(tmp_path / "missing.json")

    assert result["valid"] is False
    assert result["execution_enabled"] is False
    assert result["approval_required"] is True
    assert result["errors"]

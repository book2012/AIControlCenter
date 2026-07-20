from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "ops/macos/ollama/install-managed-ollama.sh"


def test_installer_production_paths_are_overridable():
    text = INSTALLER.read_text()

    assert "${PLIST_TARGET:-/Library/LaunchDaemons/" in text
    assert "${ENV_TARGET:-/Library/Application Support/" in text
    assert "${MODELS_TARGET:-/Users/kyouhan/Library/" in text
    assert "${LOG_TARGET:-/Users/kyouhan/Library/Logs/" in text


def test_service_and_health_are_overridable():
    text = INSTALLER.read_text()

    assert "${SERVICE:-system/com.aicontrolcenter.ollama}" in text
    assert "${HEALTH_URL:-http://127.0.0.1:11434/api/tags}" in text


def test_gate_and_backup_implementations_are_injectable():
    text = INSTALLER.read_text()

    assert "EXECUTION_GATE_MODULE=" in text
    assert "BACKUP_GENERATOR=" in text
    assert '-m "$EXECUTION_GATE_MODULE"' in text
    assert '"$PYTHON" "$BACKUP_GENERATOR"' in text

def test_binary_target_is_overridable():
    text = INSTALLER.read_text()

    assert (
        "${OLLAMA_BINARY_TARGET:-/opt/homebrew/bin/ollama}"
        in text
    )
    assert (
        '"$OLLAMA_BINARY_TARGET" || true'
        in text
    )

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESIGN_PATH = (
    ROOT / "config/services/designs/ollama-managed-service.json"
)


def load_design() -> dict:
    return json.loads(DESIGN_PATH.read_text())


def test_ollama_design_is_mac_native_and_independent():
    design = load_design()

    assert design["service_id"] == "ollama"
    assert design["status"] == "DESIGN_ONLY"
    assert design["ubuntu_dependency"] is False
    assert design["deployment"]["platform"] == "macos"
    assert design["deployment"]["runtime"] == "native-binary"
    assert design["deployment"]["supervisor"] == "system-launchdaemon"


def test_ollama_network_is_loopback_only():
    design = load_design()
    network = design["network"]

    assert network["listen_host"] == "127.0.0.1"
    assert network["port"] == 11434
    assert network["health_endpoint"] == "/api/tags"
    assert network["external_exposure_allowed"] is False


def test_ollama_storage_is_external_to_repository_and_runtime():
    design = load_design()
    storage = design["storage"]

    assert storage["repository_owned"] is False
    assert storage["immutable_runtime_owned"] is False
    assert "Application Support/Ollama/models" in storage["models_path"]


def test_ollama_environment_contract_contains_no_secrets():
    design = load_design()
    environment = design["environment"]

    assert environment["owner"] == "root"
    assert environment["group"] == "staff"
    assert environment["mode"] == "0640"
    assert environment["secret_values_allowed"] is False


def test_ollama_write_execution_remains_disabled():
    design = load_design()
    safety = design["safety"]

    assert safety["write_execution_enabled"] is False
    assert safety["human_approval_required"] is True
    assert safety["dry_run_required"] is True
    assert safety["rollback_required"] is True

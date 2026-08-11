from __future__ import annotations

import importlib.util
from pathlib import Path
import plistlib
import subprocess
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "ops/macos/runtime/run-canonical-api-immutable-source.sh"
IAC = ROOT / "ops/macos/launchd/canonical-api-launchagent.py"


def load_iac() -> ModuleType:
    spec = importlib.util.spec_from_file_location("canonical_api_launchagent", IAC)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_canonical_runtime_contract_is_isolated_from_shadow() -> None:
    source = RUNNER.read_text(encoding="utf-8")
    assert "core.api.app:app" in source
    assert "AICONTROLCENTER_CANONICAL_HOST:-127.0.0.1" in source
    assert "AICONTROLCENTER_CANONICAL_PORT:-58081" in source
    assert "core.api.shadow:app" not in source
    assert "18100" not in source


def test_data_root_is_required_and_never_initialized() -> None:
    source = RUNNER.read_text(encoding="utf-8")
    assert "$HOME_DIR/Library/Application Support/AIControlCenter" in source
    assert 'export AICONTROLCENTER_DATA_ROOT="$DATA_ROOT"' in source
    assert '[[ ! -d "$DATA_ROOT" || -L "$DATA_ROOT" ]]' in source
    forbidden = ("mkdir", "sqlite3", "migrat", "product-drafts.sqlite3", "woocommerce")
    assert all(term not in source.lower() for term in forbidden)


def test_runner_uses_validated_immutable_source_without_credentials() -> None:
    source = RUNNER.read_text(encoding="utf-8")
    assert "runtime-source-artifact.py" in source
    assert "--expected-source-commit" in source
    assert 'cd "$SOURCE_ROOT"' in source
    assert "provider-secret" not in source
    assert "AI_PROVIDER" not in source
    assert "launchctl" not in source


def test_runner_shell_syntax_is_valid() -> None:
    result = subprocess.run(["zsh", "-n", str(RUNNER)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


def test_launchagent_render_is_deterministic_and_user_relative() -> None:
    module = load_iac()
    home = Path("/Users/operator")
    first = module.render(home)
    assert first == module.render(home)
    payload = plistlib.loads(first)
    assert payload["Label"] == "com.aicontrolcenter.api"
    assert payload["EnvironmentVariables"]["AICONTROLCENTER_DATA_ROOT"] == (
        "/Users/operator/Library/Application Support/AIControlCenter/data"
    )
    assert payload["KeepAlive"] is True
    assert payload["RunAtLoad"] is True


def test_iac_plan_is_pure_and_activation_is_next_task_only() -> None:
    module = load_iac()
    plan = module.build_plan(ROOT, Path("/Users/operator"), 501)
    assert plan["write_operations_executed"] is False
    assert plan["activation_authorized"] is False
    assert plan["contract"] == {
        "label": "com.aicontrolcenter.api",
        "service": "gui/501/com.aicontrolcenter.api",
        "app": "core.api.app:app",
        "host": "127.0.0.1",
        "port": 58081,
        "data_root": "/Users/operator/Library/Application Support/AIControlCenter/data",
    }
    assert plan["activation_next_task_only"][0][0:2] == ["launchctl", "bootstrap"]

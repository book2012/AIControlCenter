from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import plistlib
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "ops/macos/launchd/canonical_api_daemon.py"


def load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("canonical_api_daemon", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_canonical_system_contract_and_plan() -> None:
    module = load_module()
    result = module.build_install_plan(ROOT)
    assert result["canonical_launchd_contract_gate_passed"] is True
    assert all(result["checks"].values())
    installation = result["installation"]
    assert installation == {
        "label": "com.aicontrolcenter.api", "service": "system/com.aicontrolcenter.api",
        "bootstrap_domain": "system", "plist": "/Library/LaunchDaemons/com.aicontrolcenter.api.plist",
        "runner": "/usr/local/libexec/aicontrolcenter/run-canonical-api-immutable-source.sh",
        "log_directory": "/var/log/aicontrolcenter",
        "stdout_log": "/var/log/aicontrolcenter/canonical-api.stdout.log",
        "stderr_log": "/var/log/aicontrolcenter/canonical-api.stderr.log",
        "application_user": "kyouhan", "application_group": "staff",
        "application": "core.api.app:app", "host": "127.0.0.1", "port": 58081,
        "data_root": "/Users/kyouhan/Library/Application Support/AIControlCenter/data",
    }
    json.dumps(result)


def test_plist_exact_runtime_environment_and_background_contract() -> None:
    module = load_module()
    with module.canonical_paths(ROOT)["plist"].open("rb") as stream:
        payload = plistlib.load(stream)
    assert payload["UserName"] == "kyouhan" and payload["GroupName"] == "staff"
    assert payload["EnvironmentVariables"] == module.EXPECTED_ENVIRONMENT
    assert payload["RunAtLoad"] is True and payload["KeepAlive"] is True
    assert payload["ProcessType"] == "Background" and payload["ThrottleInterval"] == 10


def test_plan_is_first_activation_without_forbidden_content() -> None:
    module = load_module()
    plan = module.build_install_plan(ROOT)
    text = json.dumps(plan)
    assert "run-canonical-api-immutable-source.sh" in text
    for forbidden in ("bootout", "retry", "rollback", "api.shadow", "core.api.shadow:app", "18100", "provider-secret-delivery"):
        assert forbidden not in text
    sources = [step["source"] for step in plan["installation_plan"] if step["step"] == "install_file"]
    assert sources == [str(ROOT / "ops/macos/runtime/run-canonical-api-immutable-source.sh"), str(ROOT / "ops/macos/launchd/com.aicontrolcenter.api.plist")]

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

from core.providers.credentials import EnvironmentCredentialSource
from core.providers.openai_adapter import OpenAIAdapter
from core.agent.brain_agent import BrainAgent
from core.config.settings import load_settings


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "ops/macos/launchd/provider-secret-delivery.py"
SENTINEL = "sec-01b-fake-credential"


def load_helper() -> ModuleType:
    spec = importlib.util.spec_from_file_location("provider_secret_delivery", HELPER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_secret(root: Path, value: bytes = SENTINEL.encode() + b"\n") -> Path:
    root.mkdir(mode=0o700)
    path = root / "openai-api-key"
    path.write_bytes(value)
    path.chmod(0o600)
    return path


def test_valid_mandatory_secret_and_json_are_redacted(tmp_path: Path) -> None:
    helper = load_helper()
    root = tmp_path / "secrets"
    write_secret(root)
    result = helper.validate("openai", root)
    rendered = json.dumps(helper.asdict(result))
    assert result.ready is True
    assert result.environment_variable == "OPENAI_API_KEY"
    assert result.credential_value_exposed is False
    assert SENTINEL not in rendered


@pytest.mark.parametrize("value", [b"", b" value", b"value ", b"value\n\n", b"value\r\n", b"a\nb"])
def test_empty_or_malformed_secret_fails_without_exposure(tmp_path: Path, value: bytes) -> None:
    helper = load_helper()
    root = tmp_path / "secrets"
    write_secret(root, value)
    result = helper.validate("openai", root)
    assert result.ready is False
    with pytest.raises(helper.SecretValidationError) as error:
        helper.execute("openai", ["unused"], root, {})
    assert str(error.value) == helper.FAILURE
    assert SENTINEL not in str(error.value)
    assert SENTINEL not in repr(error.value)


def test_missing_and_mode_invalid_mandatory_secret_fail(tmp_path: Path) -> None:
    helper = load_helper()
    root = tmp_path / "secrets"
    assert helper.validate("openai", root).ready is False
    path = write_secret(root)
    path.chmod(0o640)
    result = helper.validate("openai", root)
    assert result.mode_valid is False
    assert result.ready is False


def test_invalid_owner_policy_is_rejected_without_privilege(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    helper = load_helper()
    root = tmp_path / "secrets"
    write_secret(root)
    monkeypatch.setattr(helper, "EXPECTED_UID", helper.EXPECTED_UID + 1)
    assert helper.validate("openai", root).owner_valid is False


def test_optional_local_provider_needs_no_secret(tmp_path: Path) -> None:
    helper = load_helper()
    result = helper.validate("ollama", tmp_path / "absent")
    assert result.mandatory is False
    assert result.ready is True
    assert result.environment_variable is None


def test_execute_constructs_deterministic_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    helper = load_helper()
    root = tmp_path / "secrets"
    write_secret(root)
    captured: dict[str, object] = {}

    def fake_exec(file: str, argv: list[str], environment: dict[str, str]) -> None:
        captured.update(file=file, argv=argv, environment=environment)

    monkeypatch.setattr(helper.os, "execvpe", fake_exec)
    helper.execute("openai", ["runtime-python", "-m", "uvicorn"], root, {"SAFE": "1"})
    environment = captured["environment"]
    assert isinstance(environment, dict)
    assert environment == {"SAFE": "1", "OPENAI_API_KEY": SENTINEL}


def test_adapter_consumes_environment_source_without_business_logic() -> None:
    received: list[str] = []
    source = EnvironmentCredentialSource({"OPENAI_API_KEY": SENTINEL})
    adapter = OpenAIAdapter(
        credential_source=source,
        invocation_boundary=lambda request, credential: received.append(credential),
    )
    assert "redacted=True" in repr(source)
    assert SENTINEL not in repr(source)
    assert adapter._credential_lookup("OPENAI_API_KEY") == SENTINEL
    assert received == []


def test_brain_agent_does_not_retain_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", SENTINEL)
    agent = BrainAgent(settings=load_settings())
    assert agent.settings.openai.api_key is None
    assert SENTINEL not in repr(agent.settings)
    assert SENTINEL not in repr(agent.provider_router)


def test_wrapper_and_plist_secret_contracts() -> None:
    wrapper = (ROOT / "ops/macos/launchd/run-shadow-daemon.sh").read_text()
    plist = (ROOT / "ops/macos/launchd/com.aicontrolcenter.api.shadow.plist").read_text()
    assert "provider-secret-delivery.py" in wrapper
    assert " exec --provider " in wrapper
    assert SENTINEL not in wrapper
    assert "OPENAI_API_KEY" not in plist
    assert "launchctl setenv" not in wrapper
    assert "openai-api-key" not in wrapper
    assert "unset PYTHONPATH" in wrapper
    assert 'cd "$SOURCE_REAL"' in wrapper
    assert '  -P \\\n  -m uvicorn' in wrapper
    assert "/Users/kyouhan/AIControlCenter" not in wrapper
    assert "WorkingDirectory" not in plist

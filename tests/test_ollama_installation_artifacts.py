import plistlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLIST = ROOT / "ops/macos/ollama/com.aicontrolcenter.ollama.plist"
ENV = ROOT / "ops/macos/ollama/ollama.env.example"


def test_ollama_launchdaemon_contract():
    with PLIST.open("rb") as handle:
        data = plistlib.load(handle)

    assert data["Label"] == "com.aicontrolcenter.ollama"
    assert data["ProgramArguments"] == [
        "/opt/homebrew/bin/ollama",
        "serve",
    ]
    assert data["UserName"] == "kyouhan"
    assert data["GroupName"] == "staff"
    assert data["RunAtLoad"] is True
    assert data["KeepAlive"] is True
    assert data["EnvironmentVariables"]["OLLAMA_HOST"] == (
        "127.0.0.1:11434"
    )


def test_ollama_environment_contract_contains_no_secrets():
    values = {}

    for line in ENV.read_text().splitlines():
        key, value = line.split("=", 1)
        values[key] = value

    assert set(values) == {
        "OLLAMA_HOST",
        "OLLAMA_MODELS",
        "OLLAMA_KEEP_ALIVE",
    }
    assert values["OLLAMA_HOST"] == "127.0.0.1:11434"
    assert all("SECRET" not in key for key in values)
    assert all("TOKEN" not in key for key in values)

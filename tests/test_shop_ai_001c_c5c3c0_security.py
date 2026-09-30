import ast
from pathlib import Path

from core.shopping.adapters.twilio_authenticated_read_offline_transport import (
    TwilioOfflineHttpObservation,
)


RUNTIME_FILES = (
    Path(
        "core/shopping/adapters/"
        "twilio_authenticated_read_offline_transport.py"
    ),
    Path(
        "ops/macos/shopping/"
        "twilio_authenticated_read_offline_runtime.py"
    ),
)


FORBIDDEN_IMPORT_ROOTS = {
    "requests",
    "httpx",
    "socket",
    "urllib",
    "aiohttp",
    "twilio",
    "keyring",
    "subprocess",
}


def _root(path: Path) -> Path:
    return Path(__file__).resolve().parents[1] / path


def test_runtime_has_no_network_or_keychain_imports():
    for rel in RUNTIME_FILES:
        tree = ast.parse(
            _root(rel).read_text(
                encoding="utf-8"
            )
        )

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    assert (
                        root
                        not in FORBIDDEN_IMPORT_ROOTS
                    )

            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                root = module.split(".")[0]

                if root == "twilio":
                    raise AssertionError(
                        "Twilio SDK import forbidden"
                    )

                assert (
                    root
                    not in {
                        "requests",
                        "httpx",
                        "socket",
                        "urllib",
                        "aiohttp",
                        "keyring",
                        "subprocess",
                    }
                )


def test_runtime_contains_no_http_write_verbs():
    for rel in RUNTIME_FILES:
        text = _root(rel).read_text(
            encoding="utf-8"
        )
        for token in (
            '"POST"',
            '"PUT"',
            '"PATCH"',
            '"DELETE"',
            ".post(",
            ".put(",
            ".patch(",
            ".delete(",
        ):
            assert token not in text


def test_raw_observation_repr_redacts_payload():
    observation = TwilioOfflineHttpObservation(
        status_code=200,
        payload={
            "to": "sensitive-destination",
            "credential": "sensitive-value",
        },
    )

    text = repr(observation)

    assert "sensitive-destination" not in text
    assert "sensitive-value" not in text
    assert "payload=<redacted>" in text


def test_no_real_keychain_adapter_import():
    for rel in RUNTIME_FILES:
        text = _root(rel).read_text(
            encoding="utf-8"
        )
        assert "provider_secret_resolver" not in text
        assert "macos.keychain" not in text
        assert "security find-generic-password" not in text


def test_offline_transport_has_no_retry_loop():
    text = _root(RUNTIME_FILES[0]).read_text(
        encoding="utf-8"
    )
    tree = ast.parse(text)

    for node in ast.walk(tree):
        assert not isinstance(
            node,
            (ast.For, ast.While),
        )

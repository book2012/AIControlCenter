from __future__ import annotations

import ast
import json
import os
from pathlib import Path

import jsonschema
import pytest

from core.secrets.ports import SecretBackendInspectionPort
from ops.macos.shopping.sops_age_backend import (
    BackendDefinitionError,
    SopsAgeBackendAdapter,
    load_definition,
    validate_definition,
)

ROOT = Path(__file__).resolve().parents[1]
DEFINITION_PATH = ROOT / "config/shopping-secret-backend.json"
SCHEMA_PATH = ROOT / "config/schemas/shopping-secret-backend.schema.json"
ADAPTER_PATH = ROOT / "ops/macos/shopping/sops_age_backend.py"


def definition_for(tmp_path: Path) -> dict[str, object]:
    return json.loads(json.dumps(load_definition()))


def adapter_for(tmp_path: Path, definition: dict[str, object], resolver=lambda _name: "/safe/bin/tool") -> SopsAgeBackendAdapter:
    return SopsAgeBackendAdapter(
        definition, executable_resolver=resolver,
        repository_root=tmp_path / "repo", control_plane_home=tmp_path / "home",
        expected_uid=os.getuid(),
    )


def material_paths(tmp_path: Path) -> tuple[Path, Path]:
    return (
        tmp_path / "repo/deploy/shopping/secrets/shopping.enc.yaml",
        tmp_path / "home/.config/sops/age/keys.txt",
    )


def create_material(path: Path, marker: str, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(marker)
    path.chmod(mode)


def checks(report) -> dict[str, bool]:
    return dict(report.checks)


def test_canonical_definition_matches_json_schema_and_value_free_contract() -> None:
    definition = load_definition()
    jsonschema.Draft202012Validator(json.loads(SCHEMA_PATH.read_text())).validate(definition)
    raw = DEFINITION_PATH.read_text()
    assert definition["backend_kind"] == "sops-age"
    assert definition["production_status"] == "NOT_DEPLOYED"
    assert definition["materialization_implemented"] is False
    assert definition["owner"] == "MAC_MINI_M4_AICONTROLCENTER_CONTROL_PLANE"
    validate_definition(definition)
    assert definition["identity_custody"]["base"] == "control-plane-home"
    assert definition["identity_custody"]["relative_path"] == ".config/sops/age/keys.txt"
    assert "/Users/" not in raw
    assert not any(token in raw.lower() for token in ('"value"', '"default"', '"credential"', '"recipient" :'))


def test_two_recipient_policy_is_metadata_only() -> None:
    policy = load_definition()["recipient_policy"]
    assert policy == {
        "minimum_recipients": 2,
        "roles": ["control-plane", "offline-recovery"],
        "recipient_material_stored": False,
    }


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("encrypted_payload", "path", "payload.enc.yaml"),
        ("encrypted_payload", "path", "/deploy/shopping/secrets/shopping.enc.yaml"),
        ("encrypted_payload", "path", "deploy/shopping/secrets/../shopping.enc.yaml"),
        ("encrypted_payload", "path", "deploy/shopping/secrets/shopping.yaml"),
        ("identity_custody", "relative_path", ""),
        ("identity_custody", "relative_path", "/Users/example/.config/sops/age/keys.txt"),
        ("identity_custody", "relative_path", ".config/sops/../age/keys.txt"),
        ("identity_custody", "base", "user-home"),
        ("identity_custody", "platform", "linux"),
        ("identity_custody", "required_owner", "any-user"),
        ("identity_custody", "maximum_mode", "0644"),
        ("identity_custody", "external_to_repository", False),
        ("identity_custody", "contents_inspected", True),
    ],
)
def test_schema_and_runtime_reject_unsafe_contracts(
    tmp_path: Path, section: str, field: str, value: object,
) -> None:
    definition = definition_for(tmp_path)
    definition[section][field] = value
    schema = json.loads(SCHEMA_PATH.read_text())
    assert not jsonschema.Draft202012Validator(schema).is_valid(definition)
    with pytest.raises(BackendDefinitionError):
        validate_definition(definition)
    report = adapter_for(tmp_path, definition).inspect()
    assert report.configuration_valid is False
    assert report.ready is False


def test_absent_binaries_fail_closed(tmp_path: Path) -> None:
    report = adapter_for(tmp_path, definition_for(tmp_path), resolver=lambda _name: None).inspect()
    assert report.ready is False
    assert all(checks(report)[f"executable:{name}"] is False for name in ("sops", "age", "age-keygen"))
    assert report.configuration_valid is True
    assert report.production_status == "NOT_DEPLOYED"


def test_absent_payload_fails_closed(tmp_path: Path) -> None:
    definition = definition_for(tmp_path)
    _, identity = material_paths(tmp_path)
    create_material(identity, "not-read-by-adapter")
    report = adapter_for(tmp_path, definition).inspect()
    assert checks(report)["payload:present"] is False
    assert report.ready is False


def test_absent_identity_fails_closed(tmp_path: Path) -> None:
    definition = definition_for(tmp_path)
    payload, _ = material_paths(tmp_path)
    create_material(payload, "encrypted-marker")
    report = adapter_for(tmp_path, definition).inspect()
    assert checks(report)["identity:present"] is False
    assert report.ready is False


@pytest.mark.parametrize(("target", "mode"), [("payload", 0o644), ("identity", 0o640)])
def test_unsafe_mode_fails_closed(tmp_path: Path, target: str, mode: int) -> None:
    definition = definition_for(tmp_path)
    payload, identity = material_paths(tmp_path)
    create_material(payload, "encrypted-marker", mode if target == "payload" else 0o600)
    create_material(identity, "identity-marker", mode if target == "identity" else 0o600)
    report = adapter_for(tmp_path, definition).inspect()
    assert checks(report)[f"{target}:mode"] is False
    assert report.ready is False


def test_unsafe_ownership_fails_closed(tmp_path: Path) -> None:
    definition = definition_for(tmp_path)
    payload, identity = material_paths(tmp_path)
    create_material(payload, "encrypted-marker")
    create_material(identity, "identity-marker")
    report = SopsAgeBackendAdapter(
        definition, executable_resolver=lambda _name: "/safe/bin/tool",
        repository_root=tmp_path / "repo", control_plane_home=tmp_path / "home",
        expected_uid=os.getuid() + 1,
    ).inspect()
    assert checks(report)["payload:owner"] is False
    assert checks(report)["identity:owner"] is False
    assert report.ready is False


def test_safe_metadata_path_is_ready_but_still_not_deployed(tmp_path: Path) -> None:
    definition = definition_for(tmp_path)
    payload, identity = material_paths(tmp_path)
    create_material(payload, "encrypted-secret-marker")
    create_material(identity, "identity-secret-marker")
    report = adapter_for(tmp_path, definition).inspect()
    rendered = json.dumps(report.to_dict(), sort_keys=True)
    assert report.ready is True
    assert report.production_status == "NOT_DEPLOYED"
    assert "encrypted-secret-marker" not in rendered
    assert "identity-secret-marker" not in rendered
    assert report.to_dict()["secret_values_read"] is False


def test_payload_and_identity_contents_are_never_read_or_serialized(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    definition = definition_for(tmp_path)
    payload, identity = material_paths(tmp_path)
    create_material(payload, "payload-secret-value")
    create_material(identity, "identity-secret-value")

    def reject_content_read(*_args, **_kwargs):
        raise AssertionError("secret material must not be read")

    monkeypatch.setattr(Path, "read_text", reject_content_read)
    rendered = json.dumps(adapter_for(tmp_path, definition).inspect().to_dict())
    assert "payload-secret-value" not in rendered
    assert "identity-secret-value" not in rendered


def test_malformed_configuration_is_distinct_from_not_deployed(tmp_path: Path) -> None:
    definition = definition_for(tmp_path)
    definition["production_status"] = "PRODUCTION"
    with pytest.raises(BackendDefinitionError):
        validate_definition(definition)
    report = adapter_for(tmp_path, definition).inspect()
    assert report.configuration_valid is False
    assert report.production_status == "UNKNOWN"
    assert report.error_code == "MALFORMED_CONFIGURATION"
    assert report.ready is False


def test_core_port_is_vendor_neutral_and_dependency_direction_is_clean() -> None:
    assert hasattr(SecretBackendInspectionPort, "inspect")
    core_text = "\n".join(path.read_text() for path in (ROOT / "core/secrets").glob("*.py"))
    assert "sops" not in core_text.lower()
    imports: list[str] = []
    for path in (ROOT / "core").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
    assert not [name for name in imports if name == "ops" or name.startswith("ops.")]
    assert not [name for name in imports if name == "integrations" or name.startswith("integrations.")]


def test_adapter_has_no_secret_runtime_keychain_or_subprocess_access() -> None:
    source = ADAPTER_PATH.read_text()
    prohibited = (
        "subprocess", "security", "keychain", "docker", "colima", "wordpress",
        "woocommerce", "mariadb", "caddy", "ubuntu", "urllib", "requests",
        "os.environ", "getenv(", "read_bytes", "decrypt(", "encrypt(", "keygen(",
    )
    assert not [token for token in prohibited if token in source.lower()]
    assert source.count("read_text(") == 1
    assert "path.read_text" in source

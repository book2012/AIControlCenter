from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
import yaml

from ops.macos.shopping.secret_preflight import (
    ContractError,
    inspect_action,
    load_contract,
    main,
    required_key_names,
    validate_contract,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "deploy/shopping/config/secret-contract.json"
RUNTIME = [
    "SHOPPING_WORDPRESS_PORT", "SHOPPING_DB_NAME", "SHOPPING_DB_USER",
    "SHOPPING_DB_PASSWORD", "SHOPPING_DB_ROOT_PASSWORD",
]
BOOTSTRAP = [
    "SHOPPING_WORDPRESS_PORT", "SHOPPING_DB_NAME", "SHOPPING_DB_USER",
    "SHOPPING_DB_PASSWORD", "SHOPPING_DB_ROOT_PASSWORD",
    "SHOPPING_SITE_URL", "SHOPPING_SITE_TITLE", "SHOPPING_ADMIN_USER",
    "SHOPPING_ADMIN_PASSWORD", "SHOPPING_ADMIN_EMAIL",
]


def test_contract_schema_shape_and_unique_names() -> None:
    contract = load_contract()
    validate_contract(contract)
    names = [item["name"] for item in contract["keys"]]
    assert len(names) == len(set(names)) == 10
    broken = json.loads(json.dumps(contract))
    broken["keys"].append(broken["keys"][0])
    try:
        validate_contract(broken)
    except ContractError:
        pass
    else:
        raise AssertionError("duplicate contract key accepted")


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("name", "SHOPPING_BAD-KEY"),
        ("sensitivity", "credential"),
    ],
)
def test_structurally_malformed_contract_fails_closed(field: str, replacement: str) -> None:
    broken = json.loads(json.dumps(load_contract()))
    target = next(item for item in broken["keys"] if item["name"] == "SHOPPING_DB_PASSWORD")
    target[field] = replacement
    with pytest.raises(ContractError):
        validate_contract(broken)


def test_secret_and_config_classification() -> None:
    classified = {item["name"]: item["sensitivity"] for item in load_contract()["keys"]}
    assert {name for name, kind in classified.items() if kind == "secret"} == {
        "SHOPPING_ADMIN_PASSWORD", "SHOPPING_DB_PASSWORD", "SHOPPING_DB_ROOT_PASSWORD"
    }
    assert {name for name, kind in classified.items() if kind == "config"} == set(classified) - {
        "SHOPPING_ADMIN_PASSWORD", "SHOPPING_DB_PASSWORD", "SHOPPING_DB_ROOT_PASSWORD"
    }


def test_action_specific_required_keys() -> None:
    contract = load_contract()
    assert required_key_names(contract, "runtime_cutover") == RUNTIME
    assert required_key_names(contract, "bootstrap") == BOOTSTRAP


def test_missing_runtime_credential_fails_closed() -> None:
    report = inspect_action(load_contract(), "runtime_cutover", present_keys=set(RUNTIME) - {"SHOPPING_DB_PASSWORD"})
    assert report["preflight_passed"] is False
    assert report["missing_key_names"] == ["SHOPPING_DB_PASSWORD"]


def test_bootstrap_only_keys_do_not_block_runtime_validation() -> None:
    report = inspect_action(load_contract(), "runtime_cutover", present_keys=set(RUNTIME))
    assert report["preflight_passed"] is True
    assert "SHOPPING_ADMIN_PASSWORD" not in report["required_key_names"]


def test_contract_is_value_free_and_names_no_env_authority_files() -> None:
    raw = CONTRACT_PATH.read_text(encoding="utf-8")
    contract = json.loads(raw)
    assert contract["value_free"] is True
    assert not any(token in raw for token in ("replace_with_", ".env.admin", ".env.woocommerce"))
    assert not {"value", "default", "example"}.intersection(raw_key for item in contract["keys"] for raw_key in item)


def test_reports_never_contain_injected_secret_values() -> None:
    marker = "never-render-this-secret"
    supplied = {name: marker for name in BOOTSTRAP}
    rendered = json.dumps(inspect_action(load_contract(), "bootstrap", injected_mapping=supplied))
    assert marker not in rendered
    assert "present" in rendered


def test_unknown_presence_key_name_fails_closed() -> None:
    with pytest.raises(ValueError, match="unknown key"):
        inspect_action(load_contract(), "runtime_cutover", present_keys={"SHOPPING_UNKNOWN"})


def test_not_evaluated_is_distinct_from_pass_and_fail() -> None:
    report = inspect_action(load_contract(), "runtime_cutover")
    assert report["presence_evaluated"] is False
    assert report["preflight_passed"] is None
    assert "missing_key_names" not in report


def test_unsupported_action_emits_fail_closed_json(monkeypatch, capsys) -> None:
    monkeypatch.setattr("sys.argv", ["secret_preflight.py", "production_apply"])
    assert main() == 2
    report = json.loads(capsys.readouterr().out)
    assert report["action"] == "production_apply"
    assert report["preflight_passed"] is False
    assert report["authorization_granted"] is False


def test_cli_missing_required_presence_returns_non_success(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["secret_preflight.py", "runtime_cutover", "--present-key", "SHOPPING_WORDPRESS_PORT"],
    )
    assert main() == 2
    report = json.loads(capsys.readouterr().out)
    assert report["presence_evaluated"] is True
    assert report["preflight_passed"] is False


def test_compose_remains_secret_independent_and_ingress_contract_preserved() -> None:
    text = (ROOT / "deploy/shopping/compose.yaml").read_text(encoding="utf-8")
    compose = yaml.safe_load(text)
    assert compose["services"]["wordpress"]["ports"] == [
        "127.0.0.1:${SHOPPING_WORDPRESS_PORT}:80"
    ]
    assert "ports" not in compose["services"]["database"]
    for name in RUNTIME:
        assert f"${{{name}}}" in text
    assert ":?" not in text
    assert ":-" not in text
    env = (ROOT / "deploy/shopping/.env.example").read_text(encoding="utf-8")
    assert "SHOPPING_WORDPRESS_PORT=58082" in env


def test_service_and_capability_remain_not_deployed() -> None:
    services = json.loads((ROOT / "config/services/mac-standalone-production.json").read_text())["services"]
    runtime = next(item for item in services if item["service_id"] == "shopping-runtime")
    capability = json.loads((ROOT / "config/capabilities/mac-standalone-production.json").read_text())["capabilities"][0]
    assert runtime["production_status"] == capability["production_status"] == "NOT_DEPLOYED"
    assert capability["activation_authorized"] is False


def test_core_dependency_direction_remains_clean() -> None:
    ops_imports = 0
    integrations_imports = 0
    for path in (ROOT / "core").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = [node.module]
            ops_imports += sum(module == "ops" or module.startswith("ops.") for module in modules)
            integrations_imports += sum(module == "integrations" or module.startswith("integrations.") for module in modules)
    assert ops_imports == 0
    assert integrations_imports == 0

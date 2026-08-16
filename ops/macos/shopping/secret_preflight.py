"""Value-free, read-only Shopping secret-contract preflight."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping, Set
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = ROOT / "deploy/shopping/config/secret-contract.json"
SENSITIVITIES = {"secret", "config"}
KEY_NAME = re.compile(r"SHOPPING_[A-Z0-9_]+")


class ContractError(ValueError):
    """The value-free Shopping contract is malformed or ambiguous."""


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    validate_contract(payload)
    return payload


def validate_contract(contract: object) -> None:
    if not isinstance(contract, dict):
        raise ContractError("contract must be an object")
    if set(contract) != {
        "schema_version", "contract_id", "authority", "value_free", "actions", "keys"
    }:
        raise ContractError("contract fields do not match schema v1")
    if contract["schema_version"] != "1.0" or contract["value_free"] is not True:
        raise ContractError("contract must be schema v1 and value-free")
    if not all(isinstance(contract[field], str) and contract[field] for field in ("contract_id", "authority")):
        raise ContractError("contract identity metadata must be non-empty strings")
    actions = contract["actions"]
    if actions != ["runtime_cutover", "bootstrap"]:
        raise ContractError("actions must be the canonical ordered action set")
    keys = contract["keys"]
    if not isinstance(keys, list) or not keys:
        raise ContractError("keys must be a non-empty array")
    names: list[str] = []
    for item in keys:
        if not isinstance(item, dict) or set(item) != {"name", "sensitivity", "required"}:
            raise ContractError("each key must contain name, sensitivity, and required only")
        name = item["name"]
        if not isinstance(name, str) or KEY_NAME.fullmatch(name) is None:
            raise ContractError("key names must be canonical SHOPPING_* names")
        if item["sensitivity"] not in SENSITIVITIES:
            raise ContractError("key sensitivity must be secret or config")
        required = item["required"]
        if not isinstance(required, dict) or list(required) != actions:
            raise ContractError("required metadata must cover each canonical action in order")
        if any(type(required[action]) is not bool for action in actions):
            raise ContractError("required flags must be booleans")
        names.append(name)
    if len(names) != len(set(names)):
        raise ContractError("key names must be unique")


def required_key_names(contract: Mapping[str, Any], action: str) -> list[str]:
    validate_contract(contract)
    if action not in contract["actions"]:
        raise ContractError("unknown action")
    return [item["name"] for item in contract["keys"] if item["required"][action]]


def inspect_action(
    contract: Mapping[str, Any],
    action: str,
    *,
    present_keys: Set[str] | None = None,
    injected_mapping: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Report key names and presence only; mapping values are never inspected."""
    validate_contract(contract)
    if present_keys is not None and injected_mapping is not None:
        raise ValueError("supply present_keys or injected_mapping, not both")
    known = {item["name"] for item in contract["keys"]}
    supplied = None
    if present_keys is not None:
        supplied = set(present_keys)
    elif injected_mapping is not None:
        supplied = set(injected_mapping.keys())
    if supplied is not None and (not all(isinstance(key, str) for key in supplied) or not supplied <= known):
        raise ValueError("presence input contains an unknown key name")

    required = required_key_names(contract, action)
    missing = [] if supplied is None else [name for name in required if name not in supplied]
    report: dict[str, object] = {
        "schema_version": "1.0",
        "contract_id": contract["contract_id"],
        "action": action,
        "inspection": "read-only",
        "required_key_names": required,
        "presence_evaluated": supplied is not None,
        "preflight_passed": None if supplied is None else not missing,
        "authorization_granted": False,
        "mutation_performed": False,
        "secret_values_materialized": False,
    }
    if supplied is not None:
        report["key_state"] = [
            {"name": name, "state": "present" if name in supplied else "missing"}
            for name in required
        ]
        report["missing_key_names"] = missing
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action")
    parser.add_argument("--present-key", action="append", default=None, metavar="SHOPPING_KEY")
    args = parser.parse_args()
    try:
        report = inspect_action(
            load_contract(), args.action,
            present_keys=None if args.present_key is None else set(args.present_key),
        )
    except (ContractError, ValueError, json.JSONDecodeError, OSError) as error:
        report = {
            "schema_version": "1.0", "action": args.action,
            "inspection": "read-only", "preflight_passed": False,
            "error_type": type(error).__name__, "authorization_granted": False,
            "mutation_performed": False, "secret_values_materialized": False,
        }
        print(json.dumps(report, sort_keys=True, separators=(",", ":")))
        return 2
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0 if report["preflight_passed"] is not False else 2


if __name__ == "__main__":
    sys.exit(main())

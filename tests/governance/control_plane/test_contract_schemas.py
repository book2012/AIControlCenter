from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator

from core.governance.control_plane.contracts import CONTRACT_NAMES, load_contract_registry

AUTHORIZATION_STATES = ["REQUESTED", "AUTHORIZED", "STALE", "CONSUMED", "REJECTED"]
BUDGET_STATES = ["AVAILABLE", "CONSUMED", "EXHAUSTED", "VIOLATED"]
FORBIDDEN_NAMES = {
    "authorization_header", "cookies", "environment_dump", "raw_environment", "payload", "raw_command",
    "provider_response", "private_key", "access_token", "password", "secret",
}


def _walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def test_all_schemas_are_valid_closed_top_level_objects_with_unique_ids() -> None:
    registry = load_contract_registry()
    ids = []
    for name in CONTRACT_NAMES:
        schema = registry.contract_schema(name)
        Draft202012Validator.check_schema(schema)
        assert schema["title"] == name
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
        assert schema["required"]
        ids.append(schema["$id"])
    assert len(ids) == len(set(ids)) == 16


def test_frozen_enums_match_domain_contracts() -> None:
    registry = load_contract_registry()
    state_record = registry.contract_schema("GovernanceAuthorizationStateRecord")
    assert state_record["$defs"]["state"]["enum"] == AUTHORIZATION_STATES
    budget = registry.contract_schema("GovernanceMutationBudget")
    assert budget["$defs"]["status"]["enum"] == BUDGET_STATES
    assert budget["$defs"]["invocation_outcome"]["enum"] == [
        "COMPLETED", "CONFIRMED_ZERO_EFFECT", "UNCERTAIN"
    ]
    snapshot = registry.contract_schema("GovernancePreconditionSnapshot")
    assert snapshot["$defs"]["comparison_status"]["enum"] == ["MATCH", "DRIFT"]
    execution = registry.contract_schema("GovernanceExecutionReceipt")
    assert execution["properties"]["status"]["enum"] == ["COMPLETED", "FAILED", "UNCERTAIN"]
    postcondition = registry.contract_schema("GovernancePostconditionReport")
    assert postcondition["properties"]["decision"]["enum"] == ["PASS", "FAIL"]


def test_schemas_have_no_remote_refs_or_forbidden_transport_fields() -> None:
    registry = load_contract_registry()
    for name in CONTRACT_NAMES:
        schema = registry.contract_schema(name)
        for node in _walk(schema):
            ref = node.get("$ref")
            assert not (isinstance(ref, str) and ref.startswith(("http://", "https://")))
            properties = node.get("properties", {})
            assert not (set(properties) & FORBIDDEN_NAMES), (name, set(properties) & FORBIDDEN_NAMES)

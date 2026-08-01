import json
from pathlib import Path

import jsonschema


ROOT = Path(__file__).parents[1]
CONTRACTS = ROOT / "docs/contracts/shopping"


def load(name):
    return json.loads((CONTRACTS / name).read_text(encoding="utf-8"))


def _walk_values(value, key):
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            if child_key == key:
                yield child_value
            yield from _walk_values(child_value, key)
    elif isinstance(value, list):
        for child_value in value:
            yield from _walk_values(child_value, key)


def test_contracts_are_valid_deterministic_draft_202012_json():
    manifest = load("product-draft-manifest.json")
    for relative in manifest["contracts"].values():
        path = CONTRACTS / relative
        schema = json.loads(path.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        assert json.dumps(schema, sort_keys=True, separators=(",", ":"))
        assert schema["$schema"].endswith("2020-12/schema")


def test_identity_source_concurrency_and_idempotency_are_required():
    draft = load("v1/product-draft.schema.json")
    assert {"draft_id", "revision_id", "revision_number", "previous_revision_id", "created_at", "created_by", "correlation_id", "audit_reference"} <= set(draft["required"])
    assert {"snapshot_reference", "snapshot_digest"} <= set(draft["properties"]["source"]["required"])
    transition = load("v1/transition.schema.json")["$defs"]["command"]
    assert {"expected_revision_id", "expected_revision_number", "idempotency_key", "command_digest", "actor", "correlation_id", "audit_reference"} <= set(transition["required"])
    assert load("product-draft-manifest.json")["concurrency"]["policy"] == "EXACT_REVISION_MATCH"
    assert load("product-draft-manifest.json")["idempotency"]["different_digest_outcome"] == "REJECTED_IDEMPOTENCY_KEY_REUSE"


def test_approval_is_revision_bound_and_human_only():
    approval = load("v1/approval-decision.schema.json")
    assert {"draft_id", "revision_id", "reviewer", "correlation_id", "audit_reference", "idempotency_key"} <= set(approval["required"])
    assert approval["properties"]["reviewer"]["properties"]["actor_type"] == {"const": "HUMAN"}
    assert "AI" not in json.dumps(approval)


def test_lifecycle_is_closed_and_has_no_deployed_state():
    manifest = load("product-draft-manifest.json")
    lifecycle = manifest["lifecycle"]
    assert lifecycle["unspecified_transition_policy"] == "REJECT"
    assert "DEPLOYMENT_READY" in lifecycle["states"]
    assert "DEPLOYED" not in lifecycle["states"]
    assert ["REVIEW_REQUIRED", "APPROVED"] in lifecycle["permitted_transitions"]
    assert ["REJECTED", "APPROVED"] not in lifecycle["permitted_transitions"]
    states = set(lifecycle["states"])
    assert all(set(pair) <= states and len(pair) == 2 for pair in lifecycle["permitted_transitions"])
    assert len(lifecycle["permitted_transitions"]) == len({tuple(pair) for pair in lifecycle["permitted_transitions"]})


def test_contracts_exclude_credentials_and_ubuntu_ownership():
    text = " ".join((CONTRACTS / path).read_text(encoding="utf-8").lower() for path in load("product-draft-manifest.json")["contracts"].values())
    for forbidden in ("password", "secret", "consumer_key", "consumer_secret", "credential", "ubuntu"):
        assert forbidden not in text


def test_no_runtime_mutation_route_or_woocommerce_write_was_added():
    route = (ROOT / "core/api/routes/shopping.py").read_text(encoding="utf-8")
    assert all(token not in route for token in ("@router.post", "@router.put", "@router.patch", "@router.delete"))
    assert "NOT_IMPLEMENTED" in json.dumps(load("product-draft-manifest.json"))


def test_manifest_documentation_and_utc_rules_agree():
    manifest = load("product-draft-manifest.json")
    architecture = (ROOT / "docs/architecture/SHOP-02A-PRODUCT-DRAFT-WORKFLOW.md").read_text(encoding="utf-8")
    for state in manifest["lifecycle"]["states"]:
        assert state in architecture
    for schema in manifest["contracts"].values():
        assert (CONTRACTS / schema).is_file()
    for name in (
        "product-draft.schema.json",
        "source-snapshot-reference.schema.json",
        "revision-identity.schema.json",
        "suggestion-provenance.schema.json",
        "validation-result.schema.json",
        "approval-decision.schema.json",
        "transition.schema.json",
        "deployment-intent.schema.json",
    ):
        schema = load(f"v1/{name}")
        assert any(
            value == "Z$"
            for value in _walk_values(schema, "pattern")
        )


def test_validation_and_deployment_intent_are_revision_bound_and_deterministic():
    validation = load("v1/validation-result.schema.json")
    assert {"revision_id", "validation_input_digest", "result_digest", "validator_version"} <= set(validation["required"])
    intent = load("v1/deployment-intent.schema.json")
    assert {"intent_id", "revision_id", "expected_source_digest", "authorization_reference", "idempotency_key", "created_by", "correlation_id", "audit_reference", "created_at"} <= set(intent["required"])
    assert intent["properties"]["readiness_status"]["enum"] == ["NOT_READY", "READY"]


def test_inventory_is_machine_readable_and_matches_static_architecture():
    inventory = load("inventory.json")
    counts = inventory["counts"]
    assert counts["draft_assets_found"] == 9
    assert counts["existing_shopping_mutation_routes"] == 0
    assert counts["woocommerce_write_methods"] == 0
    assert counts["approval_assets_found"] > 0
    assert counts["audit_assets_found"] > 0
    assert counts["idempotency_assets_found"] > 0
    assert inventory["baseline_commit"] == "31a3569100bf8049b918b0c17eb8c546c1968b74"
    shopping_api = (ROOT / "docs/shopping/API.md").read_text(encoding="utf-8")
    assert "NOT_IMPLEMENTED" in shopping_api and "NOT_AUTHORIZED" in shopping_api

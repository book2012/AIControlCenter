from __future__ import annotations

import ast
import copy
import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import jsonschema
import pytest

from core.secrets.provisioning import ProvisioningPlan, Readiness, plan_for
from ops.macos.shopping.sops_age_provisioning_inspector import (
    ProvisioningObservations,
    SopsAgeProvisioningInspector,
    load_backend_definition,
    load_provisioning_definition,
    validate_provisioning_definition,
)

ROOT = Path(__file__).resolve().parents[1]
DEFINITION_PATH = ROOT / "config/shopping-secret-provisioning.json"
SCHEMA_PATH = ROOT / "config/schemas/shopping-secret-provisioning.schema.json"
INSPECTOR_PATH = ROOT / "ops/macos/shopping/sops_age_provisioning_inspector.py"
PAYLOAD_PATH = ROOT / "deploy/shopping/secrets/shopping.enc.yaml"


def observations(**overrides: bool) -> ProvisioningObservations:
    values = {
        "sops_executable_present": True,
        "age_executable_present": True,
        "age_keygen_executable_present": True,
        "control_plane_identity_metadata_safe_present": True,
        "control_plane_recipient_metadata_registered_valid": True,
        "offline_recovery_inbox_ready": True,
        "offline_recovery_public_metadata_registered_valid": True,
    }
    values.update(overrides)
    return ProvisioningObservations(**values)


def inspect(**overrides: bool) -> dict[str, ProvisioningPlan]:
    plans = SopsAgeProvisioningInspector(
        load_provisioning_definition(), load_backend_definition(),
        observations(**overrides), control_plane_home=Path("portable-control-plane-home"),
    ).inspect()
    return {plan.action: plan for plan in plans}


def action(suffix: str, plans: dict[str, ProvisioningPlan]) -> ProvisioningPlan:
    return next(plan for name, plan in plans.items() if name.endswith(suffix))


def test_canonical_metadata_validates_as_draft_2020_12_and_preserves_history() -> None:
    definition = load_provisioning_definition()
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(definition)
    assert definition["production_status"] == "NOT_DEPLOYED"
    assert definition["materialization_implemented"] is False
    assert definition["inspection_mode"] == "READ_ONLY"
    assert definition["governance_compatibility"] == "SEC-02_CONTROLLED_EXECUTION"
    validate_provisioning_definition(definition)


@pytest.mark.parametrize(
    ("mutation"),
    [
        lambda definition: definition["actions"][0].__setitem__("action_id", "CHANGED_ACTION"),
        lambda definition: (
            definition["actions"][0].__setitem__("planner_rule", definition["actions"][1]["planner_rule"]),
            definition["actions"][1].__setitem__("planner_rule", "SOPS_PRESENT"),
        ),
        lambda definition: definition["actions"][0].__setitem__("missing_reason_code", "CHANGED_REASON"),
    ],
    ids=("action-id", "swapped-planner-rule", "missing-reason-code"),
)
def test_exact_action_contract_is_schema_and_runtime_enforced(mutation) -> None:
    definition = copy.deepcopy(load_provisioning_definition())
    mutation(definition)
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(definition)
    with pytest.raises(ValueError):
        validate_provisioning_definition(definition)


def test_canonical_json_is_the_only_exact_action_table() -> None:
    definition = load_provisioning_definition()
    identifiers = [item["action_id"] for item in definition["actions"]]
    assert identifiers == [
        "SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE",
        "SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE",
        "SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE",
        "SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE",
        "SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE",
        "SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE",
    ]
    source = INSPECTOR_PATH.read_text(encoding="utf-8")
    assert not [identifier for identifier in identifiers if identifier in source]
    assert [plan.action for plan in inspect().values()] == identifiers


@pytest.mark.parametrize(
    ("readiness", "mutation", "authorization", "count"),
    [
        (Readiness.READY, False, False, 0),
        (Readiness.MISSING, True, True, 1),
        (Readiness.BLOCKED, False, False, 0),
        (Readiness.MALFORMED, False, False, 0),
    ],
)
def test_plan_readiness_invariants(readiness, mutation, authorization, count) -> None:
    reasons = () if readiness is Readiness.READY else ("STABLE_REASON",)
    plan = plan_for(
        schema_version="1.0", backend_definition_id="opaque-backend",
        action="OPAQUE_ACTION", readiness=readiness,
        missing_prerequisites=reasons,
    )
    assert (plan.mutation_required, plan.authorization_required, plan.invocation_count) == (
        mutation, authorization, count,
    )
    assert plan.retry_policy == "NO_AUTOMATIC_RETRY"
    assert plan.rollback_policy == "NO_AUTOMATIC_ROLLBACK"
    assert plan.secret_values_read is False
    assert plan.invocation_count in (0, 1)
    with pytest.raises(FrozenInstanceError):
        plan.invocation_count = 2


def test_invalid_invariant_policy_and_secret_read_values_are_rejected() -> None:
    base = dict(schema_version="1.0", backend_definition_id="backend", action="ACTION")
    with pytest.raises(ValueError):
        ProvisioningPlan(**base, current_readiness=Readiness.READY, mutation_required=True)
    with pytest.raises(ValueError):
        ProvisioningPlan(
            **base, current_readiness=Readiness.MISSING,
            missing_prerequisites=("REASON",),
        )
    with pytest.raises(ValueError):
        ProvisioningPlan(
            **base, current_readiness=Readiness.BLOCKED,
            missing_prerequisites=("REASON",), invocation_count=1,
        )
    with pytest.raises(ValueError):
        ProvisioningPlan(
            **base, current_readiness=Readiness.MALFORMED,
            missing_prerequisites=("REASON",), authorization_required=True,
        )
    with pytest.raises(ValueError):
        ProvisioningPlan(**base, current_readiness=Readiness.READY, retry_policy="RETRY")
    with pytest.raises(ValueError):
        ProvisioningPlan(**base, current_readiness=Readiness.READY, rollback_policy="ROLLBACK")
    with pytest.raises(ValueError):
        ProvisioningPlan(**base, current_readiness=Readiness.READY, secret_values_read=True)


@pytest.mark.parametrize("readiness", [Readiness.MISSING, Readiness.BLOCKED, Readiness.MALFORMED])
def test_non_ready_plan_without_reason_code_is_rejected(readiness: Readiness) -> None:
    with pytest.raises(ValueError):
        plan_for(
            schema_version="1.0", backend_definition_id="backend",
            action="ACTION", readiness=readiness,
        )


def test_ready_plan_with_reason_code_is_rejected() -> None:
    with pytest.raises(ValueError):
        plan_for(
            schema_version="1.0", backend_definition_id="backend",
            action="ACTION", readiness=Readiness.READY,
            missing_prerequisites=("NOT_READY",),
        )


@pytest.mark.parametrize("reason", ["/unsafe/path", "prose like reason", "lowercase_reason"])
def test_unsafe_reason_code_is_rejected(reason: str) -> None:
    with pytest.raises(ValueError):
        plan_for(
            schema_version="1.0", backend_definition_id="backend",
            action="ACTION", readiness=Readiness.BLOCKED,
            missing_prerequisites=(reason,),
        )


@pytest.mark.parametrize("unsafe_action", ["/tmp/action", "action prose", "lowercase-action"])
def test_unsafe_action_identifier_is_rejected(unsafe_action: str) -> None:
    with pytest.raises(ValueError):
        plan_for(
            schema_version="1.0", backend_definition_id="backend",
            action=unsafe_action, readiness=Readiness.READY,
        )


def test_tool_plans_are_zero_when_satisfied_and_one_when_missing() -> None:
    ready = inspect()
    assert action("SOPS_INSTALL_ENSURE", ready).current_readiness is Readiness.READY
    assert action("AGE_INSTALL_ENSURE", ready).invocation_count == 0
    missing = inspect(sops_executable_present=False, age_executable_present=False)
    assert action("SOPS_INSTALL_ENSURE", missing).invocation_count == 1
    assert action("AGE_INSTALL_ENSURE", missing).current_readiness is Readiness.MISSING
    assert action("AGE_INSTALL_ENSURE", missing).authorization_required is True


def test_identity_creation_dependency_states() -> None:
    blocked = inspect(
        control_plane_identity_metadata_safe_present=False,
        age_keygen_executable_present=False,
    )
    blocked_plan = action("CONTROL_PLANE_CREATE", blocked)
    assert blocked_plan.current_readiness is Readiness.BLOCKED
    assert blocked_plan.missing_prerequisites == ("AGE_KEYGEN_TOOLING_UNAVAILABLE",)
    missing = inspect(control_plane_identity_metadata_safe_present=False)
    assert action("CONTROL_PLANE_CREATE", missing).current_readiness is Readiness.MISSING
    assert action("CONTROL_PLANE_CREATE", missing).invocation_count == 1
    assert action("CONTROL_PLANE_CREATE", inspect()).current_readiness is Readiness.READY


def test_control_plane_recipient_is_blocked_until_identity_ready() -> None:
    plans = inspect(
        control_plane_identity_metadata_safe_present=False,
        control_plane_recipient_metadata_registered_valid=False,
    )
    plan = action("CONTROL_PLANE_REGISTER_VALIDATE", plans)
    assert plan.current_readiness is Readiness.BLOCKED
    assert plan.invocation_count == 0
    missing = inspect(control_plane_recipient_metadata_registered_valid=False)
    assert action("CONTROL_PLANE_REGISTER_VALIDATE", missing).current_readiness is Readiness.MISSING


@pytest.mark.parametrize("registered", [True, False])
def test_offline_recovery_uses_public_metadata_presence_only(registered: bool) -> None:
    plan = action(
        "OFFLINE_RECOVERY_REGISTER_VALIDATE",
        inspect(offline_recovery_public_metadata_registered_valid=registered),
    )
    assert plan.current_readiness is (Readiness.READY if registered else Readiness.MISSING)
    assert not hasattr(ProvisioningObservations, "offline_recovery_private_identity")
    with pytest.raises(TypeError):
        ProvisioningObservations(  # type: ignore[call-arg]
            sops_executable_present=True,
            age_executable_present=True,
            age_keygen_executable_present=True,
            control_plane_identity_metadata_safe_present=True,
            control_plane_recipient_metadata_registered_valid=True,
            offline_recovery_inbox_ready=True,
            offline_recovery_public_metadata_registered_valid=registered,
            offline_recovery_private_identity=True,
        )


@pytest.mark.parametrize("ready", [True, False])
def test_offline_recovery_intake_is_a_distinct_sixth_action(ready: bool) -> None:
    plans = inspect(offline_recovery_inbox_ready=ready)
    intake = action("OFFLINE_RECOVERY_INTAKE", plans)
    registration = action("OFFLINE_RECOVERY_REGISTER_VALIDATE", plans)
    assert intake.action != registration.action
    assert intake.current_readiness is (Readiness.READY if ready else Readiness.MISSING)
    assert registration.current_readiness is Readiness.READY
    policy = load_provisioning_definition()["offline_recovery_intake_policy"]
    assert policy == {
        "base": "control-plane-home",
        "relative_path": ".config/aicontrolcenter/shopping-secrets/inbox/offline-recovery.txt",
        "required_owner": "control-plane-user",
        "maximum_mode": "0600",
        "external_to_repository": True,
        "no_clobber": True,
        "public_recipient_only": True,
    }


def test_value_free_plan_projection_has_only_allowed_facts() -> None:
    allowed = {
        "schema_version", "backend_definition_id", "action", "current_readiness",
        "missing_prerequisites", "mutation_required", "authorization_required",
        "invocation_count", "retry_policy", "rollback_policy", "secret_values_read",
    }
    rendered = json.dumps([plan.to_dict() for plan in inspect().values()], sort_keys=True)
    assert all(set(plan.to_dict()) == allowed for plan in inspect().values())
    assert "/Users/" not in rendered
    prohibited = ("private", "fingerprint", "credential", "BEGIN AGE", "recipient_value")
    assert not [token for token in prohibited if token.lower() in rendered.lower()]


def test_canonical_metadata_contains_no_material_or_runtime_instructions() -> None:
    raw = DEFINITION_PATH.read_text(encoding="utf-8")
    assert "/Users/" not in raw
    prohibited_keys = {
        "command", "argv", "environment", "executable_path", "private_identity",
        "public_recipient", "fingerprint", "credential", "secret", "key_contents",
    }
    assert not prohibited_keys.intersection(
        key for item in json.loads(raw)["actions"] for key in item
    )


def test_malformed_definitions_fail_closed_without_mutation() -> None:
    definition = load_provisioning_definition()
    definition["production_status"] = "DEPLOYED"
    hostile = "secret=/Users/victim/.config/private-key AGE-SECRET-KEY-1HOSTILE"
    definition["actions"][0]["action_id"] = hostile
    plans = SopsAgeProvisioningInspector(
        definition, load_backend_definition(), observations(),
        control_plane_home=Path("portable-home"),
    ).inspect()
    assert len(plans) == 1
    plan = plans[0]
    assert plan.current_readiness is Readiness.MALFORMED
    assert plan.action == "UNKNOWN_ACTION"
    assert plan.missing_prerequisites == ("MALFORMED_CONFIGURATION",)
    assert plan.invocation_count == 0
    assert plan.mutation_required is False
    assert plan.authorization_required is False
    assert plan.secret_values_read is False
    assert hostile not in json.dumps(plan.to_dict())


def test_inspector_has_no_runtime_secret_or_mutation_access() -> None:
    source = INSPECTOR_PATH.read_text(encoding="utf-8").lower()
    prohibited = (
        "subprocess", "os.environ", "getenv(", "import pwd", "keychain", "docker",
        "colima", "wordpress", "woocommerce", "mariadb", "caddy", "ubuntu",
        "urllib", "requests", "socket", "controlledexecutionport", "invoke_once",
        "age-keygen", "homebrew", "brew ", "read_bytes", "write_text",
    )
    assert not [token for token in prohibited if token in source]
    assert source.count("read_text(") == 2


def test_core_dependency_direction_is_clean() -> None:
    imports: list[str] = []
    for path in (ROOT / "core").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
    assert not [name for name in imports if name == "ops" or name.startswith("ops.")]
    assert not [name for name in imports if name == "integrations" or name.startswith("integrations.")]


def test_no_encrypted_shopping_payload_was_created() -> None:
    assert not PAYLOAD_PATH.exists()

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
from ops.macos.shopping.secret_provisioning_observations import (
    ExecutableObservation,
    FileObservation,
    RuntimeProvisioningObservations,
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


def readiness_observations(**overrides: object) -> RuntimeProvisioningObservations:
    executable = ExecutableObservation(True, True, True)
    safe_file = FileObservation(True, False, True, True, True)
    values: dict[str, object] = {
        "sops": executable,
        "age": executable,
        "age_keygen": executable,
        "control_plane_identity": safe_file,
        "control_plane_recipient_registered": True,
        "offline_recovery_inbox": safe_file,
        "offline_recovery_recipient_registered": True,
        "secret_payload_configured": False,
        "secret_payload_ready": False,
        "runtime_dependencies_configured": False,
        "runtime_dependencies_ready": False,
    }
    values.update(overrides)
    return RuntimeProvisioningObservations(**values)  # type: ignore[arg-type]


def composition(**overrides: object) -> dict[str, object]:
    inspector = SopsAgeProvisioningInspector(
        load_provisioning_definition(), load_backend_definition(), observations(),
        control_plane_home=Path("TEST_SECRET_VALUE_DO_NOT_EXPOSE"),
    )
    return inspector.inspect_readiness_composition(readiness_observations(**overrides))


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
        "colima", "caddy", "ubuntu",
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


def test_readiness_composition_has_stable_json_contract_and_is_deterministic() -> None:
    expected_top_level = {
        "schema_version", "inspection", "owner", "value_free",
        "secret_values_read", "mutation_authority", "facts", "overall_state",
        "reason_codes",
    }
    expected_facts = {
        "sops", "age", "age_keygen", "control_plane_identity",
        "control_plane_recipient_registration", "offline_recovery_inbox",
        "offline_recovery_recipient_registration", "secret_payload",
        "secret_materialization", "runtime_dependencies", "mariadb_continuity",
        "runtime_activation",
    }
    first = composition()
    second = composition()
    assert set(first) == expected_top_level
    assert set(first["facts"]) == expected_facts  # type: ignore[arg-type]
    assert first == second
    assert json.loads(json.dumps(first, sort_keys=True)) == first
    assert first["inspection"] == "READ_ONLY"
    assert first["owner"] == "MAC_MINI_M4_AICONTROLCENTER_CONTROL_PLANE"
    assert first["value_free"] is True
    assert first["secret_values_read"] is False
    assert first["mutation_authority"] is False


def test_composition_fails_closed_for_missing_and_unsafe_metadata() -> None:
    missing = composition(sops=ExecutableObservation(False, False, False))
    assert missing["overall_state"] == "BLOCKED"
    assert missing["facts"]["sops"]["state"] == "MISSING"  # type: ignore[index]
    unsafe = composition(
        offline_recovery_inbox=FileObservation(False, True, False, False, False)
    )
    inbox = unsafe["facts"]["offline_recovery_inbox"]  # type: ignore[index]
    assert inbox == {
        "state": "UNSAFE", "present": True, "regular_file": False,
        "symlink_rejected": True, "expected_ownership": False,
        "safe_mode": False, "nonempty": False, "ready": False,
        "fixed_canonical_artifact": True, "contents_inspected": False,
    }
    assert unsafe["overall_state"] == "BLOCKED"


def test_mariadb_and_unimplemented_materialization_block_runtime_activation() -> None:
    report = composition(
        secret_payload_configured=True, secret_payload_ready=True,
        runtime_dependencies_configured=True, runtime_dependencies_ready=True,
    )
    facts = report["facts"]  # type: ignore[assignment]
    continuity = facts["mariadb_continuity"]
    assert continuity["state"] == "BLOCKED"
    assert continuity["reason_codes"] == [
        "MARIADB_HISTORICAL_CREDENTIAL_CONTINUITY_UNRESOLVED"
    ]
    assert continuity["credential_values_inspected"] is False
    assert continuity["blocks"] == [
        "DB_SECRET_PAYLOAD", "DB_SECRET_MATERIALIZATION", "DB_DEPENDENT_VALIDATION",
        "WORDPRESS_WOOCOMMERCE_DB_CUTOVER", "RUNTIME_CUTOVER",
        "SHOPPING_RUNTIME_ACTIVATED",
    ]
    assert facts["secret_materialization"]["implemented"] is False
    assert facts["runtime_activation"] == {
        "state": "BLOCKED", "ready": False, "activated": False,
    }


@pytest.mark.parametrize(
    ("fact_name", "configured_name", "ready_name"),
    (
        ("secret_payload", "secret_payload_configured", "secret_payload_ready"),
        (
            "runtime_dependencies",
            "runtime_dependencies_configured",
            "runtime_dependencies_ready",
        ),
    ),
)
@pytest.mark.parametrize(
    ("configured", "ready", "expected_state"),
    (
        (False, False, "MISSING"),
        (True, False, "BLOCKED"),
        (True, True, "READY"),
        (False, True, "MALFORMED"),
    ),
)
def test_configured_readiness_state_table_fails_closed(
    fact_name: str,
    configured_name: str,
    ready_name: str,
    configured: bool,
    ready: bool,
    expected_state: str,
) -> None:
    overrides = {configured_name: configured, ready_name: ready}
    first = composition(**overrides)
    second = composition(**overrides)
    fact = first["facts"][fact_name]  # type: ignore[index]

    assert fact == {
        "state": expected_state,
        "configured": configured,
        "ready": ready,
    }
    assert first["reason_codes"] == second["reason_codes"]

    if expected_state == "MALFORMED":
        activation = first["facts"]["runtime_activation"]  # type: ignore[index]
        assert first["overall_state"] == "BLOCKED"
        assert activation["ready"] is False
        assert activation["activated"] is False
        assert f"{fact_name.upper()}_MALFORMED" in first["reason_codes"]
        assert not any(
            value in json.dumps(first["reason_codes"])
            for value in (
                "TEST_SECRET_VALUE_DO_NOT_EXPOSE",
                "TEST_RECIPIENT_VALUE_DO_NOT_EXPOSE",
                "TEST_PRIVATE_IDENTITY_DO_NOT_EXPOSE",
                "/Users/",
            )
        )


def test_composition_projection_excludes_sensitive_values_paths_and_authority() -> None:
    sentinels = (
        "TEST_SECRET_VALUE_DO_NOT_EXPOSE",
        "TEST_RECIPIENT_VALUE_DO_NOT_EXPOSE",
        "TEST_PRIVATE_IDENTITY_DO_NOT_EXPOSE",
    )
    rendered = json.dumps(composition(), sort_keys=True)
    assert not [sentinel for sentinel in sentinels if sentinel in rendered]
    assert "/Users/" not in rendered
    assert "stdout" not in rendered and "stderr" not in rendered
    assert "environment" not in rendered
    assert "AuthorizationConsumptionPort" not in rendered
    assert "ControlledExecutionPort" not in rendered
    assert "mutation_budget" not in rendered
    assert "GovernanceExecutionRequest" not in rendered

    def assert_json_types(value: object) -> None:
        assert not isinstance(value, Path)
        if isinstance(value, dict):
            for key, item in value.items():
                assert isinstance(key, str)
                assert_json_types(item)
        elif isinstance(value, list):
            for item in value:
                assert_json_types(item)
        else:
            assert value is None or isinstance(value, (str, bool, int, float))

    assert_json_types(composition())


def test_composition_has_closed_readiness_vocabulary_and_no_mutation_surface() -> None:
    report = composition()
    assert {fact["state"] for fact in report["facts"].values()} <= {
        "READY", "MISSING", "BLOCKED", "UNSAFE", "MALFORMED",
    }
    inspector = SopsAgeProvisioningInspector(
        load_provisioning_definition(), load_backend_definition(), observations(),
        control_plane_home=Path("portable-home"),
    )
    prohibited = {
        "invoke", "invoke_once", "execute", "write", "create", "install",
        "register", "materialize", "cutover", "retry", "rollback", "compensate",
        "recover", "authorize", "consume_authorization",
    }
    assert not prohibited.intersection(dir(inspector))


def test_composition_preserves_six_action_semantics_and_control_plane_ownership() -> None:
    before = [plan.to_dict() for plan in inspect().values()]
    composition()
    after = [plan.to_dict() for plan in inspect().values()]
    assert before == after
    assert [item["action"] for item in after][-2:] == [
        "SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE",
        "SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE",
    ]
    rendered = json.dumps(composition(), sort_keys=True)
    assert "UBUNTU" not in rendered
    assert "WORDPRESS_WOOCOMMERCE_DB_CUTOVER" in rendered
    assert composition()["owner"] != "WORDPRESS"
    assert composition()["owner"] != "WOOCOMMERCE"

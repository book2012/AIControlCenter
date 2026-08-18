import ast
import copy
import pickle
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from core.secrets.mariadb_continuity_validation import MariaDBContinuityValidationRequest
from ops.macos.shopping.mariadb_continuity_validation_composition import (
    HumanPresenceGrant,
    HumanPresenceGrantError,
    MariaDBContinuityCompositionError,
    MariaDBContinuityValidationCompositionService,
    _issue_phase_a_inert_test_grant,
)


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = ROOT / "ops/macos/shopping/mariadb_continuity_validation_composition.py"
PRESERVED = (
    "core/secrets/mariadb_continuity_validation.py",
    "core/secrets/mariadb_continuity_validation_port.py",
    "ops/macos/shopping/mariadb_continuity_validation_adapter.py",
)
SIX_ACTION_FILES = (
    "core/governance/control_plane/application/shopping_provisioning_coordinator.py",
    "ops/macos/shopping/secret_provisioning_adapters.py",
)
SIX_ACTIONS = {
    "SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE",
    "SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE",
    "SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE",
    "SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE",
    "SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE",
    "SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE",
}


class FakeAssembler:
    def __init__(self, capability=object(), error=None):
        self.capability, self.error, self.calls = capability, error, 0

    def assemble(self, request):
        self.calls += 1
        if self.error:
            raise self.error
        return self.capability


def test_canonical_composition_is_opaque_and_does_not_invoke_capability() -> None:
    class Capability:
        calls = 0
        def validate_once(self):
            self.calls += 1
    capability = Capability()
    assembler = FakeAssembler(capability)
    request = MariaDBContinuityValidationRequest.canonical()
    result = MariaDBContinuityValidationCompositionService(assembler).compose(
        request, _issue_phase_a_inert_test_grant(request)
    )
    assert result is capability
    assert assembler.calls == 1
    assert capability.calls == 0


def test_types_and_canonical_profile_are_closed() -> None:
    service = MariaDBContinuityValidationCompositionService(FakeAssembler())
    with pytest.raises(TypeError):
        service.compose(object(), object())
    with pytest.raises(HumanPresenceGrantError):
        HumanPresenceGrant(MariaDBContinuityValidationRequest.canonical())
    with pytest.raises(HumanPresenceGrantError):
        HumanPresenceGrant(object())


def test_grant_is_single_use_before_assembly() -> None:
    request = MariaDBContinuityValidationRequest.canonical()
    grant, assembler = _issue_phase_a_inert_test_grant(request), FakeAssembler()
    service = MariaDBContinuityValidationCompositionService(assembler)
    service.compose(request, grant)
    with pytest.raises(HumanPresenceGrantError):
        service.compose(request, grant)
    assert assembler.calls == 1


def test_concurrent_use_assembles_exactly_once() -> None:
    request = MariaDBContinuityValidationRequest.canonical()
    grant, assembler = _issue_phase_a_inert_test_grant(request), FakeAssembler()
    service = MariaDBContinuityValidationCompositionService(assembler)
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: _capture(service, request, grant), range(2)))
    assert sum(outcome == "ok" for outcome in outcomes) == 1
    assert assembler.calls == 1


def _capture(service, request, grant):
    try:
        service.compose(request, grant)
        return "ok"
    except HumanPresenceGrantError:
        return "consumed"


def test_assembly_failure_consumes_without_retry_or_recreation() -> None:
    request = MariaDBContinuityValidationRequest.canonical()
    marker = "driver-secret-error-text"
    grant = _issue_phase_a_inert_test_grant(request)
    assembler = FakeAssembler(error=RuntimeError(marker))
    service = MariaDBContinuityValidationCompositionService(assembler)
    with pytest.raises(MariaDBContinuityCompositionError) as captured:
        service.compose(request, grant)
    assert marker not in str(captured.value)
    assert captured.value.__cause__ is None
    assert captured.value.__context__ is None
    assert assembler.calls == 1
    with pytest.raises(HumanPresenceGrantError):
        service.compose(request, grant)
    assert assembler.calls == 1


def test_grant_has_no_serializable_projection_or_token_identity() -> None:
    grant = _issue_phase_a_inert_test_grant(
        MariaDBContinuityValidationRequest.canonical()
    )
    with pytest.raises(TypeError):
        copy.copy(grant)
    with pytest.raises(TypeError):
        copy.deepcopy(grant)
    with pytest.raises(TypeError):
        pickle.dumps(grant)
    assert not hasattr(grant, "to_projection")
    assert not hasattr(grant, "to_dict")
    assert not hasattr(grant, "id")
    assert not hasattr(grant, "token")
    assert not hasattr(grant, "authorization_id")
    assert not hasattr(grant, "capability_id")
    assert not hasattr(grant, "__dict__")


def test_static_architecture_and_06_are_preserved() -> None:
    source = PRODUCTION.read_text()
    tree = ast.parse(source)
    forbidden_imports = {
        "subprocess", "socket", "requests", "urllib", "docker", "pymysql",
        "MySQLdb", "mysql", "mariadb", "sqlalchemy", "os", "pathlib",
    }
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree) if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    assert imported.isdisjoint(forbidden_imports)
    forbidden_names = {
        "GovernanceAuthorization", "AuthorizationConsumptionPort",
        "GovernanceMutationBudget", "GovernanceExecutionRequest",
        "GovernanceExecutionReceipt", "ControlledExecutionPort",
        "ShoppingProvisioningGovernanceCoordinator",
    }
    assert forbidden_names.isdisjoint(source.split())
    authority_verbs = {"mint", "issue", "authorize", "create_grant", "new_grant"}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            normalized = node.name.strip("_").lower()
            if normalized in authority_verbs or any(
                verb in normalized for verb in authority_verbs
            ):
                assert node.name.startswith("_")
                assert "Phase-A" in (ast.get_docstring(node) or "")
                assert "not Production authorization" in (ast.get_docstring(node) or "")
    for relative in PRESERVED:
        assert (ROOT / relative).read_bytes() == _head_bytes(relative)


def test_exact_six_shopping_actions_and_tracked_files_are_preserved() -> None:
    for relative in SIX_ACTION_FILES:
        path = ROOT / relative
        source = path.read_text()
        actions = {
            node.value
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value.startswith("SHOPPING_SECRET_")
            and node.value != "SHOPPING_SECRET_PROVISIONING"
        }
        assert actions == SIX_ACTIONS
        assert path.read_bytes() == _head_bytes(relative)


def test_composition_service_has_no_grant_creation_path() -> None:
    tree = ast.parse(PRODUCTION.read_text())
    service = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "MariaDBContinuityValidationCompositionService"
    )
    assert not any(
        isinstance(node, ast.Call)
        and (
            isinstance(node.func, ast.Name) and node.func.id == "HumanPresenceGrant"
            or isinstance(node.func, ast.Name)
            and "grant" in node.func.id.lower()
        )
        for node in ast.walk(service)
    )


def _head_bytes(relative):
    import subprocess
    return subprocess.run(
        ["git", "show", f"HEAD:{relative}"], cwd=ROOT, check=True,
        stdout=subprocess.PIPE,
    ).stdout

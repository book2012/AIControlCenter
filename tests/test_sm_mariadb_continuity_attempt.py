import ast
from dataclasses import fields
from pathlib import Path

import pytest

from core.secrets.mariadb_continuity_attempt import (
    AttemptState,
    MariaDBContinuityAttempt,
)


ROOT = Path(__file__).parents[1]
PRODUCTION_FILE = ROOT / "core/secrets/mariadb_continuity_attempt.py"
FORBIDDEN_IMPORTS = {
    "subprocess", "socket", "requests", "urllib", "docker", "pymysql",
    "MySQLdb", "mysql", "mariadb", "sqlalchemy", "pathlib", "os",
}
FORBIDDEN_AUTHORITY_FIELDS = {
    "authorization_id", "capability_id", "token", "nonce", "mutation_budget",
    "execution_request", "execution_receipt",
}


def test_exact_closed_state_vocabulary_and_full_ordering():
    assert tuple(state.value for state in AttemptState) == (
        "NEW", "AUTHORIZED", "CONSUMED", "PRE_ATTEMPT",
        "ATTEMPT_INITIATED", "TERMINAL",
    )
    attempt = MariaDBContinuityAttempt.new()
    for state in tuple(AttemptState)[1:]:
        attempt = attempt.transition(state)
    assert attempt.state is AttemptState.TERMINAL
    assert attempt.attempted_count == 1


def test_pre_attempt_terminal_preserves_zero_attempts():
    attempt = MariaDBContinuityAttempt.new()
    for state in (AttemptState.AUTHORIZED, AttemptState.CONSUMED, AttemptState.PRE_ATTEMPT):
        attempt = attempt.transition(state)
    terminal = attempt.transition(AttemptState.TERMINAL)
    assert terminal.initiation_occurred is False
    assert terminal.attempted_count == 0


@pytest.mark.parametrize(
    ("start", "destination"),
    [
        (AttemptState.NEW, AttemptState.CONSUMED),
        (AttemptState.CONSUMED, AttemptState.AUTHORIZED),
        (AttemptState.AUTHORIZED, AttemptState.AUTHORIZED),
        (AttemptState.TERMINAL, AttemptState.NEW),
        (AttemptState.ATTEMPT_INITIATED, AttemptState.ATTEMPT_INITIATED),
    ],
)
def test_invalid_skipped_reverse_repeated_terminal_and_second_attempt_rejected(start, destination):
    initiated = start in (AttemptState.ATTEMPT_INITIATED, AttemptState.TERMINAL)
    with pytest.raises(ValueError):
        MariaDBContinuityAttempt(start, initiated).transition(destination)


@pytest.mark.parametrize("value", ["NEW", 1, None, object()])
def test_invalid_types_rejected(value):
    with pytest.raises(TypeError):
        MariaDBContinuityAttempt(value)
    with pytest.raises(TypeError):
        MariaDBContinuityAttempt.new().transition(value)


def test_projection_and_model_have_zero_authority_and_no_operational_api():
    projection = MariaDBContinuityAttempt.new().to_projection()
    authority = {key: value for key, value in projection.items() if key.endswith("_authority")}
    assert authority and set(authority.values()) == {False}
    assert FORBIDDEN_AUTHORITY_FIELDS.isdisjoint(projection)
    names = {item.name for item in fields(MariaDBContinuityAttempt)} | set(dir(MariaDBContinuityAttempt))
    assert FORBIDDEN_AUTHORITY_FIELDS.isdisjoint(names)
    assert not any(fragment in name.lower() for name in names for fragment in ("retry", "reconnect", "pool"))


def test_no_filesystem_network_driver_sql_or_governance_dependencies():
    source = PRODUCTION_FILE.read_text()
    tree = ast.parse(source)
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert imports.isdisjoint(FORBIDDEN_IMPORTS)
    assert not any(word in source for word in (
        "GovernanceAuthorization", "AuthorizationConsumptionPort",
        "GovernanceMutationBudget", "GovernanceExecutionRequest",
        "GovernanceExecutionReceipt", "ControlledExecutionPort",
        "ShoppingProvisioningGovernanceCoordinator",
    ))
    assert not any(keyword in source.upper() for keyword in ("SELECT ", "INSERT ", "UPDATE ", "DELETE ", "CREATE ", "ALTER ", "DROP "))

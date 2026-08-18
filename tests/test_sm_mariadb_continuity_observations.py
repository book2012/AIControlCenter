from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from core.secrets.mariadb_continuity_observations import (
    ConsumerCompatibility,
    ContinuityValidationCategory,
    MariaDBContinuityObservations,
    MariaDBContinuityRuntimeObservation,
    ObservationState,
    canonical_phase_b2a_observations,
)


ROOT = Path(__file__).parents[1]
PRODUCTION = ROOT / "core/secrets/mariadb_continuity_observations.py"


def test_closed_vocabulary_and_canonical_fail_closed_facts() -> None:
    assert [item.value for item in ContinuityValidationCategory] == [
        "CREDENTIAL_ACCEPTED",
        "EXPECTED_DATABASE_IDENTITY",
        "EXPECTED_ACCOUNT_IDENTITY",
        "REQUIRED_GRANTS",
        "EXPECTED_DATA_IDENTITY",
        "DECLARED_DATA_CONTINUITY",
    ]
    observation = canonical_phase_b2a_observations()
    assert all(state is ObservationState.NOT_EVALUATED for _, state in observation.facts)
    assert observation.consumer_compatibility is ConsumerCompatibility.NOT_EVALUATED
    assert observation.complete_validation is False


def test_projection_is_value_free_and_grants_zero_authority() -> None:
    projection = canonical_phase_b2a_observations().to_projection()
    assert projection["value_free"] is True
    assert all(
        projection[name] is False
        for name in (
            "authorization_authority", "capability_authority", "execution_authority",
            "mutation_authority", "retry_authority", "reconnect_authority",
            "rollback_authority",
        )
    )
    forbidden = {"password", "secret", "token", "nonce", "host", "port", "dsn", "url", "username", "sql"}
    assert not (forbidden & {key.lower() for key in projection})


def test_caller_cannot_forge_canonical_truth() -> None:
    with pytest.raises(TypeError):
        MariaDBContinuityObservations(complete_validation=True)
    observation = MariaDBContinuityObservations()
    with pytest.raises(FrozenInstanceError):
        observation.complete_validation = True


def runtime(*states: ObservationState) -> MariaDBContinuityRuntimeObservation:
    return MariaDBContinuityRuntimeObservation(*states)


def test_runtime_observation_has_exactly_six_typed_expressive_facts() -> None:
    states = (
        ObservationState.CONFIRMED,
        ObservationState.REJECTED,
        ObservationState.UNCERTAIN,
        ObservationState.NOT_EVALUATED,
        ObservationState.CONFIRMED,
        ObservationState.REJECTED,
    )
    observation = runtime(*states)
    assert tuple(state for _, state in observation.facts) == states
    assert tuple(category for category, _ in observation.facts) == tuple(ContinuityValidationCategory)
    assert observation.consumer_compatibility is ConsumerCompatibility.NOT_EVALUATED
    with pytest.raises(TypeError):
        runtime(*states[:-1], "CONFIRMED")  # type: ignore[arg-type]


def test_runtime_complete_validation_is_derived_from_all_six_facts() -> None:
    confirmed = (ObservationState.CONFIRMED,) * 6
    assert runtime(ObservationState.CONFIRMED, *((ObservationState.NOT_EVALUATED,) * 5)).complete_validation is False
    assert runtime(*confirmed).complete_validation is True
    assert runtime(*confirmed[:-1], ObservationState.UNCERTAIN).complete_validation is False
    with pytest.raises(TypeError):
        MariaDBContinuityRuntimeObservation(*confirmed, complete_validation=True)  # type: ignore[call-arg]


def test_runtime_projection_is_value_free_and_zero_authority() -> None:
    projection = runtime(*((ObservationState.CONFIRMED,) * 6)).to_projection()
    assert projection["value_free"] is True
    for authority in (
        "authorization_authority", "capability_authority", "execution_authority",
        "mutation_authority", "retry_authority", "reconnect_authority",
        "rollback_authority",
    ):
        assert projection[authority] is False


def test_production_surface_has_no_sensitive_fields() -> None:
    source = PRODUCTION.read_text()
    for forbidden in ("password", "credential_value", "authorization_id", "capability_id", "database_name", "username", "SQL text"):
        assert forbidden not in source

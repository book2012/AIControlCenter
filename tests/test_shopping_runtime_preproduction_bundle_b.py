from dataclasses import fields

import pytest

from core.secrets.mariadb_continuity import ContinuityState
from core.secrets.mariadb_continuity_validation import AccountProfile
from ops.macos.shopping.shopping_runtime_preproduction_bundle_b import (
    canonical_bundle_b_preparation,
)
from ops.macos.shopping.wu09_image_preload_composition import (
    WU09ProductionComposition,
    conduct_wu09_production_image_preload,
)


def test_bundle_is_value_free_inert_and_preserves_separate_boundaries():
    bundle = canonical_bundle_b_preparation()
    projection = bundle.to_projection()
    assert projection == {
        "wu09_preload_repository_preparation_ready": True,
        "wu09_loopback_repository_preparation_ready": True,
        "wu10_repository_preparation_ready": True,
        "wu11_repository_preparation_ready": True,
        "mariadb_continuity_state": "UNRESOLVED",
        "trusted_issuer_root_operationally_available": False,
        "fresh_human_production_authorization_available": False,
        "fresh_production_observation_performed": False,
        "durable_authorization_consumed": False,
        "sec02_allow_single_invocation_granted": False,
        "production_invocation_performed": False,
        "production_access": False,
        "production_mutation": False,
        "authorization_consumed": False,
        "docker_access": False,
        "colima_access": False,
        "secret_values_read": False,
        "mariadb_connection": False,
        "sql_execution": False,
        "shopping_runtime_activated": False,
        "separate_human_authorization_required_per_future_boundary": True,
    }
    assert bundle.continuity_validation.continuity_state is ContinuityState.UNRESOLVED
    assert type(bundle.continuity_validation.continuity_state) is ContinuityState
    assert bundle.credential_slot.account_profile is (
        AccountProfile.SHOPPING_MARIADB_HISTORICAL_ACCOUNT
    )
    assert type(bundle.credential_slot.account_profile) is AccountProfile
    assert bundle.continuity_validation.mutation_budget == 0
    assert bundle.credential_slot.value_free is True
    assert bundle.credential_slot.credential_material_available is False


def test_loopback_contract_is_exact_credential_blind_and_one_shot():
    contract = canonical_bundle_b_preparation().loopback_deployment
    assert (contract.project, contract.service) == (
        "ai-shopping-mariadb-loopback", "mariadb-loopback-adapter"
    )
    assert (contract.bind_host, contract.host_port, contract.target, contract.network) == (
        "127.0.0.1", 58083, "database:3306", "ai-shopping-internal"
    )
    assert contract.maximum_deployment_invocations == 1
    assert all(getattr(contract, name) for name in (
        "credential_blind", "database_recreation_forbidden", "network_mutation_forbidden",
        "main_shopping_compose_access_forbidden", "retry_prohibited", "rollback_prohibited",
        "compensation_prohibited", "authorization_reuse_prohibited",
    ))
    assert contract.production_authorized is False


def test_object_new_composition_forgery_is_rejected_before_coordinator_execution():
    sealed = object.__new__(WU09ProductionComposition)
    with pytest.raises(AttributeError):
        sealed._coordinator = object()
    with pytest.raises(AttributeError):
        sealed._lifecycle = object()
    with pytest.raises(TypeError, match="not actively issued"):
        conduct_wu09_production_image_preload(sealed)


def test_contracts_expose_no_secret_value_or_execution_payload_fields():
    bundle = canonical_bundle_b_preparation()
    names = {
        item.name.lower()
        for contract in (bundle.loopback_deployment, bundle.credential_slot, bundle.continuity_validation)
        for item in fields(contract)
    }
    assert not {"secret", "password", "credential_value", "sql", "argv"}.intersection(names)

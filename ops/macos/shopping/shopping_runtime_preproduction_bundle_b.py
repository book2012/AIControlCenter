"""Value-free readiness contracts for the WU09-WU11 Production boundaries.

Importing or constructing these contracts performs no observation, secret
acquisition, authorization consumption, connection, SQL, or mutation.
"""

from dataclasses import dataclass, field
from typing import Any

from core.secrets.mariadb_continuity import ContinuityState
from core.secrets.mariadb_continuity_validation import AccountProfile
from ops.macos.shopping.mariadb_continuity_credential_slot_resolver import (
    CredentialSlot,
    ResolverOwner,
)
from ops.macos.shopping.mariadb_loopback_port_deployment import (
    BIND_HOST,
    EXTERNAL_NETWORK,
    PROJECT,
    SERVICE,
    TARGET_HOST,
    TARGET_PORT,
)


@dataclass(frozen=True, slots=True)
class WU09LoopbackDeploymentCeremonyContract:
    project: str = field(default=PROJECT, init=False)
    service: str = field(default=SERVICE, init=False)
    bind_host: str = field(default=BIND_HOST, init=False)
    host_port: int = field(default=58083, init=False)
    target: str = field(default=f"{TARGET_HOST}:{TARGET_PORT}", init=False)
    network: str = field(default=EXTERNAL_NETWORK, init=False)
    fresh_human_authorization_required: bool = field(default=True, init=False)
    durable_consume_once_required: bool = field(default=True, init=False)
    sec02_single_invocation_required: bool = field(default=True, init=False)
    maximum_deployment_invocations: int = field(default=1, init=False)
    credential_blind: bool = field(default=True, init=False)
    database_recreation_forbidden: bool = field(default=True, init=False)
    network_mutation_forbidden: bool = field(default=True, init=False)
    main_shopping_compose_access_forbidden: bool = field(default=True, init=False)
    retry_prohibited: bool = field(default=True, init=False)
    rollback_prohibited: bool = field(default=True, init=False)
    compensation_prohibited: bool = field(default=True, init=False)
    authorization_reuse_prohibited: bool = field(default=True, init=False)
    production_authorized: bool = field(default=False, init=False)


@dataclass(frozen=True, slots=True)
class WU10CredentialSlotProvisioningPreparation:
    account_profile: AccountProfile = field(
        default=AccountProfile.SHOPPING_MARIADB_HISTORICAL_ACCOUNT, init=False
    )
    slot: CredentialSlot = field(default=CredentialSlot.FIXED_AUTHORITATIVE_PRODUCTION_SLOT, init=False)
    owner: ResolverOwner = field(default=ResolverOwner.MAC_CONTROL_PLANE, init=False)
    existing_secret_provisioning_infrastructure_required: bool = field(default=True, init=False)
    exact_create_only: bool = field(default=True, init=False)
    read_only_readiness_required: bool = field(default=True, init=False)
    durable_consume_once_required: bool = field(default=True, init=False)
    maximum_provisioning_invocations: int = field(default=1, init=False)
    value_free: bool = field(default=True, init=False)
    credential_material_available: bool = field(default=False, init=False)
    production_authorized: bool = field(default=False, init=False)


@dataclass(frozen=True, slots=True)
class WU11ContinuityValidationPreparation:
    continuity_state: ContinuityState = field(
        default=ContinuityState.UNRESOLVED, init=False
    )
    concrete_validator_reuse_required: bool = field(default=True, init=False)
    fresh_human_authorization_required: bool = field(default=True, init=False)
    read_only: bool = field(default=True, init=False)
    mutation_budget: int = field(default=0, init=False)
    maximum_connection_auth_attempts: int = field(default=1, init=False)
    retry_prohibited: bool = field(default=True, init=False)
    reconnect_prohibited: bool = field(default=True, init=False)
    strategy_selection_authorized: bool = field(default=False, init=False)
    production_authorized: bool = field(default=False, init=False)


@dataclass(frozen=True, slots=True)
class ShoppingRuntimePreproductionBundleB:
    preload_repository_preparation_ready: bool = field(default=True, init=False)
    loopback_deployment: WU09LoopbackDeploymentCeremonyContract = field(default_factory=WU09LoopbackDeploymentCeremonyContract, init=False)
    credential_slot: WU10CredentialSlotProvisioningPreparation = field(default_factory=WU10CredentialSlotProvisioningPreparation, init=False)
    continuity_validation: WU11ContinuityValidationPreparation = field(default_factory=WU11ContinuityValidationPreparation, init=False)

    def to_projection(self) -> dict[str, Any]:
        return {
            "wu09_preload_repository_preparation_ready": (
                self.preload_repository_preparation_ready
            ),
            "wu09_loopback_repository_preparation_ready": True,
            "wu10_repository_preparation_ready": True,
            "wu11_repository_preparation_ready": True,
            "mariadb_continuity_state": self.continuity_validation.continuity_state.value,
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


def canonical_bundle_b_preparation() -> ShoppingRuntimePreproductionBundleB:
    return ShoppingRuntimePreproductionBundleB()


__all__ = (
    "ShoppingRuntimePreproductionBundleB", "WU09LoopbackDeploymentCeremonyContract",
    "WU10CredentialSlotProvisioningPreparation",
    "WU11ContinuityValidationPreparation", "canonical_bundle_b_preparation",
)

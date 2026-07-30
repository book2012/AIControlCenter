"""Pure read-only M3-A4C validation and deterministic closeout."""

from __future__ import annotations

from dataclasses import asdict

from .models import (
    BRANCH,
    BOOTSTRAP_COMMIT,
    RECOVERY_COMMIT,
    TASK,
    ControlledActivationCloseoutReport,
    ControlledActivationInvariant,
    ControlledActivationReadinessDecision,
    ControlledActivationValidationConfig,
    ControlledActivationValidationError,
    ControlledActivationValidationResult,
    FutureControlledActivationContract,
    digest,
)


class ControlledActivationValidator:
    """Validates evidence facts only; exposes no writer, runner, or remote port."""

    def validate(
        self, config: ControlledActivationValidationConfig
    ) -> tuple[ControlledActivationValidationResult, ControlledActivationCloseoutReport]:
        checks: tuple[tuple[bool, str], ...] = (
            (config.branch == BRANCH, "BRANCH_MISMATCH"),
            (config.commit == RECOVERY_COMMIT, "COMMIT_MISMATCH"),
            (config.bootstrap_commit == BOOTSTRAP_COMMIT, "BOOTSTRAP_COMMIT_MISMATCH"),
            (config.control_plane_owner == "AIControlCenter", "CONTROL_PLANE_OWNER_INVALID"),
            (config.governance_owner == "AIControlCenter", "GOVERNANCE_OWNER_INVALID"),
            (config.authorization_owner == "AIControlCenter", "AUTHORIZATION_OWNER_INVALID"),
            (config.permit_owner == "AIControlCenter", "PERMIT_OWNER_INVALID"),
            (config.claim_owner == "AIControlCenter", "CLAIM_OWNER_INVALID"),
            (config.evidence_owner == "AIControlCenter", "EVIDENCE_OWNER_INVALID"),
            (config.deployment_controller == "AIControlCenter", "EXTERNAL_DEPLOYMENT_CONTROL"),
            (config.host_role == "MAC_ALWAYS_ON_BRAIN", "MAC_CONTROL_PLANE_ROLE_INVALID"),
            (not config.wordpress_business_logic_present, "WORDPRESS_LOGIC_PROHIBITED"),
            (not config.woocommerce_business_logic_present, "WOOCOMMERCE_LOGIC_PROHIBITED"),
            (not config.n8n_control_present, "N8N_CONTROL_PROHIBITED"),
            (not config.external_component_control_present, "EXTERNAL_DEPLOYMENT_CONTROL"),
            (not config.ubuntu_participation, "UBUNTU_PARTICIPATION_PROHIBITED"),
            (not config.ubuntu_authorization_scope, "UBUNTU_AUTHORIZATION_SCOPE_PROHIBITED"),
            (not config.ubuntu_state_ownership, "UBUNTU_STATE_OWNERSHIP_PROHIBITED"),
            (not config.linux_live_host, "LINUX_LIVE_HOST_PROHIBITED"),
            (not config.root_operator, "ROOT_OPERATOR_PROHIBITED"),
            (not config.environment_only_activation, "ENVIRONMENT_ONLY_ACTIVATION_PROHIBITED"),
            (config.authorization_present, "AUTHORIZATION_MISSING"),
            (config.authorization_valid, "AUTHORIZATION_INVALID"),
            (not config.authorization_expired, "AUTHORIZATION_EXPIRED"),
            (config.permit_present, "PERMIT_MISSING"),
            (not config.permit_expired, "PERMIT_EXPIRED"),
            (config.permit_consumed, "PERMIT_UNCONSUMED"),
            (not config.permit_reused, "PERMIT_REUSED"),
            (config.claim_present, "CLAIM_MISSING"),
            (config.claim_count == 1, "EXACTLY_ONE_CLAIM_REQUIRED"),
            (config.evidence_chain_valid, "EVIDENCE_CHAIN_INVALID"),
            (config.bootstrap_evidence_present, "BOOTSTRAP_EVIDENCE_MISSING"),
            (config.bootstrap_evidence_valid, "BOOTSTRAP_EVIDENCE_INVALID"),
            (config.recovery_report_present, "M3_A4B3_REPORT_MISSING"),
            (config.recovery_report_valid, "M3_A4B3_REPORT_INVALID"),
            (config.recovery_validation_passed, "RECOVERY_VALIDATION_FAILED"),
            (config.audit_status == "HEALTHY", "AUDIT_UNHEALTHY"),
            (config.audit_event_count == 0, "AUDIT_EVENT_COUNT_INVALID"),
            (config.replay_status == "HEALTHY", "REPLAY_UNHEALTHY"),
            (config.replay_event_count == 0, "REPLAY_EVENT_COUNT_INVALID"),
            (config.managed_filesystem_ready, "MANAGED_FILESYSTEM_NOT_READY"),
            (config.operational_root_safe, "OPERATIONAL_ROOT_UNSAFE"),
            (not config.operational_root_arbitrary, "ARBITRARY_OPERATIONAL_ROOT"),
            (not config.writers_authorized, "WRITERS_AUTHORIZATION_PROHIBITED"),
            (not config.monitoring_authorized, "MONITORING_AUTHORIZATION_PROHIBITED"),
            (not config.external_dispatch_authorized, "DISPATCH_AUTHORIZATION_PROHIBITED"),
            (not config.production_authorized, "PRODUCTION_AUTHORIZATION_PROHIBITED"),
            (not config.writers_active, "WRITERS_ACTIVE"),
            (not config.monitoring_active, "MONITORING_ACTIVE"),
            (not config.dispatch_active, "DISPATCH_ACTIVE"),
            (not config.validation_runner_write_requested, "VALIDATION_RUNNER_WRITE_PROHIBITED"),
            (not config.live_test_adapter_supplied, "LIVE_TEST_ADAPTER_PROHIBITED"),
            (not config.api_write_route_requested, "API_WRITE_ROUTE_PROHIBITED"),
        )
        failures = tuple(code for passed, code in checks if not passed)
        if failures:
            raise ControlledActivationValidationError(failures[0])

        invariants = tuple(ControlledActivationInvariant)
        decision = (
            ControlledActivationReadinessDecision
            .READY_FOR_SEPARATELY_AUTHORIZED_CONTROLLED_ACTIVATION
        )
        risks = ("427_EXISTING_DEPRECATION_WARNINGS",)
        result = ControlledActivationValidationResult(invariants, (), risks, decision)
        future = FutureControlledActivationContract()
        content = {
            "task": TASK,
            "branch": config.branch,
            "commit": config.commit,
            "bootstrap_evidence_status": "VALID",
            "recovery_validation_status": "VALID",
            "audit_health": config.audit_status,
            "audit_event_count": config.audit_event_count,
            "replay_health": config.replay_status,
            "replay_event_count": config.replay_event_count,
            "consumed_permit_status": "CONSUMED_SINGLE_USE",
            "single_claim_status": "EXACTLY_ONE_ATOMIC_CLAIM",
            "managed_filesystem_readiness": "READY",
            "writers_active": False,
            "monitoring_active": False,
            "dispatch_active": False,
            "ubuntu_participation": False,
            "production_authorization": False,
            "future_authorization_required": True,
            "blockers": (),
            "risks": risks,
            "readiness_decision": decision.value,
            "future_activation_contract": asdict(future),
        }
        report = ControlledActivationCloseoutReport(
            **{key: value for key, value in content.items()
               if key not in ("readiness_decision", "future_activation_contract")},
            readiness_decision=decision,
            future_activation_contract=future,
            report_digest=digest(content),
        )
        return result, report

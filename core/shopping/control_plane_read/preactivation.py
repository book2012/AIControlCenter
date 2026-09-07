"""Value-free readiness reducer. PASS never constitutes live activation proof."""

NAMESPACE = "/wp-json/aicontrolcenter/v1/shopping/"
EDGE_CHECKS = (
    ("runtime_evidence_complete", "RUNTIME_EVIDENCE_MISSING"),
    ("wordpress_loopback_only", "WORDPRESS_LOOPBACK_UNPROVEN"),
    ("direct_validation_loopback_only", "DIRECT_VALIDATION_LOOPBACK_UNPROVEN"),
    ("mariadb_internal_only", "MARIADB_INTERNAL_ONLY_UNPROVEN"),
    ("mac_only_path_verified", "MAC_ONLY_PATH_UNPROVEN"),
)
LOG_CHECKS = (("repository_controls_verified", "REPOSITORY_SAFETY_CONTROLS_UNVERIFIED"),)


def _evaluate(facts):
    facts = facts if type(facts) is dict else {}
    exact = type(facts.get("namespace")) is str and facts["namespace"] == NAMESPACE
    reasons = [] if exact else ["ADAPTER_NAMESPACE_MISMATCH"]
    reasons += [reason for key, reason in EDGE_CHECKS + LOG_CHECKS if facts.get(key) is not True]
    repository = exact and facts.get("repository_controls_verified") is True
    return {
        "status": "BLOCKED" if reasons else "PASS",
        "scope": "repository-controls-and-local-container-topology",
        "activation_status": "BLOCKED",
        "activation_reason_codes": ["EFFECTIVE_EDGE_AND_LOGGING_ATTESTATION_REQUIRED"],
        "public_edge_runtime_isolation_proven": False,
        "deployment_logging_safety_proven": False,
        "repository_logging_policy_verified": repository,
        "repository_namespace_deny_verified": repository,
        "repository_rest_route_deny_verified": repository,
        "repository_wordpress_upstream_verified": repository,
        "wordpress_loopback_only": facts.get("wordpress_loopback_only") is True,
        "automatic_retry": False, "mutation_performed": False,
        "secret_values_exposed": False, "production_authority": False,
        "ubuntu_authority": False, "reason_codes": reasons,
    }

"""Closed, value-free runtime evidence reduction; never grants activation.

Only the local collector supplies facts. This is not an evidence ingestion API.
Unknown fields and non-boolean assertions are rejected, never projected.
"""

from .runtime_components import components_complete

SCHEMA = "shopping/effective-runtime-attestation/v2"
CHECKS = {
    "caddy_effective": (
        "loaded_config_proven", "host_edge_identity_proven", "upstream_58082_proven",
        "namespace_deny_proven", "rest_route_deny_proven", "no_alternate_handler_proven",
        "loaded_equals_reviewed_adaptation", "safe_sink_proven",
    ),
    "repository_invariants": (
        "reviewed_edge_policy_valid", "reviewed_safety_controls_valid",
        "no_generic_proxy_or_caller_target", "no_public_observation_endpoint",
    ),
    "deployment_identity": (
        "reviewed_pinned_identity_contract", "expected_immutable_wordpress_image",
        "actual_runtime_image_matches", "container_identity_bound",
        "runtime_generation_identity_bound", "runtime_generation_fresh",
        "serving_generation_provenance_bound", "expected_mounts_config_bound",
        "mount_artifact_integrity_proven", "no_unexpected_mutable_executable_config",
        "caddy_executable_config_generation_bound", "control_plane_implementation_bound",
    ),
    "closed_controls": (
        "apache_configuration_closure_approved", "apache_access_sink_discard_only",
        "apache_error_sink_discard_only", "php_logging_disabled_or_discard_only",
        "php_display_errors_disabled", "php_display_startup_errors_disabled",
        "exception_argument_projection_suppressed", "wordpress_debug_false",
        "wordpress_debug_log_false", "wordpress_debug_display_false",
        "authorization_code_no_deliberate_secret_projection",
        "no_authorization_capture_tracing_apm_logging", "no_unresolved_executable_logging_component",
    ),
    "topology": (
        "mac_only_proven", "wordpress_identity_proven", "database_identity_proven",
        "wordpress_loopback_58082_proven", "mariadb_no_published_ports_proven",
        "internal_network_proven", "expected_networks_proven",
    ),
    "transport": (
        "repository_controls_proven", "literal_loopback_proven", "port_58082_proven",
        "fixed_target_proven", "trust_env_false_proven", "redirects_disabled_proven",
        "retries_zero_proven", "total_deadline_enforced", "response_bounded_proven",
    ),
}
FALSE_FIELDS = (
    "authenticated_read_performed", "capability_created", "verifier_mutation_performed",
    "mutation_performed", "secret_values_exposed", "production_authority", "ubuntu_authority",
)
ERRORS = frozenset((
    "CALLER_OVERRIDE_REJECTED", "MAC_IDENTITY_UNPROVEN", "SUBPROCESS_TIMEOUT",
    "SUBPROCESS_NONZERO", "STDOUT_OVERSIZED", "MALFORMED_JSON", "DUPLICATE_JSON_KEYS",
    "INSPECTION_UNAVAILABLE", "TOTAL_DEADLINE_EXCEEDED", "UNEXPECTED_EVIDENCE",
    "CADDY_LOADED_CONFIG_MISMATCH", "CADDY_HOST_PROCESS_UNPROVEN",
    "RUNTIME_BINDING_UNPROVEN", "SERVING_GENERATION_PROVENANCE_UNPROVEN",
))


def reduce_evidence(facts, errors=(), *, manifest=None, observed_components=None):
    # Repository-owned manifest supplies policy; runtime supplies identity only.
    reasons = []
    components = components_complete(manifest, observed_components)
    if type(facts) is not dict or set(facts) - set(CHECKS):
        facts = {}
        reasons.append("UNEXPECTED_EVIDENCE")
    result = {}
    for group, keys in CHECKS.items():
        values = facts.get(group, {})
        if type(values) is not dict or set(values) - set(keys):
            values = {}
            reasons.append("UNEXPECTED_EVIDENCE")
        if any(type(value) is not bool for value in values.values()):
            reasons.append("UNEXPECTED_EVIDENCE")
        result[group] = {key: values.get(key) is True for key in keys}
        reasons.extend(group.upper() + "_" + key.upper()
                       for key in keys if not result[group][key])
    if type(errors) not in (tuple, list):
        errors = ("UNEXPECTED_EVIDENCE",)
    reasons.extend(code if type(code) is str and code in ERRORS else "UNEXPECTED_EVIDENCE"
                   for code in errors)
    malformed = "UNEXPECTED_EVIDENCE" in reasons
    edge = (not malformed and all(result["caddy_effective"][key] for key in CHECKS["caddy_effective"]
                                if key != "safe_sink_proven")
            and all(result["topology"].values()) and all(result["transport"].values())
            and all(result["repository_invariants"][key] for key in (
                "reviewed_edge_policy_valid", "no_generic_proxy_or_caller_target", "no_public_observation_endpoint")))
    logging = (not malformed and components and result["repository_invariants"]["reviewed_safety_controls_valid"]
               and all(result["deployment_identity"].values())
               and all(result["closed_controls"].values())
               and all(result["caddy_effective"][key] for key in (
                   "loaded_config_proven", "host_edge_identity_proven",
                   "loaded_equals_reviewed_adaptation", "safe_sink_proven")))
    if not components:
        reasons.append("COMPONENT_INVENTORY_UNPROVEN")
    ready = edge and logging and not reasons
    result.update(
        schema_version=SCHEMA, scope="effective-runtime-preactivation-attestation",
        status="BLOCKED" if reasons else "PASS", activation_status="BLOCKED",
        public_edge_runtime_isolation_proven=edge,
        deployment_logging_safety_proven=logging,
        complete_component_identity_proven=components,
        controlled_nonprod_soft_launch_ready=ready,
        reason_codes=sorted(set(reasons)), **{key: False for key in FALSE_FIELDS},
    )
    return result

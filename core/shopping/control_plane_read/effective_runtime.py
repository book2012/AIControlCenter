"""Closed, value-free runtime evidence reduction; never grants activation.

Only the local collector supplies facts. This is not an evidence ingestion API.
Unknown fields and non-boolean assertions are rejected, never projected.
"""

SCHEMA = "shopping/effective-runtime-attestation/v1"
CHECKS = {
    "caddy_effective": (
        "loaded_config_proven", "host_edge_identity_proven", "upstream_58082_proven",
        "namespace_deny_proven", "rest_route_deny_proven", "no_alternate_handler_proven",
        "authorization_not_logged_proven", "safe_sink_proven",
    ),
    "apache_effective": (
        "loaded_config_proven", "custom_log_safe_proven", "error_log_safe_proven",
        "override_disabled_proven", "authorization_not_logged_proven", "modules_safe_proven",
    ),
    "php_effective": (
        "loaded_config_proven", "log_errors_off_proven", "display_errors_off_proven",
        "display_startup_errors_off_proven", "exception_args_ignored_proven",
        "error_log_safe_proven", "extensions_safe_proven",
    ),
    "wordpress_effective": (
        "debug_false_proven", "debug_log_false_proven", "debug_display_false_proven",
        "read_plugin_deployed_proven", "read_plugin_active_proven",
        "active_plugins_safe_proven", "mu_plugins_safe_proven", "drop_ins_safe_proven",
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
    "APACHE_LOADED_STATE_UNOBSERVABLE", "PHP_APACHE_SAPI_LOADED_STATE_UNOBSERVABLE",
    "WORDPRESS_EFFECTIVE_CONSTANTS_UNOBSERVABLE", "WORDPRESS_ACTIVE_PLUGINS_UNOBSERVABLE",
    "UNAPPROVED_WORDPRESS_COMPONENT", "READ_PLUGIN_NOT_DEPLOYED",
    "DEPLOYED_APACHE_POLICY_MISMATCH", "DEPLOYED_PHP_POLICY_MISMATCH",
    "WORDPRESS_DEBUG_LITERALS_UNPROVEN",
))


def reduce_evidence(facts, errors=()):
    reasons = []
    if type(facts) is not dict or set(facts) - set(CHECKS):
        facts = {}
        reasons.append("UNEXPECTED_EVIDENCE")
    result = {}
    for group, keys in CHECKS.items():
        values = facts.get(group, {})
        if type(values) is not dict or set(values) - set(keys):
            values = {}
            reasons.append("UNEXPECTED_EVIDENCE")
        result[group] = {key: values.get(key) is True for key in keys}
        reasons.extend(group.upper() + "_" + key.upper()
                       for key in keys if not result[group][key])
    reasons.extend(code if type(code) is str and code in ERRORS else "UNEXPECTED_EVIDENCE"
                   for code in errors)
    edge = all(result["caddy_effective"].values()) and all(result["topology"].values())
    logging = all(result[group][key] for group in
                  ("caddy_effective", "apache_effective", "php_effective", "wordpress_effective")
                  for key in CHECKS[group])
    result.update(
        schema_version=SCHEMA, scope="effective-runtime-preactivation-attestation",
        status="BLOCKED" if reasons else "PASS", activation_status="BLOCKED",
        public_edge_runtime_isolation_proven=edge,
        deployment_logging_safety_proven=logging,
        reason_codes=sorted(set(reasons)), **{key: False for key in FALSE_FIELDS},
    )
    return result

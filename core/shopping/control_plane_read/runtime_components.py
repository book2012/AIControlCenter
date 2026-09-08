"""Pure internal closed inventory comparison; no evidence ingestion or authority.

Runtime reports identity only; AIControlCenter owns and applies manifest policy.
A later trusted collector must establish identity through deployment binding.
Source-level effect annotations do not approve transitive dependency behavior.
"""
import re

CATEGORIES = (
    "apache_modules", "php_extensions", "zend_extensions", "wordpress_plugins",
    "wordpress_network_plugins", "wordpress_mu_plugins", "wordpress_dropins",
)
REQUIRED_PLUGINS = frozenset(("woocommerce", "ai-shopping-storefront", "ai-controlcenter-shopping-read"))
IDENTITY_FIELDS = frozenset(("identifier", "version", "artifact_digest_or_immutable_identity"))
FIELDS = frozenset(("identifier", "version", "artifact_digest_or_immutable_identity",
                    "identity_status", "role", "effect_class", "outbound_network_allowed",
                    "application_state_write_allowed", "handles_authorization", "participates_in_observation"))
BOOLS = ("outbound_network_allowed", "application_state_write_allowed", "handles_authorization")


def validate_observed_identity(entry):
    """Accept the closed identity projection, never policy assertions."""
    return (type(entry) is dict and set(entry) == IDENTITY_FIELDS
            and all(type(entry[k]) is str and entry[k].strip() == entry[k] and bool(entry[k])
                    and not any(c in entry[k] for c in "*?") for k in IDENTITY_FIELDS)
            and re.fullmatch(r"[a-zA-Z0-9_.:/-]+", entry["identifier"]) is not None)


def validate_manifest_policy_entry(entry):
    """Require resolved reviewed policy for every approved manifest entry."""
    return (type(entry) is dict and set(entry) == FIELDS
            and all(type(entry[k]) is str and entry[k].strip() == entry[k] and bool(entry[k])
                    and not any(c in entry[k] for c in '*?')
                    for k in FIELDS - set(BOOLS) - {"participates_in_observation"})
            and re.fullmatch(r"[a-zA-Z0-9_.:/-]+", entry["identifier"]) is not None
            and entry["identity_status"] == "REVIEWED_EXACT"
            and all(type(entry[k]) is bool for k in BOOLS)
            and entry["participates_in_observation"] is False)


def components_complete(manifest, observed):
    if (type(manifest) is not dict or set(manifest) != {"schema_version", *CATEGORIES}
            or manifest["schema_version"] != "shopping/runtime-component-manifest/v1"
            or type(observed) is not dict or set(observed) != set(CATEGORIES)):
        return False
    for category in CATEGORIES:
        policy = manifest[category]
        if (type(policy) is not dict or set(policy) != {
                "required", "optional_approved", "forbidden_unknown", "inventory_status"}
                or policy["forbidden_unknown"] is not True
                or policy["inventory_status"] != "REVIEWED_COMPLETE"
                or any(type(policy[k]) is not list for k in ("required", "optional_approved"))
                or type(observed[category]) is not list):
            return False
        approved = policy["required"] + policy["optional_approved"]
        actual = observed[category]
        if (not all(validate_manifest_policy_entry(e) for e in approved)
                or not all(validate_observed_identity(e) for e in actual)):
            return False
        by_identifier = {e["identifier"]: e for e in approved}
        identities = [e["identifier"] for e in approved]
        seen = [e["identifier"] for e in actual]
        required = {e["identifier"] for e in policy["required"]}
        if (len(set(identities)) != len(identities) or len(set(seen)) != len(seen)
                or not required <= set(seen) or not set(seen) <= set(identities)):
            return False
        if any(any(e[k] != by_identifier[e["identifier"]][k] for k in IDENTITY_FIELDS)
               for e in actual):
            return False
        if category == "wordpress_plugins" and not REQUIRED_PLUGINS <= required:
            return False
    return True

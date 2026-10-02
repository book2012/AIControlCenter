"""Single TTY ceremony for issue-and-run of PUBLIC-STOREFRONT-V2-ACTIVATION-01."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import uuid

from core.secrets.mariadb_continuity_trusted_mac_account_home_runtime_resolver import resolve_trusted_mac_account_home
from core.secrets.mariadb_continuity_trusted_ownership_expectation import issue_trusted_ownership_expectation
from core.shopping.public_storefront_v2_activation_03_final_authorization import (
    PublicStorefrontV2ActivationAuthorization, immutable_contract,
)
from core.shopping.public_storefront_v2_activation_03_final_reconciliation import (
    AUTHORITY_ID, EXPECTED_PORTS, MAXIMUM_LIFETIME_SECONDS,
    MUTATION_ID, canonical_json, projection,
)
from ops.macos.shopping.public_storefront_v2_activation_03_final_authorization_store import (
    PublicStorefrontV2ActivationAuthorizationStore,
)
from ops.macos.shopping.public_storefront_v2_activation_03_final_operator import (
    MacActivationPort, RUNTIME_ROOT, source_identity,
)


ACKNOWLEDGEMENT = "AUTHORIZE " + AUTHORITY_ID


def _authorization(*, preconditions: dict, uid: int, gid: int):
    now = datetime.now(timezone.utc)
    values = {
        **immutable_contract(uid=uid, gid=gid),
        "authorization_id": str(uuid.uuid4()),
        "issued_at": now.isoformat(),
        "expires_at": (now + timedelta(seconds=MAXIMUM_LIFETIME_SECONDS)).isoformat(),
        "source_head": preconditions["source"]["head"],
        "activation_bundle_sha256": preconditions["source"]["activation_bundle_sha256"],
        "precondition_json": canonical_json(preconditions),
        "artifact_identities_json": canonical_json(preconditions["source"]["artifacts"]),
        "expected_ports_json": canonical_json(EXPECTED_PORTS),
    }
    value = object.__new__(PublicStorefrontV2ActivationAuthorization)
    for name in PublicStorefrontV2ActivationAuthorization.__dataclass_fields__:
        object.__setattr__(value, name, values[name])
    return value


def issue_and_run(*, candidate_root: Path, runtime_root: Path = RUNTIME_ROOT) -> dict:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return projection("TTY_REQUIRED")
    candidate_root = candidate_root.resolve(strict=True)
    source = source_identity(candidate_root, clean_required=True)
    home = resolve_trusted_mac_account_home()
    owner = issue_trusted_ownership_expectation(home)
    port = MacActivationPort(source_root=candidate_root, runtime_root=runtime_root)
    before = port.observe_preconditions()
    print(json.dumps({
        "authority_id": AUTHORITY_ID,
        "mutation_id": MUTATION_ID,
        "source_head": source["head"],
        "activation_bundle_sha256": source["activation_bundle_sha256"],
        "source_clean_candidate": True,
        "reviewed_runtime_artifact_identities": source["artifacts"],
        "profile": "aicontrolcenter-commerce",
        "expected_ports": EXPECTED_PORTS,
        "ubuntu_authority": False,
        "business_mutation_authority": False,
        "database_recreation_allowed": False,
        "volume_recreation_allowed": False,
        "woo_write_authority": False,
    }, sort_keys=True, separators=(",", ":")))
    if input("Bind independently reviewed candidate HEAD exactly: ") != source["head"]:
        return projection("REVIEWED_HEAD_BINDING_REQUIRED")
    if input("Bind independently reviewed activation bundle SHA256 exactly: ") != source["activation_bundle_sha256"]:
        return projection("REVIEWED_BUNDLE_BINDING_REQUIRED")
    if input(f"Type exactly: {ACKNOWLEDGEMENT}\n> ") != ACKNOWLEDGEMENT:
        return projection("ACKNOWLEDGEMENT_REQUIRED")
    # The clean candidate and runtime facts are both re-read before issuance;
    # drift never consumes or authorizes a mutation.
    reread_source = source_identity(candidate_root, clean_required=True)
    if (reread_source["head"] != source["head"] or
            reread_source["activation_bundle_sha256"] != source["activation_bundle_sha256"] or
            reread_source["artifacts"] != source["artifacts"]):
        return projection("SOURCE_IDENTITY_DRIFT")
    if port.observe_preconditions() != before:
        return projection("PRECONDITION_DRIFT")
    store = PublicStorefrontV2ActivationAuthorizationStore._initialize_for_issuer()
    store._issue(_authorization(preconditions=before, uid=owner.expected_uid, gid=owner.expected_gid))
    from ops.macos.shopping.public_storefront_v2_activation_03_final_operator import ActivationRunner
    result = ActivationRunner(store, port, owner.expected_uid, owner.expected_gid).run()
    result["old_authorizations_reused"] = False
    return result


def main() -> int:
    if len(sys.argv) != 2:
        print(json.dumps(projection("CALLER_OVERRIDE_REJECTED"), sort_keys=True, separators=(",", ":")))
        return 2
    try:
        result = issue_and_run(candidate_root=Path(sys.argv[1]))
    except Exception:
        result = projection("ISSUANCE_DENIED")
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result.get("status") == "ACTIVATED" else 2


__all__ = ["ACKNOWLEDGEMENT", "issue_and_run", "main"]


if __name__ == "__main__":
    raise SystemExit(main())

"""TTY-gated issuer for PUBLIC-STOREFRONT-V2-ACTIVATION-02."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import uuid

from core.secrets.mariadb_continuity_trusted_mac_account_home_runtime_resolver import resolve_trusted_mac_account_home
from core.secrets.mariadb_continuity_trusted_ownership_expectation import issue_trusted_ownership_expectation
from core.shopping.public_storefront_v2_activation_02_authorization import PublicStorefrontV2ActivationAuthorization, immutable_contract
from core.shopping.public_storefront_v2_activation_02_reconciliation import (
    AUTHORITY_ID, MAXIMUM_LIFETIME_SECONDS, MUTATION_ID, canonical_json, projection,
)
from ops.macos.shopping.public_storefront_v2_activation_02_authorization_store import PublicStorefrontV2ActivationAuthorizationStore
from ops.macos.shopping.public_storefront_v2_activation_02_operator import MacActivationPort, RUNTIME_ROOT, source_identity


ACKNOWLEDGEMENT = "AUTHORIZE PUBLIC-STOREFRONT-V2-ACTIVATION-02"


def _authorization(*, preconditions: dict, uid: int, gid: int):
    now = datetime.now(timezone.utc)
    values = {**immutable_contract(uid=uid, gid=gid), "authorization_id": str(uuid.uuid4()),
              "issued_at": now.isoformat(), "expires_at": (now + timedelta(seconds=MAXIMUM_LIFETIME_SECONDS)).isoformat(),
              "source_head": preconditions["source"]["head"],
              "activation_bundle_sha256": preconditions["source"]["activation_bundle_sha256"],
              "precondition_json": canonical_json(preconditions),
              "artifact_identities_json": canonical_json(preconditions["source"]["artifacts"]),
              "expected_ports_json": canonical_json({"public": 58082, "shopping": 58081, "dev": 18080})}
    value = object.__new__(PublicStorefrontV2ActivationAuthorization)
    for field in PublicStorefrontV2ActivationAuthorization.__dataclass_fields__:
        object.__setattr__(value, field, values[field])
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
    print(json.dumps({"authority_id": AUTHORITY_ID, "mutation_id": MUTATION_ID,
                      "source_head": source["head"], "activation_bundle_sha256": source["activation_bundle_sha256"],
                      "reviewed_artifacts": source["artifacts"], "profile": "aicontrolcenter-commerce",
                      "maximum_uses": 1, "maximum_lifetime_seconds": MAXIMUM_LIFETIME_SECONDS,
                      "caddy_reload_max": 1, "colima_restart_authority": False,
                      "wordpress_runtime_mutation_authority": False, "database_recreation_authority": False,
                      "volume_recreation_authority": False, "woo_write_authority": False, "dns_change_authority": False},
             sort_keys=True, separators=(",", ":")))
    if input("Bind independently reviewed candidate HEAD exactly: ") != source["head"]:
        return projection("REVIEWED_HEAD_BINDING_REQUIRED")
    if input("Bind independently reviewed activation bundle SHA256 exactly: ") != source["activation_bundle_sha256"]:
        return projection("REVIEWED_BUNDLE_BINDING_REQUIRED")
    if input(f"Type exactly: {ACKNOWLEDGEMENT}\n> ") != ACKNOWLEDGEMENT:
        return projection("ACKNOWLEDGEMENT_REQUIRED")
    reread = source_identity(candidate_root, clean_required=True)
    if reread != source or port.observe_preconditions() != before:
        return projection("PRECONDITION_DRIFT")
    store = PublicStorefrontV2ActivationAuthorizationStore._initialize_for_issuer()
    store._issue(_authorization(preconditions=before, uid=owner.expected_uid, gid=owner.expected_gid))
    from ops.macos.shopping.public_storefront_v2_activation_02_operator import ActivationRunner
    return ActivationRunner(store, port, owner.expected_uid, owner.expected_gid).run()


def main() -> int:
    print(json.dumps(projection("CALLER_OVERRIDE_REJECTED"), sort_keys=True, separators=(",", ":")))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

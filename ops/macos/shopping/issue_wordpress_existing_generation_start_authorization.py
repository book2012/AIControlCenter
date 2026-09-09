"""Separate interactive 01G1G issuer; issuance never executes the mutation."""
from datetime import datetime, timedelta, timezone
import json
import sys
import uuid

from core.secrets.mariadb_continuity_trusted_mac_account_home_runtime_resolver import resolve_trusted_mac_account_home
from core.secrets.mariadb_continuity_trusted_ownership_expectation import issue_trusted_ownership_expectation
from core.shopping.wordpress_existing_generation_start_authorization import WordPressExistingGenerationStartAuthorization, immutable_contract
from core.shopping.wordpress_existing_generation_start_reconciliation import MUTATION_ID, MUTATION_ARGS, canonical_snapshot, projection
from ops.macos.shopping.wordpress_existing_generation_start_authorization_store import WordPressExistingGenerationStartAuthorizationStore
from ops.macos.shopping.wordpress_existing_generation_start_operator import observe_preconditions

ACKNOWLEDGEMENT = "AUTHORIZE " + MUTATION_ID


def issue():
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise RuntimeError("TTY_REQUIRED")
    home = resolve_trusted_mac_account_home()
    owner = issue_trusted_ownership_expectation(home)
    expected_head = input("Issuance expected clean Git HEAD (40 lowercase hex characters): ")
    expected_artifact = input("Canonical-reviewed artifact SHA-256 (from independent review record): ")
    before = canonical_snapshot(observe_preconditions())
    if json.loads(before)["head"] != expected_head:
        raise RuntimeError("EXPECTED_HEAD_REQUIRED")
    if json.loads(before)["reviewed_artifact"] != expected_artifact:
        raise RuntimeError("REVIEWED_ARTIFACT_REQUIRED")
    print(json.dumps({**immutable_contract(uid=owner.expected_uid, gid=owner.expected_gid),
                      "preconditions": json.loads(before),
                      "mutation_argv": ["/opt/homebrew/bin/docker", *MUTATION_ARGS],
                      "lifecycle_authority": False,
                      "business_mutation_authority": False}, sort_keys=True))
    if input(f"Type exactly: {ACKNOWLEDGEMENT}\n> ") != ACKNOWLEDGEMENT:
        raise RuntimeError("ACKNOWLEDGEMENT_REQUIRED")
    if canonical_snapshot(observe_preconditions()) != before:
        raise RuntimeError("PRECONDITION_DRIFT")
    now = datetime.now(timezone.utc)
    values = {**immutable_contract(uid=owner.expected_uid, gid=owner.expected_gid),
              "precondition_json": before, "authorization_id": str(uuid.uuid4()),
              "issued_at": now.isoformat(), "expires_at": (now + timedelta(minutes=10)).isoformat()}
    authorization = object.__new__(WordPressExistingGenerationStartAuthorization)
    for name in WordPressExistingGenerationStartAuthorization.__dataclass_fields__:
        object.__setattr__(authorization, name, values[name])
    WordPressExistingGenerationStartAuthorizationStore._initialize_for_issuer()._issue(authorization)
    return projection("AVAILABLE")


def main():
    try:
        result = projection("CALLER_OVERRIDE_REJECTED") if len(sys.argv) != 1 else issue()
    except Exception:
        result = projection("ISSUANCE_DENIED")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "AVAILABLE" else 2


if __name__ == "__main__":
    raise SystemExit(main())

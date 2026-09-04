"""Interactive Mac-local issuer for one immutable controlled-non-production mutation."""

from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timedelta, timezone

from core.secrets.mariadb_continuity_trusted_mac_account_home_runtime_resolver import resolve_trusted_mac_account_home
from core.secrets.mariadb_continuity_trusted_ownership_expectation import issue_trusted_ownership_expectation
from core.shopping.runtime_cutover_secret_source import SOURCE_ROLE, WORDPRESS_PORT_KEY
from core.shopping.runtime_cutover_source_authorization import (
    AUTHORITATIVE_WORK_ITEM, DESIRED_VALUE, ENVIRONMENT, MAXIMUM_USES, MUTATION_ID,
    SourceMutationAuthorization,
)
from ops.macos.shopping.runtime_cutover_source_authorization_store import RuntimeCutoverSourceAuthorizationStore

ACKNOWLEDGEMENT = "AUTHORIZE SHOP-SERVICE-START-01B:RUNTIME_CUTOVER_SOURCE_PORT_TO_58082"
EXPIRY_MINUTES = 10


def issue() -> dict[str, object]:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise RuntimeError("interactive stdin/stdout TTY required")
    home = resolve_trusted_mac_account_home()
    ownership = issue_trusted_ownership_expectation(home)
    contract = {
        "authoritative_work_item": AUTHORITATIVE_WORK_ITEM, "environment": ENVIRONMENT,
        "mutation_id": MUTATION_ID, "source_role": SOURCE_ROLE, "source_key": WORDPRESS_PORT_KEY,
        "desired_value": DESIRED_VALUE, "maximum_uses": MAXIMUM_USES,
        "trusted_uid": ownership.expected_uid, "trusted_gid": ownership.expected_gid,
        "production_authority": False, "ubuntu_authority": False,
    }
    print(json.dumps(contract, sort_keys=True))
    if input(f"Type exactly: {ACKNOWLEDGEMENT}\n> ") != ACKNOWLEDGEMENT:
        raise RuntimeError("exact human acknowledgement required")
    issued = datetime.now(timezone.utc)
    authorization = object.__new__(SourceMutationAuthorization)
    values = {**contract, "authorization_id": str(uuid.uuid4()),
              "issued_at": issued.isoformat(),
              "expires_at": (issued + timedelta(minutes=EXPIRY_MINUTES)).isoformat()}
    for name in SourceMutationAuthorization.__dataclass_fields__:
        object.__setattr__(authorization, name, values[name])
    RuntimeCutoverSourceAuthorizationStore._initialize_for_issuer()._issue(authorization)
    return {"authorization_id": authorization.authorization_id, "issued_at": authorization.issued_at,
            "expires_at": authorization.expires_at, "state": "AVAILABLE",
            "production_authority": False, "ubuntu_authority": False}


def main() -> int:
    try:
        print(json.dumps(issue(), sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"state": "DENIED", "reason": str(exc),
                          "production_authority": False, "ubuntu_authority": False}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ("issue", "main")

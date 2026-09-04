"""Read-only observer for the fixed WordPress mutation authorization store."""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from core.secrets.mariadb_continuity_trusted_mac_account_home_runtime_resolver import (
    resolve_trusted_mac_account_home,
)
from core.secrets.mariadb_continuity_trusted_ownership_expectation import (
    issue_trusted_ownership_expectation,
)
from core.shopping.wordpress_port_reconciliation import MUTATION_ID
from ops.macos.shopping.wordpress_port_authorization_store import (
    _COMPONENTS,
    _validate,
    WordPressAuthorizationStoreError,
    WordPressPortAuthorizationStore,
)

_SAFE_COLUMNS = (
    "authorization_id", "state", "issued_at", "expires_at", "mutation_id",
    "production_authority", "ubuntu_authority",
)


def _inspect_fixed_path(path: Path, *, uid: int, gid: int, test: bool = False) -> dict[str, object]:
    """Inspect a policy-bound path without constructing a mutable capability."""
    WordPressPortAuthorizationStore._safe(path, test)
    if not path.exists():
        return {"authorizations": [], "state": "MISSING_STORE"}
    WordPressPortAuthorizationStore._require(path.parent, uid, gid, 0o700, True)
    WordPressPortAuthorizationStore._require(path, uid, gid, 0o600, False)
    try:
        with sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True) as db:
            _validate(db)
            rows = db.execute(
                "SELECT " + ",".join(_SAFE_COLUMNS)
                + " FROM wordpress_mutation_authorizations ORDER BY issued_at,authorization_id"
            ).fetchall()
    except sqlite3.DatabaseError as exc:
        raise WordPressAuthorizationStoreError("authorization inspection failed") from exc

    now = datetime.now(timezone.utc)
    projected = []
    for row in rows:
        values = dict(zip(_SAFE_COLUMNS, row, strict=True))
        try:
            issued_at = datetime.fromisoformat(values["issued_at"])
            expires_at = datetime.fromisoformat(values["expires_at"])
        except (TypeError, ValueError) as exc:
            raise WordPressAuthorizationStoreError("invalid authorization timestamp") from exc
        if (issued_at.tzinfo is None or expires_at.tzinfo is None
                or issued_at >= expires_at):
            raise WordPressAuthorizationStoreError("invalid authorization timestamp")
        if type(values["authorization_id"]) is not str or not values["authorization_id"]:
            raise WordPressAuthorizationStoreError("invalid authorization identity")
        if type(values["mutation_id"]) is not str or values["mutation_id"] != MUTATION_ID:
            raise WordPressAuthorizationStoreError("invalid mutation identity")
        if (type(values["production_authority"]) is not int
                or values["production_authority"] != 0
                or type(values["ubuntu_authority"]) is not int
                or values["ubuntu_authority"] != 0):
            raise WordPressAuthorizationStoreError("invalid authority scope")
        expired = expires_at <= now
        state = values["state"]
        reported_state = "EXPIRED_AVAILABLE" if state == "AVAILABLE" and expired else state
        projected.append({
            "authorization_id": values["authorization_id"],
            "state": reported_state,
            "issued_at": values["issued_at"],
            "expires_at": values["expires_at"],
            "expired": expired,
            "mutation_id": values["mutation_id"],
            "production_authority": False,
            "ubuntu_authority": False,
        })
    return {
        "authorizations": projected,
        "state": "NO_ROWS" if not projected else "OBSERVED",
    }


def inspect_authorizations() -> dict[str, object]:
    """Return safe metadata from the sole fixed authorization store."""
    home = resolve_trusted_mac_account_home()
    owner = issue_trusted_ownership_expectation(home)
    path = Path(home.passwd_home).joinpath(*_COMPONENTS)
    return _inspect_fixed_path(
        path, uid=owner.expected_uid, gid=owner.expected_gid,
    )


def main():
    try:
        print(json.dumps(inspect_authorizations(), sort_keys=True, separators=(",", ":")))
        return 0
    except Exception:
        error = {
            "error": "WORDPRESS_AUTHORIZATION_INSPECTION_FAILED",
            "production_authority": False,
            "ubuntu_authority": False,
        }
        print(json.dumps(error, sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return 1


__all__ = ("inspect_authorizations", "main")

if __name__ == "__main__":
    raise SystemExit(main())

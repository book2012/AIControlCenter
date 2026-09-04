"""Interactive issuer for the one fixed non-production WordPress mutation."""
from __future__ import annotations
import json, sys, uuid
from datetime import datetime, timedelta, timezone
from core.secrets.mariadb_continuity_trusted_mac_account_home_runtime_resolver import resolve_trusted_mac_account_home
from core.secrets.mariadb_continuity_trusted_ownership_expectation import issue_trusted_ownership_expectation
from core.shopping.wordpress_port_authorization import WordPressMutationAuthorization, immutable_contract
from ops.macos.shopping.wordpress_port_authorization_store import WordPressPortAuthorizationStore

ACKNOWLEDGEMENT="AUTHORIZE SHOP-SERVICE-START-01B:WORDPRESS_PORT_58081_TO_58082"
EXPIRY_MINUTES=10

def issue() -> dict[str, object]:
    if not sys.stdin.isatty() or not sys.stdout.isatty(): raise RuntimeError("interactive stdin/stdout TTY required")
    home=resolve_trusted_mac_account_home(); owner=issue_trusted_ownership_expectation(home)
    contract=immutable_contract(uid=owner.expected_uid,gid=owner.expected_gid)
    print(json.dumps(contract,sort_keys=True))
    if input(f"Type exactly: {ACKNOWLEDGEMENT}\n> ") != ACKNOWLEDGEMENT: raise RuntimeError("exact human acknowledgement required")
    issued=datetime.now(timezone.utc); values={**contract,"authorization_id":str(uuid.uuid4()),"issued_at":issued.isoformat(),"expires_at":(issued+timedelta(minutes=EXPIRY_MINUTES)).isoformat()}
    authorization=object.__new__(WordPressMutationAuthorization)
    for name in WordPressMutationAuthorization.__dataclass_fields__: object.__setattr__(authorization,name,values[name])
    WordPressPortAuthorizationStore._initialize_for_issuer()._issue(authorization)
    return {"authorization_id":authorization.authorization_id,"issued_at":authorization.issued_at,"expires_at":authorization.expires_at,"state":"AVAILABLE","production_authority":False,"ubuntu_authority":False}

def main() -> int:
    try: print(json.dumps(issue(),sort_keys=True)); return 0
    except Exception as exc:
        print(json.dumps({"state":"DENIED","reason":str(exc),"production_authority":False,"ubuntu_authority":False}),file=sys.stderr); return 1

if __name__=="__main__": raise SystemExit(main())
__all__=("issue","main")

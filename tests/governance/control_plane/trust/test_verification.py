from copy import deepcopy
from datetime import timedelta
import hashlib
import pytest
from core.governance.control_plane.trust.canonical import canonicalize
from core.governance.control_plane.trust.models import VerificationError
from core.governance.control_plane.trust.verification import decode_base64url, parse_registry, verify_authorization_envelope
from tests.governance.control_plane.trust.fixtures.factory import NOW, material

def redigest(registry):
 body={key:value for key,value in registry.items() if key!="registry_digest"}
 registry["registry_digest"]="sha256:"+hashlib.sha256(canonicalize(body)).hexdigest()

def test_valid_canonical_artifact_verifies():
 _,_,_,encode=material(); raw,registry=encode(); assert verify_authorization_envelope(raw,registry,now=NOW).key_id=="key-1"
def test_canonical_base64url_enforced():
 with pytest.raises(VerificationError): decode_base64url("AA==",1,"value")
@pytest.mark.parametrize("change",["algorithm","signature","unknown","revoked","key_expired","artifact_expired","digest"])
def test_verification_denials(change):
 _,p,r,encode=material(); p=deepcopy(p); r=deepcopy(r)
 if change=="algorithm": p["algorithm"]="RSA"
 elif change=="signature":
  raw,reg=encode(); envelope=__import__('json').loads(raw); envelope["signature"]="A"*86; raw=canonicalize(envelope)
  with pytest.raises(VerificationError): verify_authorization_envelope(raw,reg,now=NOW)
  return
 elif change=="unknown": p["key_id"]="missing"
 elif change=="revoked": r["issuers"][0]["status"]="REVOKED"
 elif change=="key_expired": r["issuers"][0]["not_after"]="2029-12-01T00:00:00Z"
 elif change=="artifact_expired": p["expires_at"]="2029-12-01T00:00:00Z"
 elif change=="digest": r["registry_digest"]="sha256:"+"0"*64
 if change in {"revoked","key_expired"}: redigest(r)
 raw,reg=encode(p,r)
 with pytest.raises(VerificationError): verify_authorization_envelope(raw,reg,now=NOW)
def test_registry_duplicate_and_malformed_rejected():
 with pytest.raises(VerificationError): parse_registry(b'{"a":1,"a":2}')
def test_duplicate_registry_key_id_rejected():
 _,_,registry,_=material(); registry=deepcopy(registry); registry["issuers"].append(deepcopy(registry["issuers"][0])); redigest(registry)
 with pytest.raises(VerificationError): parse_registry(canonicalize(registry))

@pytest.mark.parametrize("change", ["empty_version", "equal_interval", "reversed_interval"])
def test_registry_policy_states_rejected(change):
 _,_,registry,_=material(); registry=deepcopy(registry)
 if change == "empty_version": registry["registry_version"]=""; registry["issuers"][0]["registry_version"]=""
 elif change == "equal_interval": registry["issuers"][0]["not_after"]=registry["issuers"][0]["not_before"]
 else: registry["issuers"][0]["not_after"]="2028-01-01T00:00:00Z"
 redigest(registry)
 with pytest.raises(VerificationError): parse_registry(canonicalize(registry))

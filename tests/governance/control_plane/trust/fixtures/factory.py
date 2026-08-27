from __future__ import annotations
import base64, hashlib
from datetime import datetime, timezone
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from core.governance.control_plane.trust.canonical import canonicalize
from core.governance.control_plane.trust.verification import DOMAIN_SEPARATOR

NOW = datetime(2030,1,1,tzinfo=timezone.utc)
def b64(value: bytes) -> str: return base64.urlsafe_b64encode(value).rstrip(b"=").decode()
def material():
 key=Ed25519PrivateKey.generate(); public=b64(key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw))
 identity=lambda i,t:{"identity_id":i,"identity_type":t}
 request={"schema_version":"governance/v1","request_id":"req-1","lifecycle_id":"life-1","requester":identity("requester","HUMAN"),"operation_type":"SHOP:UPDATE","target":"product-1","environment":"Production","reason":"approved change","requested_scope":["SHOP:UPDATE"],"requested_mutation_budget_id":"budget-1","requested_at":"2029-12-31T23:00:00Z"}
 decision={"schema_version":"governance/v1","decision_id":"decision-1","request_id":"req-1","approver":identity("approver","HUMAN"),"decision":"APPROVED","reason_codes":["APPROVED_CHANGE"],"decided_at":"2029-12-31T23:10:00Z","expiry":"2030-01-01T01:00:00Z","approved_scope":["SHOP:UPDATE"],"approved_mutation_budget_id":"budget-1","precondition_snapshot_digest":"sha256:precondition"}
 receipt={"schema_version":"governance/v1","authorization_id":"auth-1","request_id":"req-1","decision_id":"decision-1","lifecycle_id":"life-1","state":"AUTHORIZED","approved_scope":["SHOP:UPDATE"],"mutation_budget_id":"budget-1","precondition_snapshot_digest":"sha256:precondition","issued_at":"2029-12-31T23:10:00Z","expires_at":"2030-01-01T01:00:00Z"}
 line={"action_type":"SHOP:UPDATE","allowed_count":1,"actual_invocation_count":0,"completed_count":0,"uncertain_count":0,"remaining_count":1,"status":"AVAILABLE"}
 budget={"schema_version":"governance/v1","budget_id":"budget-1","authorization_id":"auth-1","status":"AVAILABLE","line_items":[line],"remaining_count":1,"violation_reason_code":None}
 execution={"schema_version":"governance/v1","execution_request_id":"exec-1","lifecycle_id":"life-1","authorization_id":"auth-1","claim_id":"claim-1","mutation_budget_id":"budget-1","action_type":"SHOP:UPDATE","target":"product-1","plan_digest":"sha256:plan","requested_at":"2029-12-31T23:20:00Z"}
 protected={"envelope_version":"governance-signed-authorization-envelope/v1","key_id":"key-1","issuer_id":"issuer-1","algorithm":"Ed25519","authorization_request":request,"authorization_decision":decision,"authorization_receipt":receipt,"mutation_budget":budget,"execution_intent":execution,"expected_operator":identity("operator","MAC_LOCAL_OPERATOR_V1"),"lifecycle_id":"life-1","request_id":"req-1","decision_id":"decision-1","authorization_id":"auth-1","mutation_budget_id":"budget-1","execution_request_id":"exec-1","claim_id":"claim-1","action_type":"SHOP:UPDATE","target":"product-1","plan_digest":"sha256:plan","expected_precondition_snapshot_digest":"sha256:precondition","approved_scope":["SHOP:UPDATE"],"expires_at":"2030-01-01T01:00:00Z","allowed_invocation_count":1}
 issuer={"schema_version":"governance-trusted-issuer-registry/v1","registry_version":"1","key_id":"key-1","issuer_id":"issuer-1","issuer_type":"HUMAN_AUTHORITY","public_key":public,"algorithm":"Ed25519","status":"ACTIVE","not_before":"2029-01-01T00:00:00Z","not_after":"2031-01-01T00:00:00Z","revocation_effective_at":None}
 body={"schema_version":"governance-trusted-issuer-registry/v1","registry_version":"1","issuers":[issuer]}; registry=dict(body,registry_digest="sha256:"+hashlib.sha256(canonicalize(body)).hexdigest())
 def encode(p=protected, reg=registry):
  signature=b64(key.sign(DOMAIN_SEPARATOR+b"\0"+canonicalize(p)))
  return canonicalize({"protected":p,"signature":signature}),canonicalize(reg)
 return key,protected,registry,encode

from copy import deepcopy
import pytest
from core.governance.control_plane.domain.identity import GovernanceIdentity
from core.governance.control_plane.ports.authorization_consumption import AuthorizationConsumptionCommand
from core.governance.control_plane.trust.intake import _intake_trusted_authorization, intake_trusted_authorization
from core.governance.control_plane.trust.models import IntakeError, TrustError, VerifiedAuthorizationEvidence
from core.governance.control_plane.trust.operator_identity import ObservedMacOperator
from core.governance.control_plane.trust.verification import verify_authorization_envelope
from tests.governance.control_plane.trust.fixtures.factory import NOW, material
class Observer:
 def observe(self): return ObservedMacOperator(501,20,"operator","/Users/operator",GovernanceIdentity("operator","MAC_LOCAL_OPERATOR_V1"))
def intake(p=None):
 _,original,r,encode=material(); raw,registry=encode(p or original,r)
 return _intake_trusted_authorization(raw,registry_reader=lambda: registry,clock=lambda: NOW,operator_observer=Observer())
def test_verified_intake_reconstructs_without_consume_or_invoke():
 facts=intake(); assert facts.authorization.state.value=="AUTHORIZED"; assert facts.mutation_budget.status.value=="AVAILABLE"
 assert not hasattr(facts,"consume_once") and not hasattr(facts,"execute") and not hasattr(facts,"invoke_once")
def test_consumption_command_compatibility_without_consuming():
 facts=intake(); command=AuthorizationConsumptionCommand(facts.authorization,facts.mutation_budget,facts.execution_request)
 assert command.execution_request.action_type=="SHOP:UPDATE"
def test_manufactured_evidence_cannot_enter_public_intake():
 fake=VerifiedAuthorizationEvidence({},"key-1","issuer-1","sha256:"+"0"*64,NOW)
 with pytest.raises((TypeError, ValueError)):
  intake_trusted_authorization(fake)
def test_parse_only_grants_zero_authority():
 from core.governance.control_plane.trust.verification import parse_authorization_envelope
 _,_,_,encode=material(); raw,_=encode(); parsed=parse_authorization_envelope(raw); assert not hasattr(parsed,"invoke_once") and not hasattr(parsed,"consume_once")
def test_verify_only_grants_zero_authority():
 _,_,_,encode=material(); raw,registry=encode(); verified=verify_authorization_envelope(raw,registry,now=NOW)
 assert not hasattr(verified,"invoke_once") and not hasattr(verified,"consume_once") and not hasattr(verified,"execute")
def test_action_outside_approved_scope_rejected_before_facts_returned():
 _,p,_,_=material(); p=deepcopy(p)
 p["authorization_request"]["requested_scope"].append("SHOP:READ")
 p["approved_scope"]=["SHOP:READ"]
 p["authorization_decision"]["approved_scope"]=["SHOP:READ"]
 p["authorization_receipt"]["approved_scope"]=["SHOP:READ"]
 with pytest.raises(IntakeError): intake(p)
@pytest.mark.parametrize("field",["lifecycle_id","request_id","decision_id","authorization_id","mutation_budget_id","execution_request_id","claim_id","action_type","target","plan_digest","expected_precondition_snapshot_digest","approved_scope","expires_at","allowed_invocation_count"])
def test_each_important_binding_mismatch_rejected(field):
 _,p,_,_=material(); p=deepcopy(p); p[field]=["other"] if field=="approved_scope" else (2 if field=="allowed_invocation_count" else "other")
 with pytest.raises(TrustError): intake(p)
@pytest.mark.parametrize("pair", ["requester_approver","requester_operator","approver_operator"])
def test_identity_collisions_rejected(pair):
 _,p,_,_=material(); p=deepcopy(p)
 if pair=="requester_approver": p["authorization_decision"]["approver"]=p["authorization_request"]["requester"]
 elif pair=="requester_operator": p["authorization_request"]["requester"]=p["expected_operator"]
 else: p["authorization_decision"]["approver"]=p["expected_operator"]
 with pytest.raises(IntakeError): intake(p)
@pytest.mark.parametrize("mutation",["multiple","count","invoked"])
def test_single_pristine_mutation_budget_required(mutation):
 _,p,_,_=material(); p=deepcopy(p); line=p["mutation_budget"]["line_items"][0]
 if mutation=="multiple": p["mutation_budget"]["line_items"].append(dict(line,action_type="SHOP:DELETE"))
 elif mutation=="count": line["allowed_count"]=2; line["remaining_count"]=2; p["mutation_budget"]["remaining_count"]=2; p["allowed_invocation_count"]=2
 else: line.update(actual_invocation_count=1,completed_count=1,remaining_count=0,status="EXHAUSTED"); p["mutation_budget"].update(status="EXHAUSTED",remaining_count=0)
 with pytest.raises(IntakeError): intake(p)

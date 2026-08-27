import pytest
from core.governance.control_plane.domain.identity import GovernanceIdentity
from core.governance.control_plane.trust.models import OperatorIdentityError
from core.governance.control_plane.trust.operator_identity import ObservedMacOperator, ProductionMacOperatorObserver, observe_operator
class Observer:
 def __init__(self,value): self.value=value
 def observe(self): return self.value
def test_production_observer_has_no_caller_identity_parameters():
 import inspect
 assert tuple(inspect.signature(ProductionMacOperatorObserver.observe).parameters) == ("self",)
def test_ambiguity_rejected():
 with pytest.raises(OperatorIdentityError): observe_operator(Observer(None))
def test_root_rejected():
 value=ObservedMacOperator(0,0,"root","/var/root",GovernanceIdentity("root","MAC_LOCAL_OPERATOR_V1"))
 with pytest.raises(OperatorIdentityError): observe_operator(Observer(value))

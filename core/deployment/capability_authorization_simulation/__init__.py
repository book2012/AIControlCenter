"""M4-A3 deterministic test-only authorization simulation surface."""

from .artifact_factory import TestOnlyArtifactFactory, stable_id
from .models import *
from .replay import InMemoryTestOnlyReplayGuard
from .reporting import emit_json_report
from .simulator import TestOnlyAuthorizationSimulator
from .validation import (
    reject_at_operational_boundary, validate_bindings, validate_config,
    validate_evidence_chain, validate_request,
)

__all__ = tuple(name for name in globals() if name.startswith("TestOnly") or name in {
    "BASELINE_COMMIT", "BRANCH", "M3_BINDING", "M4_A1_BINDING", "M4_A2_BINDING",
    "SCHEMA_VERSION", "TASK", "TEST_NAMESPACE", "TEST_SOURCE",
    "InMemoryTestOnlyReplayGuard", "emit_json_report", "reject_at_operational_boundary",
    "stable_id", "validate_bindings", "validate_config", "validate_evidence_chain",
    "validate_request",
})

for _name, _value in tuple(globals().items()):
    if _name.startswith("TestOnly") and isinstance(_value, type):
        _value.__test__ = False

from pathlib import Path
import inspect
import pytest
import core.governance.control_plane.trust as public_trust
from core.governance.control_plane.trust.intake import intake_trusted_authorization
from core.governance.control_plane.trust.models import VerificationError
from tests.governance.control_plane.trust.fixtures.factory import material


TRUST = Path("core/governance/control_plane/trust")


def _production_source():
    return "\n".join(path.read_text() for path in TRUST.glob("*.py"))


def test_production_trust_has_no_private_signing_api():
    source=_production_source()
    assert "Ed25519PrivateKey" not in source and ".sign(" not in source


def test_no_generic_executor_or_external_authority_introduced():
    source=_production_source().lower()
    assert "ubuntu" not in source and "wu09" not in source
    assert "genericexecutor" not in source and "generic_executor" not in source

def test_public_production_intake_is_raw_envelope_only():
    assert tuple(inspect.signature(intake_trusted_authorization).parameters) == ("raw_envelope",)
    assert "reconstruct_trusted_facts" not in public_trust.__all__

def test_caller_created_registry_cannot_be_supplied_to_production_intake():
    _,_,_,encode=material(); raw, caller_registry=encode()
    with pytest.raises(TypeError): intake_trusted_authorization(raw, caller_registry)

@pytest.mark.parametrize(
    "authority_argument",
    ["registry_raw", "registry_path", "platform", "HOME", "uid", "gid"],
)
def test_production_intake_rejects_caller_authority_arguments(authority_argument):
    _,_,_,encode=material(); raw,_=encode()
    with pytest.raises(TypeError):
        intake_trusted_authorization(raw, **{authority_argument: object()})

def test_production_intake_internally_sources_registry(monkeypatch):
    _,_,_,encode=material(); raw,_=encode(); calls=[]
    sentinel_registry = b"test-only sentinel registry"
    def registry_reader():
        calls.append("registry")
        return sentinel_registry
    def verifier(raw_envelope, registry_raw, *, now):
        calls.append(("verify", raw_envelope, registry_raw))
        raise VerificationError("test-only verifier termination")
    monkeypatch.setattr("core.governance.control_plane.trust.intake.read_trust_registry", registry_reader)
    monkeypatch.setattr("core.governance.control_plane.trust.intake.verify_authorization_envelope", verifier)
    with pytest.raises(VerificationError, match="test-only verifier termination"):
        intake_trusted_authorization(raw)
    assert calls == ["registry", ("verify", raw, sentinel_registry)]

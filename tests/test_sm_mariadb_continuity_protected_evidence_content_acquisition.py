import copy
import json
import pickle

import pytest

from core.secrets.mariadb_continuity_protected_evidence_content_acquisition import ProtectedEvidenceContent, ProtectedEvidenceContentAcquisitionResult, _acquired_content


def test_content_is_opaque_noncopyable_nonserializable_and_repr_safe():
    secret = b"uniquely-sensitive-content"
    value = _acquired_content(secret)
    assert secret.decode() not in repr(value)
    with pytest.raises(TypeError):
        copy.copy(value)
    with pytest.raises(TypeError):
        copy.deepcopy(value)
    with pytest.raises(TypeError):
        pickle.dumps(value)
    with pytest.raises(TypeError):
        json.dumps(value)
    with pytest.raises(TypeError):
        hash(value)
    with pytest.raises(TypeError):
        ProtectedEvidenceContent()


def test_success_is_only_stable_binding_and_never_promotion():
    result = ProtectedEvidenceContentAcquisitionResult(_acquired_content(b"x"))
    assert result.content_acquired_from_stable_binding is True
    assert all(getattr(result, name) is False for name in ("evidence_admitted", "evidence_verified", "provenance_valid", "integrity_valid", "trusted_issuer", "recover_evidence_sufficient", "production_validation_ready", "production_authorization", "execution_authority"))

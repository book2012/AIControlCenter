from datetime import timedelta
from unittest.mock import Mock
import pytest
from pydantic import SecretBytes
from core.api.dependencies.customer_session import CustomerSessionBoundary
from core.shopping.customer_session_service import CustomerSessionService,SessionValidationCode
from test_shop_ai_001b3_session_api import api,clients,issue,COOKIE_NAME,SECRET,CSRF_KEY,NOW,ORIGIN,SECOND_PAYLOAD

def restarted(api):
    return CustomerSessionBoundary(service=api.real,trusted_origin=ORIGIN,csrf_key=CSRF_KEY,
        clock=lambda:api.time.now,recover_durable_bindings=True)

def test_explicit_recovery_keeps_exact_identity_csrf_and_current_checks(api,clients):
    original=issue(api);boundary=restarted(api);client=clients(boundary)
    response=client.get('/shopping/auth/session',headers={'Cookie':COOKIE_NAME+'='+SECRET})
    assert response.status_code==200 and response.json()==original.json()
    assert response.headers['X-CSRF-Token']==original.headers['X-CSRF-Token']
    api.time.now+=timedelta(minutes=30)
    assert client.get('/shopping/auth/session',headers={'Cookie':COOKIE_NAME+'='+SECRET}).status_code==401

def test_recovery_denies_revoked_customer_session(api,clients):
    issue(api)
    projection=api.boundary.authenticate(SECRET,now=api.time.now)
    api.boundary.revoke(SECRET,projection,now=api.time.now)
    assert clients(restarted(api)).get('/shopping/auth/session',headers={'Cookie':COOKIE_NAME+'='+SECRET}).status_code==401

def test_recovery_does_not_create_missing_schema_or_accept_unknown_secret(tmp_path):
    path=tmp_path/'absent.sqlite3';service=CustomerSessionService(str(path))
    assert service.validate_credential_session(SECRET,now=NOW).code==SessionValidationCode.MISSING
    assert not path.exists()

def test_recovery_rejects_duplicate_credential_binding(api,clients):
    issue(api);api.real._secret_factory=lambda:SECRET;api.client.cookies.clear()
    # Issuance persists first; the original bounded process index then denies collision.
    response=api.client.post('/shopping/auth/session',json=SECOND_PAYLOAD,headers={'Origin':ORIGIN})
    assert response.status_code==503
    assert clients(restarted(api)).get('/shopping/auth/session',headers={'Cookie':COOKIE_NAME+'='+SECRET}).status_code==401

def test_recovery_mode_is_explicit_boolean():
    with pytest.raises(ValueError):CustomerSessionBoundary(service=Mock(),trusted_origin=ORIGIN,csrf_key=CSRF_KEY,
        clock=lambda:NOW,recover_durable_bindings='true')

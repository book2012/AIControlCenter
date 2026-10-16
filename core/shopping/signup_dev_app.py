"""Explicitly isolated DEV-only signup HTTP composition.

The factory requires a DEV root, opt-in flag, injected DEV test doubles, and a
database contained under that root. It is never imported by core.api.app.
"""
from __future__ import annotations

from pathlib import Path
import secrets

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, SecretStr

from core.shopping.account_registration import SignupCandidate
from core.shopping.signup_email_and_claim import (
    SignupEmailVerificationService, TwoContactSignupClaimService,
)
from core.shopping.signup_registration_operation import SignupRegistrationOperationService
from core.shopping.signup_verification import SignupPhoneVerificationService, SQLiteSignupVerificationStore


DEV_ORIGIN = "https://dev.bokstory.duckdns.org"
DEV_PRIVACY_NOTICE_VERSION = "privacy-dev-001"
_COOKIE = "aicc_signup_dev_session"


class _Body(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class _PhoneStart(_Body):
    phone: str = Field(strict=True, min_length=13, max_length=13)


class _PhoneConfirm(_Body):
    challenge: str = Field(strict=True, min_length=1, max_length=128, repr=False)
    phone: str = Field(strict=True, min_length=13, max_length=13)
    code: str = Field(strict=True, min_length=4, max_length=4, pattern=r"^[0-9]{4}$", repr=False)


class _EmailStart(_Body):
    email: str = Field(strict=True, min_length=3, max_length=254)


class _EmailConfirm(_Body):
    challenge: str = Field(strict=True, min_length=1, max_length=128, repr=False)
    email: str = Field(strict=True, min_length=3, max_length=254)
    code: str = Field(strict=True, min_length=6, max_length=6, pattern=r"^[0-9]{6}$", repr=False)


class _PrivacyConsent(_Body):
    accepted: bool = Field(strict=True)


class _Signup(_Body):
    login_id: str = Field(strict=True, min_length=4, max_length=20)
    email: str = Field(strict=True, min_length=3, max_length=254)
    password: SecretStr = Field(min_length=8, max_length=128, repr=False)
    password_confirmation: SecretStr = Field(min_length=8, max_length=128, repr=False)
    phone: str = Field(strict=True, min_length=13, max_length=13)
    terms_accepted: bool = Field(strict=True)
    terms_version: str = Field(strict=True, min_length=1, max_length=64)
    phone_ticket: str = Field(strict=True, min_length=1, max_length=128, repr=False)
    email_ticket: str = Field(strict=True, min_length=1, max_length=128, repr=False)
    idempotency_key: str = Field(strict=True, min_length=16, max_length=128, repr=False)


def _test_double(value: object) -> bool:
    return getattr(value, "environment", None) == "DEV" and getattr(value, "is_test_double", None) is True


def create_signup_dev_app(
    *,
    environment: str,
    enable_dev_signup: bool,
    dev_data_root: str | Path,
    store: SQLiteSignupVerificationStore,
    phone_service: SignupPhoneVerificationService,
    email_service: SignupEmailVerificationService,
    claim_service: TwoContactSignupClaimService,
    operation_service: SignupRegistrationOperationService,
) -> FastAPI:
    """Build an unmounted test-only API; it cannot compose production adapters."""
    if environment != "DEV" or enable_dev_signup is not True:
        raise ValueError("DEV_SIGNUP_EXPLICIT_OPT_IN_REQUIRED")
    root = Path(dev_data_root)
    if root.is_symlink():
        raise ValueError("DEV_SIGNUP_ROOT_INVALID")
    root = root.resolve()
    if any(part.lower() in {"prod", "production"} for part in root.parts):
        raise ValueError("DEV_SIGNUP_ROOT_INVALID")
    db_path = store.path.resolve()
    if not db_path.is_relative_to(root):
        raise ValueError("DEV_SIGNUP_DATABASE_OUTSIDE_ROOT")
    if any(part.lower() in {"prod", "production"} for part in db_path.parts):
        raise ValueError("DEV_SIGNUP_DATABASE_OUTSIDE_ROOT")
    if any(service.store is not store for service in
           (phone_service, email_service, claim_service, operation_service)):
        raise ValueError("DEV_SIGNUP_STORE_MISMATCH")
    if not _test_double(phone_service.provider) or not _test_double(email_service.provider):
        raise ValueError("DEV_SIGNUP_TEST_PROVIDERS_REQUIRED")
    if not _test_double(operation_service.port):
        raise ValueError("DEV_SIGNUP_TEST_CUSTOMER_PORT_REQUIRED")

    email_service.initialize()
    operation_service.initialize()
    app = FastAPI(title="Agachichi isolated DEV signup", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.environment = "DEV"
    app.state.signup_enabled = True
    app.state.signup_store = store

    def response(payload: dict, status_code: int = 200) -> JSONResponse:
        return JSONResponse(payload, status_code=status_code, headers={
            "Cache-Control": "no-store, private, max-age=0",
            "Pragma": "no-cache",
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
        })

    @app.middleware("http")
    async def boundary(request: Request, call_next):
        origin = request.headers.get("origin")
        host = request.headers.get("host", "").split(":", 1)[0].lower()
        peer = request.client.host if request.client else ""
        # This factory is only for Starlette TestClient. A real Uvicorn
        # socket, including loopback behind Caddy, must fail closed.
        test_client_peer = peer == "testclient"
        if origin != DEV_ORIGIN or host != "dev.bokstory.duckdns.org" or not test_client_peer:
            return response({"state": "NOT_COMPLETED"}, 403)
        session = request.cookies.get(_COOKIE)
        issue_cookie = not session or len(session) < 32 or len(session) > 128
        if issue_cookie:
            session = secrets.token_urlsafe(32)
        request.state.signup_session = session
        result = await call_next(request)
        if issue_cookie:
            result.set_cookie(
                _COOKIE, session, secure=True, httponly=True,
                samesite="strict", path="/v1/shop/signup", max_age=3600,
            )
        result.headers["Cache-Control"] = "no-store, private, max-age=0"
        result.headers["Pragma"] = "no-cache"
        result.headers["Referrer-Policy"] = "no-referrer"
        result.headers["X-Content-Type-Options"] = "nosniff"
        return result

    async def bounded_model(request: Request, model: type[BaseModel], limit: int):
        raw = bytearray()
        async for chunk in request.stream():
            if len(raw) + len(chunk) > limit:
                return None
            raw.extend(chunk)
        try:
            return model.model_validate_json(bytes(raw))
        except Exception:
            return None

    @app.get("/v1/shop/signup/session")
    async def signup_session():
        return response({"state": "READY"})

    @app.get("/v1/shop/signup/privacy-notice")
    async def privacy_notice():
        return response({
            "version": DEV_PRIVACY_NOTICE_VERSION,
            "required_items": ["아이디", "이메일 주소", "휴대전화번호", "비밀번호"],
            "purpose": "DEV 테스트 계정 생성, 로그인, 연락처 확인 및 계정 보안 흐름 검증",
            "retention": "테스트 요청 종료 후 테스트 저장소에서 제거; 실제 고객정보로 시험하지 않음",
            "refusal": "동의를 거부할 수 있으며, 거부하면 가입 테스트를 진행할 수 없음",
            "provider_scope": "가상 테스트 제공자만 사용하며 실제 SMS·이메일은 발송하지 않음",
        })

    @app.post("/v1/shop/signup/privacy-consent")
    async def privacy_consent(request: Request):
        data = await bounded_model(request, _PrivacyConsent, 512)
        if data is None:
            return response({"state": "NOT_ACCEPTED"}, 422)
        state = claim_service.record_privacy_consent(
            session_ref=request.state.signup_session,
            notice_version=DEV_PRIVACY_NOTICE_VERSION,
            accepted=data.accepted,
        )
        return response({"state": state}, 200 if state == "ACCEPTED" else 422)

    @app.post("/v1/shop/signup/phone-challenge")
    async def phone_challenge(request: Request):
        data = await bounded_model(request, _PhoneStart, 1024)
        if data is None:
            return response({"state": "NOT_STARTED"}, 422)
        if not claim_service.has_privacy_consent(
            session_ref=request.state.signup_session, notice_version=DEV_PRIVACY_NOTICE_VERSION,
        ):
            return response({"state": "CONSENT_REQUIRED"}, 403)
        result = phone_service.start_phone(
            data.phone, session_ref=request.state.signup_session, client_ref="127.0.0.1",
        )
        return response({"state": result.state, "challenge": result.challenge})

    @app.post("/v1/shop/signup/phone-confirm")
    async def phone_confirm(request: Request):
        data = await bounded_model(request, _PhoneConfirm, 1024)
        if data is None:
            return response({"state": "NOT_VERIFIED"}, 422)
        if not claim_service.has_privacy_consent(
            session_ref=request.state.signup_session, notice_version=DEV_PRIVACY_NOTICE_VERSION,
        ):
            return response({"state": "CONSENT_REQUIRED"}, 403)
        result = phone_service.confirm_phone(
            data.challenge, data.phone, data.code, session_ref=request.state.signup_session,
        )
        return response({"state": result.state, "ticket": result.ticket})

    @app.post("/v1/shop/signup/email-challenge")
    async def email_challenge(request: Request):
        data = await bounded_model(request, _EmailStart, 1024)
        if data is None:
            return response({"state": "NOT_STARTED"}, 422)
        if not claim_service.has_privacy_consent(
            session_ref=request.state.signup_session, notice_version=DEV_PRIVACY_NOTICE_VERSION,
        ):
            return response({"state": "CONSENT_REQUIRED"}, 403)
        result = email_service.start_email(
            data.email, session_ref=request.state.signup_session, client_ref="127.0.0.1",
        )
        return response({"state": result.state, "challenge": result.challenge})

    @app.post("/v1/shop/signup/email-confirm")
    async def email_confirm(request: Request):
        data = await bounded_model(request, _EmailConfirm, 1024)
        if data is None:
            return response({"state": "NOT_VERIFIED"}, 422)
        if not claim_service.has_privacy_consent(
            session_ref=request.state.signup_session, notice_version=DEV_PRIVACY_NOTICE_VERSION,
        ):
            return response({"state": "CONSENT_REQUIRED"}, 403)
        result = email_service.confirm_email(
            data.challenge, data.email, data.code, session_ref=request.state.signup_session,
        )
        return response({"state": result.state, "ticket": result.ticket})

    @app.post("/v1/shop/signup/complete")
    async def complete(request: Request):
        data = await bounded_model(request, _Signup, 4096)
        if data is None:
            return response({"state": "NOT_COMPLETED"}, 422)
        candidate = SignupCandidate(
            login_id=data.login_id, email=data.email,
            password=data.password.get_secret_value(),
            password_confirmation=data.password_confirmation.get_secret_value(),
            phone=data.phone, terms_accepted=data.terms_accepted,
            privacy_accepted=True,
            terms_version=data.terms_version,
            privacy_notice_version=DEV_PRIVACY_NOTICE_VERSION,
        )
        claim = claim_service.claim(
            phone_ticket=data.phone_ticket, email_ticket=data.email_ticket,
            session_ref=request.state.signup_session, idempotency_key=data.idempotency_key,
            candidate=candidate,
        )
        if claim.state != "CLAIMED" or not claim.claim_ref:
            return response({"state": "NOT_COMPLETED"})
        operation = operation_service.execute(claim_ref=claim.claim_ref, candidate=candidate)
        return response({"state": operation.state if operation.state in {"ACTIVE", "UNKNOWN_OUTCOME"}
                         else "NOT_COMPLETED"})

    return app


__all__ = ["DEV_ORIGIN", "create_signup_dev_app"]

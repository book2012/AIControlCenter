"""Explicitly mounted DEV account-recovery HTTP boundary."""
from __future__ import annotations

import ipaddress
from typing import Annotated

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, SecretStr

from core.shopping.account_recovery import AccountRecoveryService


class _Input(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class IdChallenge(_Input):
    name: str = Field(strict=True, min_length=1, max_length=100)
    phone: str = Field(strict=True, min_length=13, max_length=13, pattern=r"^\+8210[0-9]{8}$")


class IdConfirm(_Input):
    challenge: str = Field(strict=True, min_length=32, max_length=128, repr=False)
    phone: str = Field(strict=True, min_length=13, max_length=13, pattern=r"^\+8210[0-9]{8}$")
    code: str = Field(strict=True, min_length=4, max_length=10, pattern=r"^[0-9]+$", repr=False)


class PasswordResetRequest(_Input):
    login_id: str = Field(strict=True, min_length=1, max_length=100)
    name: str = Field(strict=True, min_length=1, max_length=100)
    phone: str = Field(strict=True, min_length=13, max_length=13, pattern=r"^\+8210[0-9]{8}$")


class PasswordResetComplete(_Input):
    token: str = Field(strict=True, min_length=32, max_length=128, repr=False)
    new_password: SecretStr = Field(min_length=8, max_length=128, repr=False)


def account_recovery_router(service: AccountRecoveryService, *, trusted_origin: str) -> APIRouter:
    if trusted_origin != "https://dev.bokstory.duckdns.org":
        raise ValueError("DEV_RECOVERY_ORIGIN_REQUIRED")
    router = APIRouter(prefix="/v1/shop/account-recovery", tags=["account-recovery"])

    def guard(request: Request) -> str | None:
        if request.headers.get("origin") != trusted_origin:
            return None
        peer = request.client.host if request.client else ""
        # This DEV service is reachable only through local Caddy. Never trust
        # an arbitrary X-Forwarded-For supplied by a direct client.
        if peer not in {"127.0.0.1", "::1", "testclient"}:
            return None
        chain = request.headers.get("x-forwarded-for", "").split(",")
        candidate = chain[-1].strip() if chain and chain[-1].strip() else peer
        if candidate == "testclient":
            candidate = "127.0.0.1"
        try:
            return str(ipaddress.ip_address(candidate))
        except ValueError:
            return None

    async def bounded_body(request: Request, limit: int) -> bytes | None:
        raw = bytearray()
        async for chunk in request.stream():
            if len(raw) + len(chunk) > limit:
                return None
            raw.extend(chunk)
        return bytes(raw)

    def response(body: dict, status: int = 200) -> JSONResponse:
        return JSONResponse(body, status_code=status, headers={
            "Cache-Control": "no-store, private, max-age=0",
            "Pragma": "no-cache",
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
        })

    @router.post("/id-challenge")
    async def id_challenge(request: Request):
        client = guard(request)
        if client is None:
            return response({"state": "ACKNOWLEDGED", "challenge": None}, 403)
        raw = await bounded_body(request, 2048)
        if raw is None:
            return response({"state": "ACKNOWLEDGED", "challenge": None}, 413)
        try:
            data = IdChallenge.model_validate_json(raw)
        except Exception:
            return response({"state": "ACKNOWLEDGED", "challenge": None}, 422)
        result = service.start_id_lookup(data.name, data.phone, client)
        return response({"state": result.state, "challenge": result.challenge})

    @router.post("/id-confirm")
    async def id_confirm(request: Request):
        client = guard(request)
        if client is None:
            return response({"state": "NOT_FOUND"}, 403)
        raw = await bounded_body(request, 2048)
        if raw is None:
            return response({"state": "NOT_FOUND"}, 413)
        try:
            data = IdConfirm.model_validate_json(raw)
        except Exception:
            return response({"state": "NOT_FOUND"}, 422)
        result = service.confirm_id_lookup(data.challenge, data.phone, data.code, client)
        if result.login_id is None:
            return response({"state": "NOT_FOUND"})
        return response({"state": "FOUND", "login_id": result.login_id})

    @router.post("/password-reset")
    async def password_reset(request: Request):
        client = guard(request)
        if client is None:
            return response({"state": "ACKNOWLEDGED"}, 403)
        raw = await bounded_body(request, 2048)
        if raw is None:
            return response({"state": "ACKNOWLEDGED"}, 413)
        try:
            data = PasswordResetRequest.model_validate_json(raw)
        except Exception:
            return response({"state": "ACKNOWLEDGED"}, 422)
        result = service.request_password_reset(data.login_id, data.name, data.phone, client)
        return response({"state": result.state})

    @router.post("/password-reset/complete")
    async def password_reset_complete(request: Request):
        client = guard(request)
        if client is None:
            return response({"state": "NOT_COMPLETED"}, 403)
        raw = await bounded_body(request, 4096)
        if raw is None:
            return response({"state": "NOT_COMPLETED"}, 413)
        try:
            data = PasswordResetComplete.model_validate_json(raw)
        except Exception:
            return response({"state": "NOT_COMPLETED"}, 422)
        result = service.complete_password_reset(data.token, data.new_password.get_secret_value())
        return response({"state": result.state})

    return router


def mount_account_recovery(app: FastAPI, service: AccountRecoveryService, *, trusted_origin: str) -> None:
    app.include_router(account_recovery_router(service, trusted_origin=trusted_origin))

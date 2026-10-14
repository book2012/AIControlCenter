"""Narrow DEV WordPress account-recovery data adapter.

The WordPress bridge accepts only a dedicated custom capability backed by a
separate DEV application-password identity. This adapter never uses WooCommerce
REST API keys and is inert until explicitly composed by a DEV runtime.
"""
from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlsplit

import requests
from pydantic import SecretStr

from core.shopping.account_recovery import RecoveryAccount


class WooRecoveryAdapterError(RuntimeError):
    """Sanitized bridge failure."""


class WooCommerceAccountRecoveryAdapter:
    _PATH = "/wp-json/aicc-account-recovery/v1"
    _MAX_RESPONSE = 32_768

    def __init__(
        self, *, base_url: str, service_username: str, application_password: SecretStr,
        session: Any | None = None,
    ) -> None:
        parsed = urlsplit(base_url)
        if (
            parsed.scheme != "https" or parsed.hostname != "dev.bokstory.duckdns.org"
            or parsed.port not in (None, 443) or parsed.path not in ("", "/")
            or parsed.query or parsed.fragment or parsed.username or parsed.password
        ):
            raise ValueError("DEV_RECOVERY_ORIGIN_REQUIRED")
        if (
            type(service_username) is not str
            or not re.fullmatch(r"[A-Za-z0-9_.-]{1,60}", service_username)
            or not isinstance(application_password, SecretStr)
            or not application_password.get_secret_value()
        ):
            raise ValueError("DEV_RECOVERY_CREDENTIALS_REQUIRED")
        self._base = base_url.rstrip("/") + self._PATH
        self._username = service_username
        self._password = application_password
        self._session = session if session is not None else requests.Session()
        if hasattr(self._session, "trust_env"):
            self._session.trust_env = False

    def __repr__(self) -> str:
        return "WooCommerceAccountRecoveryAdapter(environment='DEV', credentials=<redacted>)"

    @staticmethod
    def _account(document: object, *, name: str, phone: str) -> RecoveryAccount | None:
        if type(document) is not dict or type(document.get("match")) is not bool:
            raise WooRecoveryAdapterError("RECOVERY_BRIDGE_RESPONSE_INVALID")
        if document["match"] is False:
            if set(document) != {"match"}:
                raise WooRecoveryAdapterError("RECOVERY_BRIDGE_RESPONSE_INVALID")
            return None
        if set(document) != {"match", "account_ref", "login_id", "full_name", "phone"}:
            raise WooRecoveryAdapterError("RECOVERY_BRIDGE_RESPONSE_INVALID")
        account_ref = document["account_ref"]
        login_id = document["login_id"]
        full_name = document["full_name"]
        returned_phone = document["phone"]
        if (
            type(account_ref) is not str
            or not re.fullmatch(r"woo-customer:[1-9][0-9]{0,9}", account_ref)
            or type(login_id) is not str or not 1 <= len(login_id) <= 100
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", login_id)
            or type(full_name) is not str or full_name != name
            or returned_phone != phone
        ):
            raise WooRecoveryAdapterError("RECOVERY_BRIDGE_RESPONSE_INVALID")
        return RecoveryAccount(account_ref, login_id, full_name, returned_phone)

    @staticmethod
    def _json(response: Any) -> object:
        try:
            raw = bytearray()
            for chunk in response.iter_content(chunk_size=4096):
                if len(raw) + len(chunk) > WooCommerceAccountRecoveryAdapter._MAX_RESPONSE:
                    raise ValueError
                raw.extend(chunk)
            def no_duplicates(pairs):
                result = {}
                for key, value in pairs:
                    if key in result:
                        raise ValueError
                    result[key] = value
                return result
            return json.loads(bytes(raw).decode("utf-8"), object_pairs_hook=no_duplicates)
        except Exception:
            raise WooRecoveryAdapterError("RECOVERY_BRIDGE_RESPONSE_INVALID") from None
        finally:
            try:
                response.close()
            except Exception:
                pass

    def _post(self, endpoint: str, body: dict[str, str]) -> object:
        try:
            response = self._session.post(
                self._base + "/" + endpoint,
                json=body,
                auth=(self._username, self._password.get_secret_value()),
                headers={
                    "Accept": "application/json",
                    "Cache-Control": "no-store",
                    "Pragma": "no-cache",
                },
                timeout=10,
                allow_redirects=False,
                stream=True,
            )
            if response.status_code != 200:
                response.close()
                raise WooRecoveryAdapterError("RECOVERY_BRIDGE_UNAVAILABLE")
            cache_control = response.headers.get("Cache-Control", "").lower()
            if "no-store" not in cache_control:
                response.close()
                raise WooRecoveryAdapterError("RECOVERY_BRIDGE_RESPONSE_INVALID")
            return self._json(response)
        except WooRecoveryAdapterError:
            raise
        except Exception:
            raise WooRecoveryAdapterError("RECOVERY_BRIDGE_UNAVAILABLE") from None

    def find_by_name_phone(self, name: str, phone: str) -> RecoveryAccount | None:
        result = self._account(self._post("lookup-id", {"name": name, "phone": phone}),
                               name=name, phone=phone)
        return result

    def find_by_login_name_phone(
        self, login_id: str, name: str, phone: str,
    ) -> RecoveryAccount | None:
        return self._account(
            self._post("lookup-password", {"login_id": login_id, "name": name, "phone": phone}),
            name=name, phone=phone,
        )

    def find_by_ref_phone(self, account_ref: str, phone: str) -> RecoveryAccount | None:
        document = self._post("verify-account", {"account_ref": account_ref, "phone": phone})
        if type(document) is dict and document.get("match") is False and set(document) == {"match"}:
            return None
        if type(document) is not dict or set(document) != {
            "match", "account_ref", "login_id", "full_name", "phone",
        } or document.get("match") is not True or document.get("account_ref") != account_ref:
            raise WooRecoveryAdapterError("RECOVERY_BRIDGE_RESPONSE_INVALID")
        name = document.get("full_name")
        return self._account(document, name=name, phone=phone)

    def change_password(self, account_ref: str, new_password: str) -> bool:
        if (
            type(account_ref) is not str
            or not re.fullmatch(r"woo-customer:[1-9][0-9]{0,9}", account_ref)
            or type(new_password) is not str
            or not 8 <= len(new_password) <= 128
            or "\x00" in new_password
        ):
            return False
        try:
            result = self._post("change-password", {
                "account_ref": account_ref, "new_password": new_password,
            })
        except WooRecoveryAdapterError:
            raise
        if type(result) is not dict or set(result) != {"changed", "account_ref"}:
            raise WooRecoveryAdapterError("RECOVERY_BRIDGE_RESPONSE_INVALID")
        return result.get("changed") is True and result.get("account_ref") == account_ref


__all__ = ["WooCommerceAccountRecoveryAdapter", "WooRecoveryAdapterError"]

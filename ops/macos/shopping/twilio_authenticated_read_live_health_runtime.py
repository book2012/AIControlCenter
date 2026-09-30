from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import base64
import http.client
import json
import re
import ssl

from core.secrets.ports import (
    EphemeralSecretLease,
    SecretReference,
    SecretResolverPort,
)
from core.shopping.adapters.twilio_verify_read import (
    TWILIO_PROVIDER_SOURCE,
    normalize_service_response,
)
from core.shopping.governance.twilio_authenticated_read_authority import (
    TwilioAuthenticatedReadAuthority,
    TwilioAuthenticatedReadRequest,
)
from core.shopping.ports.provider_activation import (
    ProviderActivationState,
    ProviderOperation,
)
from core.shopping.ports.provider_authenticated_read import (
    ProviderReadResult,
)


TWILIO_VERIFY_HOST = "verify.twilio.com"
MAX_PROVIDER_RESPONSE_BYTES = 65536

_SERVICE_PATH_RE = re.compile(
    r"/v2/Services/VA[0-9A-Fa-f]{32}\Z"
)
_API_KEY_SID_RE = re.compile(
    rb"SK[0-9A-Fa-f]{32}\Z"
)


class TwilioLiveReadHealthError(RuntimeError):
    def __init__(self, reason_code: str) -> None:
        self._reason_code = str(reason_code)
        super().__init__(self._reason_code)

    @property
    def reason_code(self) -> str:
        return self._reason_code

    def __repr__(self) -> str:
        return (
            "TwilioLiveReadHealthError("
            f"reason_code={self._reason_code!r})"
        )


TwilioLiveHttpGet = Callable[
    [str, bytes, bytes],
    tuple[int, Mapping[str, object] | None],
]


def _secret_bytes(
    value: str | bytes,
) -> bytes:
    if type(value) is bytes:
        result = value
    elif type(value) is str:
        result = value.encode("utf-8")
    else:
        raise TwilioLiveReadHealthError(
            "SECRET_VALUE_TYPE_REJECTED"
        )

    if not result or len(result) > 4096:
        raise TwilioLiveReadHealthError(
            "SECRET_VALUE_REJECTED"
        )

    return result


def _twilio_https_get_once(
    path: str,
    api_key_sid: bytes,
    api_key_secret: bytes,
) -> tuple[
    int,
    Mapping[str, object] | None,
]:
    if (
        type(path) is not str
        or _SERVICE_PATH_RE.fullmatch(path) is None
    ):
        raise TwilioLiveReadHealthError(
            "HTTP_PATH_REJECTED"
        )

    if _API_KEY_SID_RE.fullmatch(
        api_key_sid
    ) is None:
        raise TwilioLiveReadHealthError(
            "API_KEY_SID_REJECTED"
        )

    if not api_key_secret:
        raise TwilioLiveReadHealthError(
            "API_KEY_SECRET_REJECTED"
        )

    authorization = base64.b64encode(
        api_key_sid + b":" + api_key_secret
    ).decode("ascii")

    connection = http.client.HTTPSConnection(
        TWILIO_VERIFY_HOST,
        443,
        timeout=10,
        context=ssl.create_default_context(),
    )

    try:
        connection.request(
            "GET",
            path,
            body=None,
            headers={
                "Authorization": (
                    "Basic " + authorization
                ),
                "Accept": "application/json",
                "User-Agent": (
                    "AIControlCenter-C5-C3C/1"
                ),
                "Connection": "close",
            },
        )

        response = connection.getresponse()
        status = int(response.status)

        body = response.read(
            MAX_PROVIDER_RESPONSE_BYTES + 1
        )

        if (
            len(body)
            > MAX_PROVIDER_RESPONSE_BYTES
        ):
            raise TwilioLiveReadHealthError(
                "PROVIDER_RESPONSE_TOO_LARGE"
            )

        payload: Mapping[str, object] | None

        try:
            decoded = json.loads(
                body.decode("utf-8")
            )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ):
            decoded = None

        payload = (
            decoded
            if type(decoded) is dict
            else None
        )

        return status, payload
    finally:
        authorization = ""
        connection.close()


@dataclass(frozen=True, slots=True)
class TwilioAuthenticatedReadLiveHealthRuntime:
    authority: TwilioAuthenticatedReadAuthority
    api_key_sid_reference: SecretReference
    api_key_secret_reference: SecretReference
    secret_resolver: SecretResolverPort
    http_get: TwilioLiveHttpGet = (
        _twilio_https_get_once
    )

    def __post_init__(self) -> None:
        for reference in (
            self.api_key_sid_reference,
            self.api_key_secret_reference,
        ):
            if (
                reference.to_dict().get("backend")
                != "macos.keychain"
            ):
                raise TwilioLiveReadHealthError(
                    "SECRET_BACKEND_REJECTED"
                )

    def execute(
        self,
        request: TwilioAuthenticatedReadRequest,
        *,
        capability: object | None,
    ) -> ProviderReadResult:
        if (
            type(request)
            is not TwilioAuthenticatedReadRequest
        ):
            raise TwilioLiveReadHealthError(
                "REQUEST_TYPE_REJECTED"
            )

        if (
            request.provider_source
            != TWILIO_PROVIDER_SOURCE
        ):
            raise TwilioLiveReadHealthError(
                "PROVIDER_REJECTED"
            )

        if (
            request.operation
            is not ProviderOperation.READ_HEALTH
        ):
            raise TwilioLiveReadHealthError(
                "LIVE_OPERATION_NOT_ENABLED"
            )

        decision = self.authority.authorize_once(
            request,
            capability=capability,
        )

        if not decision.allowed:
            raise TwilioLiveReadHealthError(
                decision.reason_code
            )

        sid_lease = self.secret_resolver.resolve(
            self.api_key_sid_reference
        )

        secret_lease = self.secret_resolver.resolve(
            self.api_key_secret_reference
        )

        if (
            type(sid_lease)
            is not EphemeralSecretLease
            or type(secret_lease)
            is not EphemeralSecretLease
        ):
            raise TwilioLiveReadHealthError(
                "SECRET_LEASE_REJECTED"
            )

        api_key_sid = _secret_bytes(
            sid_lease.consume()
        )

        api_key_secret = _secret_bytes(
            secret_lease.consume()
        )

        service_sid = str(
            request.service_sid
        )

        path = (
            "/v2/Services/"
            + service_sid
        )

        try:
            http_status, payload = self.http_get(
                path,
                api_key_sid,
                api_key_secret,
            )
        finally:
            api_key_sid = b""
            api_key_secret = b""

        return normalize_service_response(
            http_status=http_status,
            payload=payload,
            expected_sid=request.service_sid,
            identity=request.identity,
            observed_at=datetime.now(
                timezone.utc
            ),
        )

    @property
    def target_activation_state(
        self,
    ) -> ProviderActivationState:
        return (
            ProviderActivationState
            .AUTHENTICATED_READ_ONLY
        )

    @property
    def network_enabled(self) -> bool:
        return True

    @property
    def real_credential_resolution_enabled(
        self,
    ) -> bool:
        return True

    @property
    def sms_enabled(self) -> bool:
        return False

    @property
    def max_attempts(self) -> int:
        return 1

    @property
    def retry_enabled(self) -> bool:
        return False

    @property
    def fallback_enabled(self) -> bool:
        return False

    def __repr__(self) -> str:
        return (
            "TwilioAuthenticatedReadLiveHealthRuntime("
            "activation=AUTHENTICATED_READ_ONLY,"
            "operation=READ_HEALTH,"
            "network_enabled=True,"
            "max_attempts=1,"
            "retry_enabled=False,"
            "fallback_enabled=False,"
            "sms_enabled=False)"
        )


def build_twilio_authenticated_read_live_health_runtime(
    *,
    authority: TwilioAuthenticatedReadAuthority,
    api_key_sid_reference: SecretReference,
    api_key_secret_reference: SecretReference,
    secret_resolver: SecretResolverPort,
) -> TwilioAuthenticatedReadLiveHealthRuntime:
    return TwilioAuthenticatedReadLiveHealthRuntime(
        authority=authority,
        api_key_sid_reference=(
            api_key_sid_reference
        ),
        api_key_secret_reference=(
            api_key_secret_reference
        ),
        secret_resolver=secret_resolver,
    )

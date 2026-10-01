"""Closed Caddy desired-state classification for DEV_INGRESS_001 Phase A.

This is the single future classification entry point for both Caddy adapters.
It is deliberately NOT integrated with inventory, readiness or runtime evidence.
Only the reviewed, line-oriented grammar below is supported; equivalent but
unsupported Caddy configurations are rejected rather than partially interpreted.
There is no Caddy execution, import resolution, environment expansion or network
access. Classification never proves loaded configuration or grants activation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import re
from typing import Any

from core.deployment.contracts import load_schema_registry, validate_contract_payload

_LIMIT = 32768
_PRIVATE_MATCHERS = ("@shopping_namespace", "@shopping_rest_route", "@shopping_rest_route_ambiguous")
_PUBLIC_READ_PATHS = (
    "/shopping/categories", "/shopping/search", "/shopping/featured-products",
    "/shopping/products", "/shopping/products/*",
)
_PUBLIC_MANAGEMENT_PATHS = (
    "/admin", "/admin/*", "/management", "/management/*", "/api", "/api/*",
    "/deployment", "/deployment/*", "/runtime", "/runtime/*", "/governance",
    "/governance/*", "/providers", "/providers/*", "/tasks", "/tasks/*",
    "/woocommerce", "/woocommerce/*", "/cart", "/cart/*", "/checkout",
    "/checkout/*", "/my-account", "/my-account/*", "/order-pay", "/order-pay/*",
    "/add-to-cart", "/add-to-cart/*", "/wc-api", "/wc-api/*",
)
_WORDPRESS_PATHS = (
    "/wp-admin", "/wp-admin/*", "/wp-login.php", "/xmlrpc.php", "/wp-cron.php",
    "/wp-json", "/wp-json/*",
)
_BCRYPT = re.compile(r"\$2[aby]\$(?:0[4-9]|[12][0-9]|3[01])\$[./A-Za-z0-9]{53}\Z")
_USER = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")


class CaddySitePolicyError(ValueError):
    """Only a fixed reason code crosses the boundary; never source/credentials."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class ClassifiedSite:
    role: str
    hostname: str
    host: str
    port: int
    authentication_required: bool


@dataclass(frozen=True)
class CaddySiteClassification:
    """Desired-state identities only. No READY/PASS or runtime proof fields."""

    production: ClassifiedSite
    preview: ClassifiedSite | None


@dataclass(frozen=True, repr=False)
class _Directive:
    # AST nodes stay private and cannot reveal authentication data via repr.
    words: tuple[str, ...] = field(repr=False)
    children: tuple[_Directive, ...] | None = field(default=None, repr=False)


def _fail(code: str) -> None:
    raise CaddySitePolicyError(code)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("INVALID_SITE_POLICY")
        result[key] = value
    return result


def load_site_policy(text: str) -> dict[str, Any]:
    """Read an already supplied JSON value, rejecting duplicates and unknowns."""
    try:
        if type(text) is not str or len(text) > _LIMIT:
            raise ValueError
        value = json.loads(text, object_pairs_hook=_unique_object)
        _validate_policy(value)
        return value
    except Exception:
        raise CaddySitePolicyError("INVALID_SITE_POLICY") from None


def _validate_policy(policy: dict[str, Any]) -> None:
    try:
        if type(policy) is not dict:
            raise ValueError
        validate_contract_payload(
            registry=load_schema_registry(), contract_name="CaddySitePolicy", payload=policy,
        )
        # JSON Schema treats integral floats as integers; Caddy port tokens do not.
        if any(type(policy[role]["upstream"]["port"]) is not int for role in ("production", "preview")):
            raise ValueError
        if any(type(value) is not int for value in policy["listeners"].values()):
            raise ValueError
    except Exception:
        raise CaddySitePolicyError("INVALID_SITE_POLICY") from None


def _tokens(line: str) -> tuple[str, ...]:
    """A conservative Caddy token subset: no escapes, continuations or comments inline."""
    result = []
    index = 0
    while index < len(line):
        if line[index] in " \t":
            index += 1
            continue
        if line[index] in ('"', '`'):
            quote = line[index]
            end = line.find(quote, index + 1)
            if end < 0 or (end + 1 < len(line) and line[end + 1] not in " \t"):
                _fail("UNSUPPORTED_CADDY_SYNTAX")
            token = line[index + 1:end]
            if "\\" in token:
                _fail("UNSUPPORTED_CADDY_SYNTAX")
            # Do not erase quoting around structural tokens. Only these literal
            # response/header values and the exact raw guard expression are used.
            if ((quote == '"' and token not in {"Forbidden", "Not Found", "ok", "noindex, nofollow, noarchive"})
                    or (quote == '`' and token not in {_private_query_pattern(), _rest_route_query_pattern()})):
                _fail("UNSUPPORTED_CADDY_SYNTAX")
            index = end + 1
        else:
            end = index
            while end < len(line) and line[end] not in " \t":
                end += 1
            token = line[index:end]
            if any(char in token for char in ('"', '`', '#', '\\', ';')):
                _fail("UNSUPPORTED_CADDY_SYNTAX")
            index = end
        result.append(token)
    return tuple(result)


def _parse(text: str) -> tuple[_Directive, ...]:
    if (type(text) is not str or len(text) > _LIMIT or not text.isascii()
            or any(ord(char) < 32 and char not in "\n\r\t" for char in text)):
        _fail("UNSUPPORTED_CADDY_SYNTAX")
    # Only LF/CRLF line endings are supported; bare CR is ambiguous.
    text = text.replace("\r\n", "\n")
    if "\r" in text or text.count("\n") > 512:
        _fail("UNSUPPORTED_CADDY_SYNTAX")
    lines = [_tokens(line) for line in text.split("\n")
             if line.strip() and not line.lstrip(" \t").startswith("#")]
    index = 0

    def block(depth: int) -> tuple[_Directive, ...]:
        nonlocal index
        if depth > 5:
            _fail("UNSUPPORTED_CADDY_SYNTAX")
        nodes = []
        while index < len(lines):
            words = lines[index]
            index += 1
            if words == ("}",):
                if depth == 0:
                    _fail("UNSUPPORTED_CADDY_SYNTAX")
                return tuple(nodes)
            opens = words[-1:] == ("{",)
            if opens:
                words = words[:-1]
            if any(word in ("{", "}") for word in words):
                _fail("UNSUPPORTED_CADDY_SYNTAX")
            nodes.append(_Directive(words, block(depth + 1) if opens else None))
        if depth:
            _fail("UNSUPPORTED_CADDY_SYNTAX")
        return tuple(nodes)

    return block(0)


def _leaf(*words: str) -> _Directive:
    return _Directive(words)


def _discard(*words: str) -> _Directive:
    return _Directive(words, (_leaf("output", "discard"),))


def _private_query_pattern() -> str:
    # Same reviewed namespace grammar as the existing production guard. Requiring
    # the entire expression prevents an attacker supplying a weaker lookalike.
    def spelling(word: str) -> str:
        return "".join(
            "(?:" + re.escape(char) + "|%(?:25)*(?:"
            + "|".join(sorted({format(ord(c), "02x") for c in (char.lower(), char.upper())}))
            + "))" for char in word
        )
    slash = "(?:/|%(?:25)*2f)"
    key = spelling("rest") + "(?:_|[.+]|%(?:25)*(?:5f|20|2e))" + spelling("route")
    namespace = slash.join(map(spelling, ("aicontrolcenter", "v1", "shopping")))
    return "(?i)(^|[&;])" + key + "=" + slash + "*" + namespace + "(" + slash + "|[&;]|$)"


def _rest_route_query_pattern() -> str:
    """Match every normalized spelling of the reserved WordPress query route key."""
    def spelling(word: str) -> str:
        return "".join(
            "(?:" + re.escape(char) + "|%(?:25)*(?:"
            + "|".join(sorted({format(ord(c), "02x") for c in (char.lower(), char.upper())}))
            + "))" for char in word
        )

    key = spelling("rest") + "(?:_|[.+]|%(?:25)*(?:2b|2e|5f|20))" + spelling("route")
    boundary = "(^|[&;]|%(?:25)*(?:26|3b))"
    delimiter = "(?:=|%(?:25)*(?:3d)|[&;]|%(?:25)*(?:26|3b)|$)"
    return "(?i)" + boundary + key + delimiter


def _auth(node: _Directive) -> None:
    if node.words not in (("basic_auth",), ("basic_auth", "bcrypt")):
        _fail("PREVIEW_AUTH_ORDER_OR_BYPASS")
    if node.children is None or not 1 <= len(node.children) <= 8:
        _fail("PREVIEW_AUTH_INCOMPLETE")
    users = set()
    for account in node.children:
        if (account.children is not None or len(account.words) != 2
                or not _USER.fullmatch(account.words[0])
                or not _BCRYPT.fullmatch(account.words[1]) or account.words[0] in users):
            _fail("PREVIEW_AUTH_INCOMPLETE")
        users.add(account.words[0])


def _site(node: _Directive, role: str, identity: dict[str, Any]) -> ClassifiedSite:
    if node.children is None:
        _fail("UNSUPPORTED_SITE_STRUCTURE")
    parts: dict[str, _Directive] = {}
    for child in node.children:
        if not child.words or child.words[0] in parts:
            _fail("UNSUPPORTED_SITE_STRUCTURE")
        parts[child.words[0]] = child
    if parts["log"] != _discard("log"):
        _fail("UNSAFE_LOGGING")
    header = (
        _leaf("X-Content-Type-Options", "nosniff"),
        _leaf("Referrer-Policy", "no-referrer" if role == "preview" else "strict-origin-when-cross-origin"),
        *([_leaf("X-Robots-Tag", "noindex, nofollow, noarchive")] if role == "preview" else []),
        _leaf("-Server"),
    )
    if parts["header"] != _Directive(("header",), header):
        _fail("UNSAFE_HEADER_POLICY")
    guards = (
        _leaf(_PRIVATE_MATCHERS[0], "path", "/wp-json/aicontrolcenter/v1/shopping", "/wp-json/aicontrolcenter/v1/shopping/*"),
        _leaf(_PRIVATE_MATCHERS[1], "query", "rest_route=/aicontrolcenter/v1/shopping", "rest_route=/aicontrolcenter/v1/shopping/*"),
        _leaf(_PRIVATE_MATCHERS[2], "vars_regexp", "{http.request.uri.query}", _rest_route_query_pattern()),
    )
    if not set(_PRIVATE_MATCHERS).issubset(parts):
        _fail("PRIVATE_GUARDS_REQUIRED")
    if any(parts[guard.words[0]] != guard for guard in guards):
        _fail("PRIVATE_GUARD_MISMATCH")
    route = parts["route"]
    denies = tuple(_leaf("respond", name, "Forbidden", "403") for name in _PRIVATE_MATCHERS)
    if route.words != ("route",) or route.children is None or route.children[:3] != denies:
        _fail("PRIVATE_GUARD_ORDER_OR_BYPASS")
    tail = route.children[3:]
    if role == "preview":
        if set(parts) != {"log", "header", "route", *_PRIVATE_MATCHERS}:
            _fail("UNSUPPORTED_SITE_STRUCTURE")
        if len(tail) != 2:
            if not any(child.words and child.words[0] == "basic_auth" for child in tail):
                _fail("PRIVATE_GUARDS_REQUIRED")
            _fail("PREVIEW_AUTH_ORDER_OR_BYPASS")
        _auth(tail[0])
    else:
        public_api = identity.get("public_shopping_api")
        if not isinstance(public_api, dict):
            _fail("PUBLIC_READ_POLICY_REQUIRED")
        expected_parts = {
            "log", "header", "route", *_PRIVATE_MATCHERS,
            "@public_shopping_read", "@public_shopping_namespace",
            "@management_namespace", "@wordpress_namespace", "@legacy_storefront",
        }
        if set(parts) != expected_parts:
            _fail("UNSUPPORTED_SITE_STRUCTURE")
        expected_matchers = (
            _Directive(("@public_shopping_read",), (
                _leaf("method", "GET"), _leaf("path", *_PUBLIC_READ_PATHS),
            )),
            _leaf("@public_shopping_namespace", "path", "/shopping", "/shopping/*"),
            _leaf("@management_namespace", "path", *_PUBLIC_MANAGEMENT_PATHS),
            _leaf("@wordpress_namespace", "path", *_WORDPRESS_PATHS),
            _leaf("@legacy_storefront", "path", "/homepage/storefront"),
        )
        if any(parts[item.words[0]] != item for item in expected_matchers):
            _fail("PUBLIC_READ_POLICY_MISMATCH")
        public_endpoint = public_api["upstream"]
        public_handle = _Directive(
            ("handle", "@public_shopping_read"),
            (_leaf("reverse_proxy", f"{public_endpoint['host']}:{public_endpoint['port']}"),),
        )
        endpoint = identity["upstream"]
        expected_route = (
            *denies,
            _leaf("redir", "@legacy_storefront", "/", "301"),
            _leaf("respond", "@management_namespace", "Not Found", "404"),
            _leaf("respond", "@wordpress_namespace", "Not Found", "404"),
            public_handle,
            _leaf("respond", "@public_shopping_namespace", "Not Found", "404"),
            _leaf("respond", "/__aicontrolcenter_ingress_health", "ok", "200"),
            _leaf("respond", "/healthz", "ok", "200"),
            _leaf("reverse_proxy", f"{endpoint['host']}:{endpoint['port']}"),
        )
        if route.children != expected_route:
            _fail("UNSUPPORTED_PRODUCTION_ROUTE")
        tail = expected_route
    endpoint = identity["upstream"]
    if tail[-1] != _leaf("reverse_proxy", f"{endpoint['host']}:{endpoint['port']}"):
        _fail("UNAPPROVED_UPSTREAM_OR_PROXY")
    return ClassifiedSite(role, identity["hostname"], endpoint["host"], endpoint["port"], role == "preview")


def classify_caddy_sites(
    text: str, *, policy: dict[str, Any], ingress_contract: dict[str, Any],
) -> CaddySiteClassification:
    """Classify the ENTIRE supplied file or reject it with a value-free error.

    Both legacy adapters remain unchanged in Phase A. Phase B must call this
    same function, never filter out unrecognized text or count only known ports.
    """
    _validate_policy(policy)
    try:
        validate_contract_payload(
            registry=load_schema_registry(), contract_name="IngressContract", payload=ingress_contract,
        )
        upstream = ingress_contract["upstream"]
        if {"host": upstream["host"], "port": upstream["port"]} != policy["production"]["upstream"]:
            raise ValueError
    except Exception:
        raise CaddySitePolicyError("PRODUCTION_CONTRACT_MISMATCH") from None
    nodes = _parse(text)
    listeners = policy["listeners"]
    global_options = _Directive((), (
        _leaf("http_port", str(listeners["http_port"])),
        _leaf("https_port", str(listeners["https_port"])),
        _discard("log", "default"),
    ))
    if not nodes or nodes[0] != global_options:
        _fail("UNSUPPORTED_GLOBAL_POLICY")
    sites: dict[str, ClassifiedSite] = {}
    identities = {policy[role]["hostname"]: role for role in ("production", "preview")}
    for node in nodes[1:]:
        if len(node.words) != 1 or node.words[0] not in identities:
            _fail("UNKNOWN_SITE")
        role = identities[node.words[0]]
        if role in sites:
            _fail("DUPLICATE_SITE")
        identity = dict(policy[role])
        if role == "production":
            identity["public_shopping_api"] = policy["public_shopping_api"]
        sites[role] = _site(node, role, identity)
    if "production" not in sites:
        _fail("PRODUCTION_SITE_REQUIRED")
    return CaddySiteClassification(sites["production"], sites.get("preview"))


__all__ = (
    "CaddySiteClassification", "CaddySitePolicyError", "ClassifiedSite",
    "classify_caddy_sites", "load_site_policy",
)

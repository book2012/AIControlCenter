"""Fixed loopback HTTP/1.1 read transport with deadlines on every blocking syscall.

No requests session, environment proxy lookup, DNS, redirect, or retry path.
Only bounded Content-Length or connection-close responses are accepted.
"""
import json
import socket
import time

from core.shopping.runtime_cutover_secret_source import WORDPRESS_PORT_EXPECTED
from .capability import ControlPlaneShoppingReadCapability, derive_verifier

HOST = "127.0.0.1"
PORT = int(WORDPRESS_PORT_EXPECTED)
REST_PATH = "/wp-json/aicontrolcenter/v1/shopping/products"
CONNECT_TIMEOUT = 2.0
READ_TIMEOUT = 2.0
TOTAL_TIMEOUT = 5.0
MAX_RESPONSE_BYTES = 32768
MAX_HEADER_BYTES = 8192
MAX_NAME_CHARS = 200


class ShoppingReadError(RuntimeError):
    def __init__(self):
        super().__init__("shopping read failed closed")


def validate_page(page, page_size):
    if type(page) is not int or not 1 <= page <= 10000 or type(page_size) is not int or not 1 <= page_size <= 20:
        raise ShoppingReadError()


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ShoppingReadError()
        result[key] = value
    return result


def _projection(raw, page, page_size, capability):
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique)
    if type(value) is not dict or set(value) != {"items", "page", "page_size", "has_more"}:
        raise ShoppingReadError()
    if (type(value["page"]) is not int or value["page"] != page
            or type(value["page_size"]) is not int or value["page_size"] != page_size
            or type(value["has_more"]) is not bool or type(value["items"]) is not list
            or len(value["items"]) > page_size):
        raise ShoppingReadError()
    previous = 0
    forbidden = (capability._request_ascii(), derive_verifier(capability)._provisioning_digest(), "Authorization", "Bearer ")
    for item in value["items"]:
        if type(item) is not dict or set(item) != {"id", "name"}:
            raise ShoppingReadError()
        name = item["name"]
        if (type(item["id"]) is not int or item["id"] <= previous
                or type(name) is not str or len(name) > MAX_NAME_CHARS
                or any(ord(c) < 32 or ord(c) == 127 or c in "<>" for c in name)
                or any(secret in name for secret in forbidden)):
            raise ShoppingReadError()
        previous = item["id"]
    return value


def _exchange(capability, page, page_size):
    deadline = time.monotonic() + TOTAL_TIMEOUT

    def budget(limit):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ShoppingReadError()
        return min(limit, remaining)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
        connection.settimeout(budget(CONNECT_TIMEOUT))
        connection.connect((HOST, PORT))
        request = (f"GET {REST_PATH}?page={page}&page_size={page_size} HTTP/1.1\r\n"
                   f"Host: {HOST}:{PORT}\r\nAuthorization: Bearer {capability._request_ascii()}\r\n"
                   "Accept: application/json\r\nConnection: close\r\n\r\n").encode("ascii")
        try:
            while request:
                connection.settimeout(budget(READ_TIMEOUT))
                sent = connection.send(request)
                if sent <= 0:
                    raise ShoppingReadError()
                request = request[sent:]
        finally:
            request = b""
        data = bytearray()
        while b"\r\n\r\n" not in data:
            connection.settimeout(budget(READ_TIMEOUT))
            block = connection.recv(min(4096, MAX_HEADER_BYTES + 1 - len(data)))
            if not block:
                raise ShoppingReadError()
            data.extend(block)
            if len(data) > MAX_HEADER_BYTES:
                raise ShoppingReadError()
        header, body = bytes(data).split(b"\r\n\r\n", 1)
        lines = header.split(b"\r\n")
        if lines[0] not in (b"HTTP/1.1 200 OK", b"HTTP/1.0 200 OK"):
            raise ShoppingReadError()
        headers = {}
        for line in lines[1:]:
            key, sep, value = line.partition(b":")
            key = key.lower()
            if not sep or not key or key in headers or any(c not in b"abcdefghijklmnopqrstuvwxyz0123456789-" for c in key):
                raise ShoppingReadError()
            headers[key] = value.strip()
        if b"transfer-encoding" in headers or headers.get(b"content-encoding", b"identity") != b"identity":
            raise ShoppingReadError()
        if headers.get(b"content-type", b"").split(b";", 1)[0].lower() != b"application/json":
            raise ShoppingReadError()
        size = headers.get(b"content-length")
        if size is not None and (not size.isdigit() or len(size) > 5):
            raise ShoppingReadError()
        expected = int(size) if size is not None else None
        if expected is not None and expected > MAX_RESPONSE_BYTES:
            raise ShoppingReadError()
        body = bytearray(body)
        while expected is None or len(body) < expected:
            if len(body) > MAX_RESPONSE_BYTES:
                raise ShoppingReadError()
            connection.settimeout(budget(READ_TIMEOUT))
            block = connection.recv(min(4096, MAX_RESPONSE_BYTES + 1 - len(body)))
            if not block:
                break
            body.extend(block)
        budget(READ_TIMEOUT)
        if len(body) > MAX_RESPONSE_BYTES or (expected is not None and len(body) != expected):
            raise ShoppingReadError()
        result = _projection(bytes(body), page, page_size, capability)
        budget(READ_TIMEOUT)
        return result


class ControlPlaneShoppingReadAdapter:
    __slots__ = ()
    trust_env = False
    proxies = ()
    redirects = False
    max_retries = 0

    def products(self, capability, *, page=1, page_size=20):
        validate_page(page, page_size)
        if type(capability) is not ControlPlaneShoppingReadCapability:
            raise ShoppingReadError()
        result = None
        try:
            result = _exchange(capability, page, page_size)
        except Exception:
            pass
        # Outside the handler: no raw exception context or request attached.
        if result is None:
            raise ShoppingReadError()
        return result

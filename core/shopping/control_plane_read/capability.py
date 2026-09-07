"""Control Plane owned bearer and integrity-sensitive verifier values."""
import hashlib
import re
import secrets

_CANONICAL = re.compile(r"[0-9a-f]{64}", re.ASCII)


class CapabilityError(ValueError):
    def __init__(self):
        super().__init__("shopping capability operation denied")


class ControlPlaneShoppingReadCapability:
    __slots__ = ("__ascii",)

    def __init__(self, value):
        if type(value) is not str or _CANONICAL.fullmatch(value) is None:
            raise CapabilityError()
        self.__ascii = value

    def __repr__(self):
        return "ControlPlaneShoppingReadCapability(<redacted>)"

    __str__ = __repr__

    def __reduce_ex__(self, protocol):
        raise CapabilityError()

    def _request_ascii(self):
        """Only the dedicated transport may materialize the bearer."""
        return self.__ascii


class ShoppingReadVerifier:
    __slots__ = ("__digest",)

    def __init__(self, digest):
        if type(digest) is not str or _CANONICAL.fullmatch(digest) is None:
            raise CapabilityError()
        self.__digest = digest

    def __repr__(self):
        return "ShoppingReadVerifier(<integrity-sensitive>)"

    __str__ = __repr__

    def __reduce_ex__(self, protocol):
        raise CapabilityError()

    def _provisioning_digest(self):
        return self.__digest


def _generate_with_entropy_for_tests(entropy):
    raw = entropy(32)
    if type(raw) is not bytes or len(raw) != 32:
        raise CapabilityError()
    return ControlPlaneShoppingReadCapability(raw.hex())


def generate_control_plane_shopping_read_capability():
    return _generate_with_entropy_for_tests(secrets.token_bytes)


def derive_verifier(capability):
    if type(capability) is not ControlPlaneShoppingReadCapability:
        raise CapabilityError()
    return ShoppingReadVerifier(hashlib.sha256(capability._request_ascii().encode("ascii")).hexdigest())

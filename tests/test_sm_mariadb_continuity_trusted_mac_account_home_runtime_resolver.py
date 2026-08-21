import ast
from dataclasses import FrozenInstanceError, fields
import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest

from core.secrets import mariadb_continuity_trusted_mac_account_home_runtime_resolver as resolver


ROOT = Path(__file__).parents[1]
IMPLEMENTATION = ROOT / "core/secrets/mariadb_continuity_trusted_mac_account_home_runtime_resolver.py"


def install_observations(monkeypatch, *, platform_value="Darwin", real_uid=501,
                         effective_uid=501, passwd_home="/Users/trusted"):
    calls = []

    def observe_platform():
        calls.append("platform.system")
        if isinstance(platform_value, BaseException):
            raise platform_value
        return platform_value

    def observe_real_uid():
        calls.append("os.getuid")
        if isinstance(real_uid, BaseException):
            raise real_uid
        return real_uid

    def observe_effective_uid():
        calls.append("os.geteuid")
        if isinstance(effective_uid, BaseException):
            raise effective_uid
        return effective_uid

    def lookup(uid):
        calls.append(("pwd.getpwuid", uid))
        if isinstance(passwd_home, BaseException):
            raise passwd_home
        if passwd_home is MISSING:
            return object()
        return SimpleNamespace(pw_dir=passwd_home)

    monkeypatch.setattr(resolver.platform, "system", observe_platform)
    monkeypatch.setattr(resolver.os, "getuid", observe_real_uid)
    monkeypatch.setattr(resolver.os, "geteuid", observe_effective_uid)
    monkeypatch.setattr(resolver.pwd, "getpwuid", lookup)
    return calls


MISSING = object()


def test_success_has_exact_order_sources_counts_and_uid_argument(monkeypatch):
    calls = install_observations(monkeypatch)
    result = resolver.resolve_trusted_mac_account_home()
    assert calls == [
        "platform.system", "os.getuid", "os.geteuid", ("pwd.getpwuid", 501)
    ]
    assert type(result) is resolver.ResolvedTrustedMacAccountHome
    assert result.bound_uid == 501
    assert result.passwd_home == "/Users/trusted"


@pytest.mark.parametrize("platform_value", ["Linux", "darwin", RuntimeError("fail")])
def test_platform_failure_prevents_all_uid_and_passwd_observation(monkeypatch, platform_value):
    calls = install_observations(monkeypatch, platform_value=platform_value)
    with pytest.raises(resolver.TrustedMacAccountHomeResolutionError):
        resolver.resolve_trusted_mac_account_home()
    assert calls == ["platform.system"]


def test_real_uid_failure_does_not_observe_effective_uid_or_bind_or_lookup(monkeypatch):
    calls = install_observations(monkeypatch, real_uid=RuntimeError("fail"))
    with pytest.raises(resolver.TrustedMacAccountHomeResolutionError):
        resolver.resolve_trusted_mac_account_home()
    assert calls == ["platform.system", "os.getuid"]


def test_effective_uid_failure_occurs_after_real_uid_without_binding_or_lookup(monkeypatch):
    calls = install_observations(monkeypatch, effective_uid=RuntimeError("fail"))
    with pytest.raises(resolver.TrustedMacAccountHomeResolutionError):
        resolver.resolve_trusted_mac_account_home()
    assert calls == ["platform.system", "os.getuid", "os.geteuid"]


@pytest.mark.parametrize("real_uid,effective_uid", [(0, 501), (501, 0), (0, 0)])
def test_root_in_either_uid_is_rejected_before_passwd(monkeypatch, real_uid, effective_uid):
    calls = install_observations(monkeypatch, real_uid=real_uid, effective_uid=effective_uid)
    with pytest.raises(resolver.TrustedMacAccountHomeResolutionError, match="root"):
        resolver.resolve_trusted_mac_account_home()
    assert calls == ["platform.system", "os.getuid", "os.geteuid"]


def test_uid_semantics_are_not_swapped_and_mismatch_prevents_passwd(monkeypatch):
    calls = install_observations(monkeypatch, real_uid=501, effective_uid=502)
    with pytest.raises(resolver.TrustedMacAccountHomeResolutionError, match="match"):
        resolver.resolve_trusted_mac_account_home()
    assert calls == ["platform.system", "os.getuid", "os.geteuid"]


def test_passwd_failure_is_attempted_once_without_retry(monkeypatch):
    calls = install_observations(monkeypatch, passwd_home=KeyError("missing"))
    with pytest.raises(resolver.TrustedMacAccountHomeResolutionError, match="passwd lookup"):
        resolver.resolve_trusted_mac_account_home()
    assert calls.count(("pwd.getpwuid", 501)) == 1


@pytest.mark.parametrize("passwd_home", [MISSING, None, 1, "", "relative/home", "Users/home", "/bad\0home"])
def test_invalid_pw_dir_values_fail_closed(monkeypatch, passwd_home):
    calls = install_observations(monkeypatch, passwd_home=passwd_home)
    with pytest.raises(resolver.TrustedMacAccountHomeResolutionError):
        resolver.resolve_trusted_mac_account_home()
    assert calls[-1] == ("pwd.getpwuid", 501)
    assert calls.count(("pwd.getpwuid", 501)) == 1


def test_str_subclass_pw_dir_fails_closed(monkeypatch):
    class PasswdHomeSubclass(str):
        pass

    calls = install_observations(
        monkeypatch, passwd_home=PasswdHomeSubclass("/Users/trusted")
    )
    with pytest.raises(resolver.TrustedMacAccountHomeResolutionError, match="string"):
        resolver.resolve_trusted_mac_account_home()
    assert calls == [
        "platform.system", "os.getuid", "os.geteuid", ("pwd.getpwuid", 501)
    ]


@pytest.mark.parametrize("passwd_home", ["/", "/Users/name/../unchanged", "/ trailing ", "//network-like"])
def test_valid_absolute_pw_dir_is_preserved_unchanged(monkeypatch, passwd_home):
    install_observations(monkeypatch, passwd_home=passwd_home)
    assert resolver.resolve_trusted_mac_account_home().passwd_home == passwd_home


def test_resolved_value_is_immutable_slotted_two_field_zero_authority_data(monkeypatch):
    install_observations(monkeypatch)
    value = resolver.resolve_trusted_mac_account_home()
    assert tuple(item.name for item in fields(value)) == ("bound_uid", "passwd_home")
    assert not hasattr(value, "__dict__")
    with pytest.raises(FrozenInstanceError):
        value.bound_uid = 502
    authority_terms = ("authority", "authorize", "production", "protected", "ubuntu",
                       "filesystem", "admission", "verification", "capability")
    assert not any(term in field.name for field in fields(value) for term in authority_terms)


@pytest.mark.parametrize("args", [(), (501, "/caller")])
def test_direct_resolved_value_construction_is_rejected(args):
    with pytest.raises(TypeError):
        resolver.ResolvedTrustedMacAccountHome(*args)


def test_caller_cannot_select_identity_home_or_path_inputs():
    assert not inspect.signature(resolver.resolve_trusted_mac_account_home).parameters
    assert not inspect.signature(resolver.RuntimeHomeResolver).parameters
    with pytest.raises(TypeError):
        resolver.resolve_trusted_mac_account_home(home="/caller")


def test_implementation_has_only_fixed_runtime_sources_and_no_prohibited_apis():
    tree = ast.parse(IMPLEMENTATION.read_text())
    calls = {
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, (ast.Attribute, ast.Name))
    }
    required = {"system", "getuid", "geteuid", "getpwuid"}
    prohibited = {
        "getenv", "home", "expanduser", "getpwnam", "strip", "resolve", "realpath",
        "stat", "lstat", "exists", "is_dir", "is_symlink", "glob", "rglob", "iterdir",
        "walk", "listdir", "scandir", "open", "read", "read_text", "read_bytes",
    }
    assert required <= calls
    assert calls.isdisjoint(prohibited)
    source = IMPLEMENTATION.read_text()
    assert "os.environ" not in source
    assert all(term not in source for term in ("subprocess", "docker", "pymysql", "ControlledExecutionPort"))

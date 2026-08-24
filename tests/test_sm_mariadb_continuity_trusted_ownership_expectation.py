import ast
from dataclasses import FrozenInstanceError, fields
import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest

from core.secrets import mariadb_continuity_trusted_ownership_expectation as module
from core.secrets.mariadb_continuity_trusted_mac_account_home_runtime_resolver import (
    ResolvedTrustedMacAccountHome,
)


ROOT = Path(__file__).parents[1]
IMPLEMENTATION = ROOT / "core/secrets/mariadb_continuity_trusted_ownership_expectation.py"


def resolved_home(bound_uid=501):
    value = object.__new__(ResolvedTrustedMacAccountHome)
    object.__setattr__(value, "bound_uid", bound_uid)
    object.__setattr__(value, "passwd_home", "/Users/trusted")
    return value


def install_group_lookup(monkeypatch, result=SimpleNamespace(gr_gid=20)):
    calls = []

    def lookup(group_name):
        calls.append(group_name)
        if isinstance(result, BaseException):
            raise result
        return result

    monkeypatch.setattr(module.grp, "getgrnam", lookup)
    return calls


def test_exact_repository_group_policy_and_success(monkeypatch):
    assert module.TRUSTED_APPLICATION_GROUP_NAME == "staff"
    calls = install_group_lookup(monkeypatch, SimpleNamespace(gr_gid=20))
    result = module.issue_trusted_ownership_expectation(resolved_home(501))
    assert type(result) is module.TrustedOwnershipExpectation
    assert result.expected_uid == 501
    assert result.expected_gid == 20
    assert calls == ["staff"]


def test_issuer_has_exactly_one_fixed_input_and_rejects_caller_policy():
    signature = inspect.signature(module.issue_trusted_ownership_expectation)
    assert tuple(signature.parameters) == ("resolved_home",)
    for name in ("uid", "gid", "group", "group_name", "fallback"):
        with pytest.raises(TypeError):
            module.issue_trusted_ownership_expectation(resolved_home(501), **{name: 1})


@pytest.mark.parametrize("args", [(), (501, 20)])
def test_direct_construction_is_prohibited(args):
    with pytest.raises(TypeError):
        module.TrustedOwnershipExpectation(*args)


def test_result_is_frozen_slotted_and_exactly_two_fields(monkeypatch):
    install_group_lookup(monkeypatch)
    result = module.issue_trusted_ownership_expectation(resolved_home())
    assert tuple(item.name for item in fields(result)) == (
        "expected_uid", "expected_gid"
    )
    assert not hasattr(result, "__dict__")
    with pytest.raises(FrozenInstanceError):
        result.expected_uid = 502


class IntSubclass(int):
    pass


@pytest.mark.parametrize(
    "bound_uid",
    [True, False, 0, -1, None, "501", 501.0, IntSubclass(501), object()],
)
def test_invalid_bound_uid_fails_before_group_lookup(monkeypatch, bound_uid):
    calls = install_group_lookup(monkeypatch)
    with pytest.raises(module.TrustedOwnershipExpectationIssuanceError):
        module.issue_trusted_ownership_expectation(resolved_home(bound_uid))
    assert calls == []


def test_wrong_input_type_fails_before_group_lookup(monkeypatch):
    calls = install_group_lookup(monkeypatch)
    with pytest.raises(module.TrustedOwnershipExpectationIssuanceError):
        module.issue_trusted_ownership_expectation(SimpleNamespace(bound_uid=501))
    assert calls == []


def test_group_lookup_failure_is_single_attempt_and_fail_closed(monkeypatch):
    calls = install_group_lookup(monkeypatch, KeyError("missing"))
    with pytest.raises(module.TrustedOwnershipExpectationIssuanceError):
        module.issue_trusted_ownership_expectation(resolved_home())
    assert calls == ["staff"]


def test_missing_gr_gid_fails_closed_after_one_lookup(monkeypatch):
    calls = install_group_lookup(monkeypatch, object())
    with pytest.raises(module.TrustedOwnershipExpectationIssuanceError):
        module.issue_trusted_ownership_expectation(resolved_home())
    assert calls == ["staff"]


@pytest.mark.parametrize("gr_gid", [True, IntSubclass(20), -1, None, "20", 20.0])
def test_invalid_gr_gid_fails_closed_after_one_lookup(monkeypatch, gr_gid):
    calls = install_group_lookup(monkeypatch, SimpleNamespace(gr_gid=gr_gid))
    with pytest.raises(module.TrustedOwnershipExpectationIssuanceError):
        module.issue_trusted_ownership_expectation(resolved_home())
    assert calls == ["staff"]


def test_zero_gr_gid_is_allowed(monkeypatch):
    calls = install_group_lookup(monkeypatch, SimpleNamespace(gr_gid=0))
    result = module.issue_trusted_ownership_expectation(resolved_home())
    assert result.expected_gid == 0
    assert calls == ["staff"]


def test_source_has_only_group_observation_and_no_runtime_or_filesystem_calls():
    source = IMPLEMENTATION.read_text()
    tree = ast.parse(source)
    calls = {
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Attribute, ast.Name))
    }
    assert "getgrnam" in calls
    prohibited = {
        "RuntimeHomeResolver", "resolve_trusted_mac_account_home", "system",
        "getuid", "geteuid", "getpwuid", "getgid", "getegid", "stat", "lstat",
        "exists", "is_dir", "is_file", "is_symlink", "open", "read", "read_text",
        "read_bytes", "resolve", "iterdir", "listdir", "scandir", "walk",
    }
    assert calls.isdisjoint(prohibited)
    assert "import os" not in source
    assert "import platform" not in source
    assert "import pwd" not in source


def test_value_and_documentation_preserve_zero_authority_semantics(monkeypatch):
    install_group_lookup(monkeypatch)
    result = module.issue_trusted_ownership_expectation(resolved_home())
    prohibited_terms = (
        "authority", "provenance", "capability", "path", "metadata", "evidence"
    )
    assert not any(
        term in item.name for item in fields(result) for term in prohibited_terms
    )
    documentation = module.__doc__ or ""
    for meaning in (
        "zero authority", "provenance", "authorization", "capability",
        "admission", "verification", "filesystem", "metadata", "RECOVER",
        "Production", "security boundary", "Python object identity",
    ):
        assert meaning in documentation

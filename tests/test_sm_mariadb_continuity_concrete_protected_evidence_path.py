import ast
from dataclasses import FrozenInstanceError, fields
import inspect

import pytest

from core.secrets import (
    mariadb_continuity_authoritative_mac_protected_evidence_suffix as suffix_policy,
)
from core.secrets import (
    mariadb_continuity_concrete_protected_evidence_path as composition,
)
from core.secrets import (
    mariadb_continuity_trusted_mac_account_home_runtime_resolver as resolver,
)


def _resolved_home(passwd_home: str) -> resolver.ResolvedTrustedMacAccountHome:
    value = object.__new__(resolver.ResolvedTrustedMacAccountHome)
    object.__setattr__(value, "bound_uid", 501)
    object.__setattr__(value, "passwd_home", passwd_home)
    return value


@pytest.mark.parametrize(
    ("passwd_home", "expected"),
    (
        (
            "/Users/trusted",
            "/Users/trusted/Library/Application Support/AIControlCenter/"
            "protected-external-evidence/mariadb-continuity",
        ),
        (
            "/",
            "/Library/Application Support/AIControlCenter/"
            "protected-external-evidence/mariadb-continuity",
        ),
        (
            "/Users/trusted/",
            "/Users/trusted/Library/Application Support/AIControlCenter/"
            "protected-external-evidence/mariadb-continuity",
        ),
        (
            "/Users/name/../unchanged",
            "/Users/name/../unchanged/Library/Application Support/AIControlCenter/"
            "protected-external-evidence/mariadb-continuity",
        ),
        (
            "//network-like",
            "//network-like/Library/Application Support/AIControlCenter/"
            "protected-external-evidence/mariadb-continuity",
        ),
    ),
)
def test_exact_lexical_composition_preserves_home(
    passwd_home: str, expected: str
) -> None:
    result = composition.compose_concrete_protected_evidence_path(
        _resolved_home(passwd_home)
    )

    assert result.concrete_path == expected


def test_composer_uses_exact_authoritative_repository_suffix(monkeypatch) -> None:
    repository_value = "repository-owned-test-suffix"
    monkeypatch.setattr(
        suffix_policy, "EXACT_PROTECTED_EVIDENCE_SUFFIX", repository_value
    )

    result = composition.compose_concrete_protected_evidence_path(
        _resolved_home("/Users/trusted")
    )

    assert result.concrete_path == "/Users/trusted/" + repository_value


def test_composer_accepts_only_resolved_home() -> None:
    signature = inspect.signature(
        composition.compose_concrete_protected_evidence_path
    )

    assert tuple(signature.parameters) == ("resolved_home",)
    with pytest.raises(TypeError):
        composition.compose_concrete_protected_evidence_path(
            _resolved_home("/Users/trusted"), suffix="caller"
        )
    with pytest.raises(TypeError):
        composition.compose_concrete_protected_evidence_path(
            _resolved_home("/Users/trusted"), base_path="caller"
        )
    with pytest.raises(TypeError):
        composition.compose_concrete_protected_evidence_path(
            _resolved_home("/Users/trusted"), concrete_path="caller"
        )
    with pytest.raises(TypeError):
        composition.compose_concrete_protected_evidence_path("/caller/home")


def test_composer_does_not_execute_runtime_resolver(monkeypatch) -> None:
    def prohibited(*args, **kwargs):
        raise AssertionError("runtime resolution or observation is prohibited")

    monkeypatch.setattr(resolver.RuntimeHomeResolver, "__init__", prohibited)
    monkeypatch.setattr(resolver.RuntimeHomeResolver, "resolve_once", prohibited)
    monkeypatch.setattr(resolver, "resolve_trusted_mac_account_home", prohibited)
    monkeypatch.setattr(resolver.platform, "system", prohibited)
    monkeypatch.setattr(resolver.os, "getuid", prohibited)
    monkeypatch.setattr(resolver.os, "geteuid", prohibited)
    monkeypatch.setattr(resolver.pwd, "getpwuid", prohibited)

    result = composition.compose_concrete_protected_evidence_path(
        _resolved_home("/Users/trusted")
    )

    assert result.concrete_path.startswith("/Users/trusted/")


def test_source_has_no_observation_filesystem_or_path_normalization_api() -> None:
    source = inspect.getsource(composition)
    tree = ast.parse(source)
    imported_roots = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }

    assert imported_roots.isdisjoint({"os", "pathlib", "platform", "pwd"})
    assert called_names.isdisjoint({"open", "Path"})
    assert called_attributes.isdisjoint(
        {
            "abspath",
            "exists",
            "expanduser",
            "getuid",
            "geteuid",
            "getpwuid",
            "is_dir",
            "is_file",
            "is_symlink",
            "join",
            "lstat",
            "normpath",
            "realpath",
            "resolve",
            "stat",
            "strip",
            "system",
        }
    )


def test_concrete_path_value_is_immutable_slotted_and_exactly_one_field() -> None:
    result = composition.compose_concrete_protected_evidence_path(
        _resolved_home("/Users/trusted")
    )

    assert tuple(field.name for field in fields(result)) == ("concrete_path",)
    assert composition.ConcreteProtectedEvidencePath.__slots__ == ("concrete_path",)
    assert not hasattr(result, "__dict__")
    with pytest.raises(FrozenInstanceError):
        result.concrete_path = "/caller/path"
    with pytest.raises(TypeError):
        composition.ConcreteProtectedEvidencePath()


def test_value_has_zero_authority_and_no_provenance_security_semantics() -> None:
    result = composition.compose_concrete_protected_evidence_path(
        _resolved_home("/Users/trusted")
    )
    forbidden_fields = {
        "uid",
        "suffix",
        "policy",
        "authorization",
        "capability",
        "admission",
        "verification",
        "production_authority",
        "protected_source_authority",
        "filesystem_authority",
        "provenance",
        "security_boundary",
    }

    assert forbidden_fields.isdisjoint(field.name for field in fields(result))
    assert "not provenance" in composition.__doc__
    assert "Python object identity is not a security boundary" in composition.__doc__
    assert "security boundary" in composition.__doc__
    assert "independently validate" in composition.__doc__

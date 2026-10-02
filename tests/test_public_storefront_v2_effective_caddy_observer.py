"""Focused offline tests for the dedicated effective-Caddy V2 observer."""

from pathlib import Path
from types import SimpleNamespace
import pytest

from ops.macos.shopping import public_storefront_v2_effective_caddy_observer as observer


def _classification():
    return SimpleNamespace(
        production=SimpleNamespace(hostname="bokstory.duckdns.org", port=58082,
                                   authentication_required=False),
        preview=SimpleNamespace(hostname="dev.bokstory.duckdns.org", port=18080,
                                authentication_required=True),
    )


def _adapted():
    return {"apps": {"http": {"servers": {"production": {"listen": [":58082"]}}}},
            "upstreams": ["127.0.0.1:58082", "127.0.0.1:58081"]}


def _source():
    return ("@public_shopping_read @public_shopping_namespace @management_namespace "
            "@wordpress_namespace @shopping_rest_route_ambiguous handle @public_shopping_read "
            "@legacy_storefront redir @legacy_storefront / 301 127.0.0.1:58081")


def _trusted_caddy_fixture(tmp_path, monkeypatch, version="future"):
    root = tmp_path / "homebrew"
    entrypoint = root / "bin" / "caddy"
    target = root / "Cellar" / "caddy" / version / "bin" / "caddy"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"trusted caddy")
    target.chmod(0o755)
    entrypoint.parent.mkdir(parents=True)
    entrypoint.symlink_to(target)
    monkeypatch.setattr(observer, "CADDY", str(entrypoint))
    monkeypatch.setattr(observer, "_TRUSTED_HOMEBREW_ROOT", root)
    return root, entrypoint, target


def _process_lsof(target):
    return (
        b"p123\nccaddy\nn127.0.0.1:2019\nn*:58080\nn*:58443\n",
        f"p123\nftxt\nn{target}\n".encode(),
    )


def test_trusted_caddy_symlink_resolves_into_cellar(tmp_path, monkeypatch):
    _, entrypoint, target = _trusted_caddy_fixture(tmp_path, monkeypatch, "arbitrary-version")
    assert entrypoint.is_symlink()
    assert observer._trusted_caddy_executable() == str(target)


def test_matching_resolved_lsof_executable_passes(tmp_path, monkeypatch):
    _, _, target = _trusted_caddy_fixture(tmp_path, monkeypatch)
    outputs = list(_process_lsof(target))
    monkeypatch.setattr(observer, "_run", lambda *args, **kwargs: outputs.pop(0))
    observer._prove_caddy_process(tmp_path)


def test_matching_resolved_lsof_executable_among_normal_txt_mappings_passes(tmp_path, monkeypatch):
    _, _, target = _trusted_caddy_fixture(tmp_path, monkeypatch)
    outputs = [
        b"p123\nccaddy\nn127.0.0.1:2019\nn*:58080\nn*:58443\n",
        f"p123\nftxt\nn{tmp_path / 'Cellar' / 'caddy' / 'future' / 'lib' / 'caddy.so'}\n"
        f"ftxt\nn{target}\n".encode(),
    ]
    monkeypatch.setattr(observer, "_run", lambda *args, **kwargs: outputs.pop(0))
    observer._prove_caddy_process(tmp_path)


@pytest.mark.parametrize("raw", [b"", b"n\n", b"xnot-a-mapping\n"])
def test_malformed_txt_mappings_fail_closed(tmp_path, monkeypatch, raw):
    _, _, target = _trusted_caddy_fixture(tmp_path, monkeypatch)
    outputs = [
        b"p123\nccaddy\nn127.0.0.1:2019\nn*:58080\nn*:58443\n",
        b"p123\nftxt\n" + raw,
    ]
    monkeypatch.setattr(observer, "_run", lambda *args, **kwargs: outputs.pop(0))
    with pytest.raises(RuntimeError, match="CADDY_PROCESS_IDENTITY_UNPROVEN"):
        observer._prove_caddy_process(tmp_path)


@pytest.mark.parametrize("observed", [
    "/opt/homebrew/Cellar/caddy/other-version/bin/caddy",
    "/tmp/attacker/caddy",
])
def test_nonmatching_or_basename_spoof_lsof_executable_fails(tmp_path, monkeypatch, observed):
    _trusted_caddy_fixture(tmp_path, monkeypatch)
    outputs = [
        b"p123\nccaddy\nn127.0.0.1:2019\nn*:58080\nn*:58443\n",
        f"p123\nftxt\nn{observed}\n".encode(),
    ]
    monkeypatch.setattr(observer, "_run", lambda *args, **kwargs: outputs.pop(0))
    with pytest.raises(RuntimeError, match="CADDY_PROCESS_IDENTITY_UNPROVEN"):
        observer._prove_caddy_process(tmp_path)


def test_outside_homebrew_executable_fails(tmp_path, monkeypatch):
    root, entrypoint, _ = _trusted_caddy_fixture(tmp_path, monkeypatch)
    outside = tmp_path / "outside" / "caddy"
    outside.parent.mkdir()
    outside.write_bytes(b"spoof")
    outside.chmod(0o755)
    entrypoint.unlink()
    entrypoint.symlink_to(outside)
    with pytest.raises(RuntimeError, match="CADDY_TRUSTED_EXECUTABLE_UNPROVEN"):
        observer._trusted_caddy_executable()
    assert root in entrypoint.parent.parents


def test_broken_caddy_symlink_fails_closed(tmp_path, monkeypatch):
    _, entrypoint, _ = _trusted_caddy_fixture(tmp_path, monkeypatch)
    entrypoint.unlink()
    entrypoint.symlink_to(entrypoint.parent / "missing-caddy")
    with pytest.raises(RuntimeError, match="CADDY_TRUSTED_EXECUTABLE_UNAVAILABLE"):
        observer._trusted_caddy_executable()


def test_caddy_validation_has_no_version_literal():
    assert "2.11.4" not in Path(observer.__file__).read_text()


def test_effective_v2_requires_exact_loaded_adaptation_and_closed_flags(monkeypatch, tmp_path):
    expected = _adapted()
    monkeypatch.setattr(observer, "_prove_caddy_process", lambda runtime_root: None)
    monkeypatch.setattr(observer, "_read_loaded", lambda runtime_root: expected)
    monkeypatch.setattr(observer, "_adapt_reviewed", lambda reviewed_root, runtime_root: expected)
    monkeypatch.setattr(observer, "_reviewed_semantics", lambda reviewed_root: (_classification(), _source(), "{}"))

    result = observer.observe_caddy_effective_v2(reviewed_root=tmp_path, runtime_root=tmp_path)

    assert result["status"] == "PASS"
    assert all(result[key] is True for key in observer._PROOF_KEYS)
    assert "loaded" not in result
    assert "config" not in result


def test_effective_v2_mismatch_fails_closed_without_loaded_document(monkeypatch, tmp_path):
    monkeypatch.setattr(observer, "_prove_caddy_process", lambda runtime_root: None)
    monkeypatch.setattr(observer, "_read_loaded", lambda runtime_root: {"apps": {"synthetic": "loaded"}})
    monkeypatch.setattr(observer, "_adapt_reviewed", lambda reviewed_root, runtime_root: _adapted())
    monkeypatch.setattr(observer, "_reviewed_semantics", lambda reviewed_root: (_classification(), _source(), "{}"))

    result = observer.observe_caddy_effective_v2(reviewed_root=tmp_path, runtime_root=tmp_path)

    assert result["status"] == "BLOCKED"
    assert result["failure_code"] == "CADDY_V2_SEMANTICS_MISMATCH"
    assert all(result[key] is False for key in observer._PROOF_KEYS)
    assert "synthetic" not in str(result)


def test_pre_v2_accepts_only_observed_mismatch(monkeypatch, tmp_path):
    monkeypatch.setattr(observer, "_prove_caddy_process", lambda runtime_root: None)
    monkeypatch.setattr(observer, "_read_loaded", lambda runtime_root: {"apps": {"legacy": True}})
    monkeypatch.setattr(observer, "_adapt_reviewed", lambda reviewed_root, runtime_root: _adapted())
    result = observer.observe_pre_v2(reviewed_root=Path(tmp_path), runtime_root=Path(tmp_path))
    assert result["status"] == "PASS"
    assert result["caddy_state"] == "PRE_V2"

    monkeypatch.setattr(observer, "_read_loaded", lambda runtime_root: _adapted())
    result = observer.observe_pre_v2(reviewed_root=Path(tmp_path), runtime_root=Path(tmp_path))
    assert result["status"] == "BLOCKED"
    assert result["failure_code"] == "CADDY_ALREADY_V2"

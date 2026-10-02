"""Focused offline tests for the dedicated effective-Caddy V2 observer."""

from pathlib import Path
from types import SimpleNamespace

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
    return ("@public_shopping_read @management_namespace @wordpress_namespace "
            "@shopping_rest_route_ambiguous 127.0.0.1:58081")


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

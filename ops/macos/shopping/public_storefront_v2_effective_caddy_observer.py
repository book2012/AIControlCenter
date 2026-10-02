"""Dedicated read-only effective-Caddy proof for storefront V2 activation.

This adapter is intentionally independent of the general runtime attestor.  It
returns only fixed proof flags and fixed failure codes: the loaded Caddy JSON,
configuration text, credentials, headers, and response bodies never cross the
activation boundary.
"""

from __future__ import annotations

import json
import os
import pwd
from pathlib import Path
import stat
import subprocess
from typing import Any

from core.deployment.adapters.macos.caddy_sites import classify_caddy_sites, load_site_policy
from core.deployment.contracts import load_schema_registry, validate_contract_payload
from core.shopping.public_storefront_v2_activation_03_final_reconciliation import (
    CADDYFILE, CADDY_POLICY, DEV_HOST, DEV_PORT, INGRESS, PUBLIC_HOST, PUBLIC_PORT,
)


CADDY = "/opt/homebrew/bin/caddy"
_TRUSTED_HOMEBREW_ROOT = Path("/opt/homebrew")
_LIMIT = 262144
_CADDY_LISTENERS = ("127.0.0.1:2019", "*:58080", "*:58443")
_PROOF_KEYS = (
    "loaded_config_matches_reviewed_adaptation", "production_host", "public_root_upstream",
    "shopping_read_upstream", "public_get_allowlist_matcher_loaded",
    "private_management_matcher_loaded", "wordpress_rest_matcher_loaded",
    "raw_query_rest_route_ambiguity_guard_loaded", "dev_host", "dev_basic_auth_loaded",
    "public_has_no_basic_auth",
)


def _env() -> dict[str, str]:
    return {"PATH": "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin", "HOME": "/var/empty", "LC_ALL": "C"}


def _run(argv: list[str], *, cwd: Path, timeout: int = 10) -> bytes:
    result = subprocess.run(
        argv, cwd=cwd, env=_env(), stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=timeout, check=False,
    )
    if result.returncode != 0 or len(result.stdout) > _LIMIT:
        raise RuntimeError("CADDY_OBSERVATION_UNAVAILABLE")
    return result.stdout


def _json(raw: bytes) -> dict[str, Any]:
    if len(raw) > _LIMIT:
        raise RuntimeError("CADDY_OBSERVATION_OVERSIZED")

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise RuntimeError("CADDY_OBSERVATION_DUPLICATE_KEY")
            value[key] = item
        return value

    value = json.loads(raw, object_pairs_hook=unique, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    if type(value) is not dict:
        raise RuntimeError("CADDY_OBSERVATION_INVALID_JSON")
    return value


def _admin_json(raw: bytes) -> dict[str, Any]:
    body, separator, status = raw.rpartition(b"\n")
    if not separator or status != b"200":
        raise RuntimeError("CADDY_ADMIN_READ_FAILED")
    return _json(body)


def _trusted_caddy_executable() -> str:
    """Resolve and validate the fixed Homebrew Caddy entrypoint."""
    entrypoint = Path(CADDY)
    root = _TRUSTED_HOMEBREW_ROOT
    try:
        resolved = entrypoint.resolve(strict=True)
        metadata = resolved.stat()
        trusted_uid = pwd.getpwuid(os.getuid()).pw_uid
    except (KeyError, OSError, RuntimeError) as error:
        raise RuntimeError("CADDY_TRUSTED_EXECUTABLE_UNAVAILABLE") from error
    try:
        parts = resolved.relative_to(root).parts
    except ValueError as error:
        raise RuntimeError("CADDY_TRUSTED_EXECUTABLE_UNPROVEN") from error
    if (entrypoint != root / "bin" / "caddy" or len(parts) != 5
            or parts[:2] != ("Cellar", "caddy") or not parts[2]
            or parts[3:] != ("bin", "caddy")):
        raise RuntimeError("CADDY_TRUSTED_EXECUTABLE_UNPROVEN")
    if (not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid not in (0, trusted_uid)
            or metadata.st_mode & 0o022
            or not metadata.st_mode & 0o111):
        raise RuntimeError("CADDY_TRUSTED_EXECUTABLE_UNSAFE")

    shared = {root, root / "bin", root / "Cellar"}
    parents = {root, entrypoint.parent}
    current = root
    for component in parts[:-1]:
        current = current / component
        parents.add(current)
    try:
        for parent in parents:
            parent_metadata = parent.stat()
            shared_admin_write = (
                parent in shared
                and parent_metadata.st_uid == trusted_uid
                and parent_metadata.st_gid == 80
            )
            if (parent.is_symlink()
                    or not stat.S_ISDIR(parent_metadata.st_mode)
                    or parent_metadata.st_uid not in (0, trusted_uid)
                    or parent_metadata.st_mode & 0o002
                    or (parent_metadata.st_mode & 0o020 and not shared_admin_write)):
                raise RuntimeError("CADDY_TRUSTED_EXECUTABLE_UNSAFE")
    except OSError as error:
        raise RuntimeError("CADDY_TRUSTED_EXECUTABLE_UNAVAILABLE") from error
    return str(resolved)


def _prove_caddy_process(runtime_root: Path) -> None:
    raw = _run([
        "/usr/sbin/lsof", "-nP", "-Fpcn", "-a", "-iTCP:2019", "-iTCP:58080",
        "-iTCP:58443", "-sTCP:LISTEN",
    ], cwd=runtime_root)
    lines = raw.decode("ascii", errors="strict").splitlines()
    pids = [line[1:] for line in lines if line.startswith("p") and line[1:].isdigit()]
    commands = [line[1:] for line in lines if line.startswith("c")]
    names = [line[1:] for line in lines if line.startswith("n")]
    if (len(pids) != 1 or commands != ["caddy"] or sorted(names) != sorted(_CADDY_LISTENERS)
            or any(line[:1] not in {"p", "c", "n", "f"} for line in lines)):
        raise RuntimeError("CADDY_PROCESS_IDENTITY_UNPROVEN")
    trusted_executable = _trusted_caddy_executable()
    executable = _run(["/usr/sbin/lsof", "-a", "-p", pids[0], "-d", "txt", "-Fn"], cwd=runtime_root)
    executable_lines = executable.decode("utf-8", errors="strict").splitlines()
    if (len(executable_lines) != 1 or not executable_lines[0].startswith("n")
            or executable_lines[0][1:] != trusted_executable):
        raise RuntimeError("CADDY_PROCESS_IDENTITY_UNPROVEN")


def _read_loaded(runtime_root: Path) -> dict[str, Any]:
    return _admin_json(_run([
        "/usr/bin/curl", "-q", "--silent", "--fail", "--noproxy", "*", "--proxy", "",
        "--max-time", "4", "--max-filesize", str(_LIMIT), "--proto", "=http",
        "--write-out", "\n%{http_code}", "http://127.0.0.1:2019/config/",
    ], cwd=runtime_root, timeout=8))


def _adapt_reviewed(reviewed_root: Path, runtime_root: Path) -> dict[str, Any]:
    return _json(_run([
        CADDY, "adapt", "--config", str(reviewed_root / CADDYFILE), "--adapter", "caddyfile",
    ], cwd=runtime_root, timeout=15))


def _reviewed_semantics(reviewed_root: Path) -> tuple[Any, str, str]:
    caddyfile = reviewed_root / CADDYFILE
    policy = load_site_policy((reviewed_root / CADDY_POLICY).read_text())
    ingress = json.loads((reviewed_root / INGRESS).read_text())
    classification = classify_caddy_sites(caddyfile.read_text(), policy=policy, ingress_contract=ingress)
    registry = load_schema_registry()
    validate_contract_payload(registry=registry, contract_name="CaddySitePolicy", payload=policy)
    return classification, caddyfile.read_text(), json.dumps(ingress, sort_keys=True, separators=(",", ":"))


def _failure(code: str) -> dict[str, Any]:
    return {"status": "BLOCKED", "failure_code": code, **dict.fromkeys(_PROOF_KEYS, False)}


def observe_pre_v2(*, reviewed_root: Path, runtime_root: Path) -> dict[str, Any]:
    """Prove the current loaded document is not already the reviewed V2 document."""
    try:
        reviewed_root = reviewed_root.resolve(strict=True)
        runtime_root = runtime_root.resolve(strict=True)
        _prove_caddy_process(runtime_root)
        loaded = _read_loaded(runtime_root)
        adapted = _adapt_reviewed(reviewed_root, runtime_root)
        if loaded == adapted:
            return _failure("CADDY_ALREADY_V2")
        return {"status": "PASS", "caddy_state": "PRE_V2", "loaded_config_matches_reviewed_adaptation": False}
    except Exception:
        return _failure("CADDY_PRE_V2_OBSERVATION_UNAVAILABLE")


def observe_caddy_effective_v2(*, reviewed_root: Path, runtime_root: Path) -> dict[str, Any]:
    """Prove loaded Caddy JSON equals reviewed adaptation and closed semantics."""
    result = _failure("CADDY_V2_OBSERVATION_UNAVAILABLE")
    try:
        reviewed_root = reviewed_root.resolve(strict=True)
        runtime_root = runtime_root.resolve(strict=True)
        _prove_caddy_process(runtime_root)
        loaded = _read_loaded(runtime_root)
        adapted = _adapt_reviewed(reviewed_root, runtime_root)
        classification, source_text, _ = _reviewed_semantics(reviewed_root)
        production = classification.production
        preview = classification.preview
        adapted_text = json.dumps(adapted, sort_keys=True, separators=(",", ":"))
        exact = loaded == adapted
        flags = {
            "loaded_config_matches_reviewed_adaptation": exact,
            "production_host": exact and production.hostname == PUBLIC_HOST,
            "public_root_upstream": exact and production.port == PUBLIC_PORT and "127.0.0.1:58082" in adapted_text,
            "shopping_read_upstream": exact and "127.0.0.1:58081" in adapted_text,
            "public_get_allowlist_matcher_loaded": exact and "@public_shopping_read" in source_text,
            "private_management_matcher_loaded": exact and "@management_namespace" in source_text,
            "wordpress_rest_matcher_loaded": exact and "@wordpress_namespace" in source_text,
            "raw_query_rest_route_ambiguity_guard_loaded": exact and "@shopping_rest_route_ambiguous" in source_text,
            "dev_host": exact and preview is not None and preview.hostname == DEV_HOST and preview.port == DEV_PORT,
            "dev_basic_auth_loaded": exact and preview is not None and preview.authentication_required is True,
            "public_has_no_basic_auth": exact and production.authentication_required is False,
        }
        return {"status": "PASS" if all(flags.values()) else "BLOCKED",
                "failure_code": "NONE" if all(flags.values()) else "CADDY_V2_SEMANTICS_MISMATCH",
                **flags}
    except Exception:
        return result


__all__ = ("observe_caddy_effective_v2", "observe_pre_v2")

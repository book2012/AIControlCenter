"""Deterministic, local-only AST validation of DPL dependency boundaries."""

from __future__ import annotations

import ast
import hashlib
import json
from fnmatch import fnmatchcase
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator, FormatChecker

_SCHEMA_VERSION = "dpl/v1"
_POLICY_CONTRACT = "DependencyBoundaryPolicy"
_REPORT_CONTRACT = "DependencyBoundaryReport"


class DependencyBoundaryPolicyError(ValueError):
    """Raised when inputs or policy cannot be safely analyzed."""


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def _safe_relative(value: str, *, field: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise DependencyBoundaryPolicyError(f"{field} must be a repository-relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise DependencyBoundaryPolicyError(f"{field} must not be absolute or traverse")
    return path


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DependencyBoundaryPolicyError("unable to read JSON policy asset") from error
    if not isinstance(value, dict):
        raise DependencyBoundaryPolicyError("policy must be a JSON object")
    return value


def _schema(repo_root: Path, name: str) -> Mapping[str, Any]:
    registry_path = repo_root / "core/deployment/contracts/schemas/v1/registry.json"
    registry = _load_object(registry_path)
    binding = registry.get("contracts", {}).get(name)
    if not isinstance(binding, dict) or not isinstance(binding.get("path"), str):
        raise DependencyBoundaryPolicyError(f"missing {name} schema binding")
    relative = _safe_relative(binding["path"], field="schema path")
    if len(relative.parts) != 1:
        raise DependencyBoundaryPolicyError("schema binding must remain within v1 registry")
    return _load_object(registry_path.parent / relative)


def _schema_errors(schema: Mapping[str, Any], value: Mapping[str, Any]) -> list[str]:
    return [
        error.message
        for error in sorted(
            Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value),
            key=lambda item: (
                tuple(str(part) for part in item.absolute_path),
                str(item.validator),
                item.message,
            ),
        )
    ]


def _module_for_path(path: PurePosixPath) -> str:
    parts = list(path.parts)
    parts[-1] = parts[-1][:-3]
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _matches(module: str, relative_path: str, selectors: Sequence[Mapping[str, Any]]) -> bool:
    for selector in selectors:
        module_prefix = selector.get("module_prefix")
        path_glob = selector.get("path_glob")
        if isinstance(module_prefix, str) and (
            module == module_prefix or module.startswith(module_prefix + ".")
        ):
            return True
        if isinstance(path_glob, str) and fnmatchcase(relative_path, path_glob):
            return True
    return False


def _resolve_import(importer: str, node: ast.ImportFrom) -> str:
    if node.level == 0:
        return node.module or ""
    package = importer.split(".")[:-1]
    if node.level > len(package) + 1:
        return node.module or ""
    base = package[: len(package) - node.level + 1]
    if node.module:
        base.extend(node.module.split("."))
    return ".".join(base)


def _imports(tree: ast.AST, importer: str) -> list[tuple[str, tuple[str, ...], int]]:
    found: list[tuple[str, tuple[str, ...], int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend((alias.name, (), node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = _resolve_import(importer, node)
            found.append((module, tuple(sorted(alias.name for alias in node.names)), node.lineno))
    return sorted(found, key=lambda item: (item[0], item[1], item[2]))


def _zone_for(
    module: str, relative_path: str, zones: Sequence[Mapping[str, Any]]
) -> str | None:
    matches = [
        zone["id"]
        for zone in zones
        if _matches(module, relative_path, zone["selectors"])
    ]
    return sorted(matches)[0] if matches else None


def _violation(
    *, importer: str, imported: str, rule: Mapping[str, Any], detail: str
) -> dict[str, Any]:
    return {
        "importer": importer,
        "imported_module": imported,
        "rule_id": rule["id"],
        "severity": rule["severity"],
        "detail": detail,
    }


def validate_dependency_boundaries(
    *,
    repository_root: Path,
    policy_path: str = "config/deployment/dependency-boundaries.json",
    paths: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Validate source imports without importing targets or executing commands."""

    root = repository_root.resolve()
    if not root.is_dir():
        raise DependencyBoundaryPolicyError("repository_root must be an existing directory")
    policy_relative = _safe_relative(policy_path, field="policy_path")
    policy = _load_object(root / policy_relative)
    policy_errors = _schema_errors(_schema(root, _POLICY_CONTRACT), policy)
    if policy_errors:
        raise DependencyBoundaryPolicyError("invalid policy: " + "; ".join(policy_errors))

    requested = (
        sorted({_safe_relative(item, field="path").as_posix() for item in paths})
        if paths is not None
        else sorted(
            path.relative_to(root).as_posix()
            for path in (root / "core").rglob("*.py")
            if path.is_file()
        )
    )
    for relative in requested:
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as error:
            raise DependencyBoundaryPolicyError("path escaped repository root") from error
        if not candidate.is_file() or candidate.suffix != ".py":
            raise DependencyBoundaryPolicyError(f"path is not a Python source file: {relative}")

    zones = policy["architecture_zones"]
    quarantines = {item["module"]: item for item in policy["legacy_quarantine"]}
    direction_rules = policy["dependency_rules"]
    allowed_directions = {
        item["from_zone"]: set(item["to_zones"])
        for item in policy["allowed_dependency_directions"]
    }
    external_rules = policy["prohibited_external_modules"]
    symbol_rules = policy["prohibited_symbols"]
    classified: list[dict[str, str]] = []
    allowed: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []
    quarantine_findings: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []

    for relative in requested:
        relative_path = PurePosixPath(relative)
        module = _module_for_path(relative_path)
        zone = _zone_for(module, relative, zones)
        quarantine = quarantines.get(module)
        if quarantine is not None:
            zone = "legacy_unsupported"
        if module.startswith("core.deployment") and zone is None:
            violations.append(
                {
                    "importer": module,
                    "imported_module": "",
                    "rule_id": "DPL-ZONE-001",
                    "severity": "ERROR",
                    "detail": "deployment module is not classified by policy",
                }
            )
            continue
        if zone is None:
            continue
        classified.append({"module": module, "path": relative, "zone": zone})
        try:
            tree = ast.parse((root / relative).read_text(encoding="utf-8"), filename=relative)
        except (OSError, UnicodeDecodeError, SyntaxError) as error:
            warnings.append({"module": module, "warning": f"source could not be analyzed: {type(error).__name__}"})
            continue
        imports = _imports(tree, module)
        if quarantine is not None:
            sensitive = sorted(
                imported
                for imported, _, _ in imports
                if any(
                    imported == prefix or imported.startswith(prefix + ".")
                    for rule in external_rules
                    for prefix in rule["modules"]
                )
            )
            quarantine_findings.append(
                {
                    "module": module,
                    "classification": "LEGACY_UNSUPPORTED",
                    "reason": quarantine["reason"],
                    "sensitive_imports": sensitive,
                    "production_authorized": False,
                }
            )
        for imported, symbols, line in imports:
            imported_zone = _zone_for(imported, "", zones)
            if imported in quarantines:
                imported_zone = "legacy_unsupported"
            matched = False
            if (
                imported_zone is not None
                and zone in allowed_directions
                and imported_zone not in allowed_directions[zone]
            ):
                violations.append(
                    {
                        "importer": module,
                        "imported_module": imported,
                        "rule_id": "DPL-DIRECTION-000",
                        "severity": "ERROR",
                        "detail": f"dependency is outside the allowed direction at line {line}",
                    }
                )
                matched = True
            for rule in direction_rules:
                if zone in rule["from_zones"] and imported_zone in rule["to_zones"]:
                    violations.append(
                        _violation(
                            importer=module,
                            imported=imported,
                            rule=rule,
                            detail=f"prohibited zone dependency at line {line}",
                        )
                    )
                    matched = True
            for rule in external_rules:
                if zone in rule["zones"] and any(
                    imported == prefix or imported.startswith(prefix + ".")
                    for prefix in rule["modules"]
                ):
                    violations.append(
                        _violation(
                            importer=module,
                            imported=imported,
                            rule=rule,
                            detail=f"prohibited external module at line {line}",
                        )
                    )
                    matched = True
            for rule in symbol_rules:
                if zone in rule["zones"] and any(symbol in rule["symbols"] for symbol in symbols):
                    violations.append(
                        _violation(
                            importer=module,
                            imported=imported,
                            rule=rule,
                            detail=f"prohibited imported symbol at line {line}",
                        )
                    )
                    matched = True
            if not matched:
                allowed.append(
                    {
                        "importer": module,
                        "imported_module": imported,
                        "symbols": list(symbols),
                    }
                )

    key = lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"))
    report = {
        "schema_version": _SCHEMA_VERSION,
        "policy_digest": "sha256:" + hashlib.sha256(_canonical_bytes(policy)).hexdigest(),
        "repository_root_identity": root.name,
        "analyzed_files": requested,
        "classified_modules": sorted(classified, key=key),
        "allowed_imports": sorted(allowed, key=key),
        "violations": sorted(violations, key=key),
        "quarantine_findings": sorted(quarantine_findings, key=key),
        "warnings": sorted(warnings, key=key),
        "overall_result": "FAIL" if violations else ("INCOMPLETE" if warnings else "PASS"),
        "production_authorized": False,
        "production_writes": 0,
        "ubuntu_changes": 0,
    }
    report_errors = _schema_errors(_schema(root, _REPORT_CONTRACT), report)
    if report_errors:
        raise DependencyBoundaryPolicyError("invalid report: " + "; ".join(report_errors))
    return report


__all__ = ("DependencyBoundaryPolicyError", "validate_dependency_boundaries")

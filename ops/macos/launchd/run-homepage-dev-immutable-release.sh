#!/usr/bin/env bash

set -Eeuo pipefail
umask 077

# This file is a future installed wrapper.  It is intentionally not an
# installer and does not contain a supervisor lifecycle operation.
HOME_DIR="${AICONTROLCENTER_HOME:-${HOME:-}}"
RELEASE_ROOT="${AICONTROLCENTER_DEV_RELEASE_ROOT:-$HOME_DIR/Library/Application Support/AIControlCenter/releases/homepage-dev}"
PYTHON_PATH="${AICONTROLCENTER_DEV_PYTHON:-$HOME_DIR/AIControlCenter/.venv/bin/python}"
SAFE_PATH="${PATH:-/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin}"
CURRENT_MANIFEST="$RELEASE_ROOT/current.json"

if [[ -z "$HOME_DIR" || "$RELEASE_ROOT" != /* || "$PYTHON_PATH" != /* ]]; then
  echo "Homepage DEV runtime configuration is invalid" >&2
  exit 78
fi
if [[ ! -x "$PYTHON_PATH" ]]; then
  echo "Configured Homepage DEV Python interpreter is unavailable" >&2
  exit 78
fi
if [[ ! -d "$RELEASE_ROOT" || -L "$RELEASE_ROOT" || ! -f "$CURRENT_MANIFEST" || -L "$CURRENT_MANIFEST" ]]; then
  echo "Homepage DEV current release manifest is unavailable" >&2
  exit 78
fi

# Validate only JSON metadata and release-owned paths before importing any
# release code.  No .env file is read and no working-tree module is imported.
/usr/bin/env -i \
  HOME="$HOME_DIR" \
  PATH="$SAFE_PATH" \
  PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  "$PYTHON_PATH" - "$RELEASE_ROOT" "$CURRENT_MANIFEST" <<'PY'
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

root = Path(sys.argv[1])
manifest_path = Path(sys.argv[2])
try:
    value = json.loads(manifest_path.read_text(encoding="utf-8"))
    required = {
        "schema_version", "environment", "service", "git_commit", "release_path",
        "created_at", "source_clean", "source_provenance", "presentation_identifier",
    }
    if not isinstance(value, dict) or not required.issubset(value):
        raise ValueError("manifest fields are incomplete")
    commit = value["git_commit"]
    if value["schema_version"] != 1 or value["environment"] != "dev" or value["service"] != "homepage":
        raise ValueError("manifest identity is invalid")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("manifest commit is invalid")
    datetime.fromisoformat(str(value["created_at"]).replace("Z", "+00:00"))
    provenance = value["source_provenance"]
    if value["source_clean"] is not True or not isinstance(provenance, dict):
        raise ValueError("manifest source is not clean")
    if (provenance.get("method") != "git_archive"
            or provenance.get("archived_revision") != commit
            or provenance.get("working_tree_clean") is not True):
        raise ValueError("manifest provenance is invalid")
    expected = (root / "releases" / commit).absolute()
    if value["release_path"] != str(expected):
        raise ValueError("manifest release_path is unexpected")
    if expected.is_symlink() or not expected.is_dir() or expected.resolve() != expected:
        raise ValueError("release directory is unavailable or escaped")
    marker_path = expected / ".aicontrolcenter-release.json"
    if marker_path.is_symlink() or not marker_path.is_file():
        raise ValueError("release provenance marker is unavailable")
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    if marker != value:
        raise ValueError("release provenance marker does not match current manifest")
    for required_path in (expected / "core/homepage/preview.py", expected / "core/homepage/__init__.py"):
        if required_path.is_symlink() or not required_path.is_file():
            raise ValueError("release-owned Homepage runtime is incomplete")
except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
    print(f"Homepage DEV release rejected: {exc}", file=sys.stderr)
    raise SystemExit(78)
PY

RELEASE_PATH="$RELEASE_ROOT/releases/$(/usr/bin/env -i \
  HOME="$HOME_DIR" \
  PATH="$SAFE_PATH" \
  PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  "$PYTHON_PATH" -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["git_commit"])' \
  "$CURRENT_MANIFEST")"
if [[ ! -d "$RELEASE_PATH" || -L "$RELEASE_PATH" ]]; then
  echo "Homepage DEV release path disappeared" >&2
  exit 78
fi

cd "$RELEASE_PATH"
exec /usr/bin/env -i \
  HOME="$HOME_DIR" \
  PATH="$SAFE_PATH" \
  PYTHONPATH="$RELEASE_PATH" \
  PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  "$PYTHON_PATH" -P -m uvicorn core.homepage.preview:create_app \
  --factory --host 127.0.0.1 --port 18080 --no-access-log --log-level warning

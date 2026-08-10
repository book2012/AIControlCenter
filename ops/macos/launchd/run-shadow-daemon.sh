#!/usr/bin/env bash

set -eu

WORKER_ENV_FILE="${AICONTROLCENTER_WORKER_ENV_FILE:-/Library/Application Support/AIControlCenter/worker.env}"

if [ -f "$WORKER_ENV_FILE" ]; then
  OWNER="$(stat -f "%Su" "$WORKER_ENV_FILE")"
  GROUP="$(stat -f "%Sg" "$WORKER_ENV_FILE")"
  MODE="$(stat -f "%OLp" "$WORKER_ENV_FILE")"

  if [ "$OWNER" != "root" ]; then
    echo "[FAIL] Worker environment must be owned by root" >&2
    exit 1
  fi

  if [ "$GROUP" != "staff" ]; then
    echo "[FAIL] Worker environment group must be staff" >&2
    exit 1
  fi

  if [ "$MODE" != "640" ]; then
    echo "[FAIL] Worker environment permissions must be 640" >&2
    exit 1
  fi

  set -a
  . "$WORKER_ENV_FILE"
  set +a
fi

set -Eeuo pipefail

umask 077

HOME_DIR="${AICONTROLCENTER_HOME:-/Users/kyouhan}"
RUN_USER="${AICONTROLCENTER_RUN_USER:-kyouhan}"
ACTIVE_PROVIDER="${AI_PROVIDER:-openai}"
SECRET_DELIVERY="${AICONTROLCENTER_SECRET_DELIVERY:-/usr/local/libexec/aicontrolcenter/provider-secret-delivery.py}"

RUNTIME_ROOT="$HOME_DIR/Library/Application Support/AIControlCenter/runtime"
CURRENT_RUNTIME="$RUNTIME_ROOT/current"

HOST="${AICONTROLCENTER_SHADOW_HOST:-127.0.0.1}"
PORT="${AICONTROLCENTER_SHADOW_PORT:-18100}"

export HOME="$HOME_DIR"
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
export AICONTROLCENTER_MODE="shadow-read-only"

if [[ "$(/usr/bin/id -un)" != "$RUN_USER" ]]
then
    echo "Unexpected runtime user" >&2
    exit 78
fi


if [[ ! -L "$CURRENT_RUNTIME" ]]
then
    echo "Current production runtime is not active" >&2
    exit 78
fi

RUNTIME_TARGET="$(
    /usr/bin/readlink "$CURRENT_RUNTIME"
)"

if [[ "$RUNTIME_TARGET" != /* ]]
then
    RUNTIME_TARGET="$RUNTIME_ROOT/$RUNTIME_TARGET"
fi

PYTHON_PATH="$RUNTIME_TARGET/bin/python"

if [[ ! -x "$PYTHON_PATH" ]]
then
    echo "Current runtime Python is unavailable" >&2
    exit 78
fi


# Mutable repository is not a Production application source.

unset PYTHONPATH

AICONTROLCENTER_APPLICATION_ROOT="${AICONTROLCENTER_APPLICATION_ROOT:-$HOME/Library/Application Support/AIControlCenter}"
AICONTROLCENTER_RUNTIME_LINK="${AICONTROLCENTER_RUNTIME_LINK:-$AICONTROLCENTER_APPLICATION_ROOT/runtime/current}"
AICONTROLCENTER_DATA_ROOT="${AICONTROLCENTER_DATA_ROOT:-$AICONTROLCENTER_APPLICATION_ROOT/data}"

AICONTROLCENTER_CURRENT_RELEASE="$(
  python3 -c \
    'import os,sys; print(os.path.realpath(sys.argv[1]))' \
    "$AICONTROLCENTER_RUNTIME_LINK"
)"

AICONTROLCENTER_RUNTIME_RELEASE="$(
  basename "$AICONTROLCENTER_CURRENT_RELEASE"
)"

AICONTROLCENTER_SOURCE_COMMIT_FILE="$AICONTROLCENTER_CURRENT_RELEASE/.aicontrolcenter-source-commit"

if [ ! -f "$AICONTROLCENTER_SOURCE_COMMIT_FILE" ]; then
  echo "AIControlCenter source commit metadata is missing" >&2
  exit 78
fi

AICONTROLCENTER_SOURCE_COMMIT="$(
  tr -d '\r\n[:space:]' \
    < "$AICONTROLCENTER_SOURCE_COMMIT_FILE"
)"

if ! printf '%s\n' "$AICONTROLCENTER_SOURCE_COMMIT" |
  grep -Eq '^[0-9a-f]{40}$'
then
  echo "AIControlCenter source commit metadata is invalid" >&2
  exit 78
fi

case "$AICONTROLCENTER_RUNTIME_RELEASE" in
  ""|*[!0-9a-f]*)
    echo "AIControlCenter runtime release identity is invalid" >&2
    exit 78
    ;;
esac

if [ ! -d "$AICONTROLCENTER_CURRENT_RELEASE" ]; then
  echo "AIControlCenter current release is unavailable" >&2
  exit 78
fi

mkdir -p "$AICONTROLCENTER_DATA_ROOT"

export AICONTROLCENTER_SOURCE_COMMIT
export AICONTROLCENTER_RUNTIME_RELEASE
export AICONTROLCENTER_DATA_ROOT


RUNTIME_ID="$(
    /usr/bin/basename "$RUNTIME_TARGET"
)"

SOURCE_PARENT="$RUNTIME_ROOT/sources"
SOURCE_ROOT="$SOURCE_PARENT/$RUNTIME_ID"

if [[ ! -d "$SOURCE_PARENT" || -L "$SOURCE_PARENT" ]]
then
    echo "AIControlCenter source parent is unavailable" >&2
    exit 78
fi

if [[ ! -d "$SOURCE_ROOT" || -L "$SOURCE_ROOT" ]]
then
    echo "AIControlCenter immutable source artifact is unavailable" >&2
    exit 78
fi

SOURCE_PARENT_REAL="$(
    cd "$SOURCE_PARENT" &&
    /bin/pwd -P
)"

SOURCE_REAL="$(
    cd "$SOURCE_ROOT" &&
    /bin/pwd -P
)"

if [[ "${SOURCE_REAL%/*}" != "$SOURCE_PARENT_REAL" ]]
then
    echo "AIControlCenter source artifact escaped source parent" >&2
    exit 78
fi

RUNTIME_SOURCE_MARKER="$RUNTIME_TARGET/.aicontrolcenter-source-commit"
SOURCE_SOURCE_MARKER="$SOURCE_REAL/.aicontrolcenter-source-commit"
SOURCE_MANIFEST="$SOURCE_REAL/.aicontrolcenter-source-manifest.json"

if [[ ! -f "$RUNTIME_SOURCE_MARKER" ||
      ! -f "$SOURCE_SOURCE_MARKER" ||
      ! -f "$SOURCE_MANIFEST" ]]
then
    echo "AIControlCenter immutable source identity is unavailable" >&2
    exit 78
fi

RUNTIME_SOURCE_COMMIT="$(
    /usr/bin/tr -d '\n' < "$RUNTIME_SOURCE_MARKER"
)"

SOURCE_SOURCE_COMMIT="$(
    /usr/bin/tr -d '\n' < "$SOURCE_SOURCE_MARKER"
)"

if [[ "${#RUNTIME_SOURCE_COMMIT}" -ne 40 ]] ||
   ! printf '%s\n' "$RUNTIME_SOURCE_COMMIT" |
       /usr/bin/grep -Eq '^[0-9a-f]{40}$'
then
    echo "AIControlCenter Runtime source identity is invalid" >&2
    exit 78
fi

if [[ "$RUNTIME_SOURCE_COMMIT" != "$SOURCE_SOURCE_COMMIT" ]]
then
    echo "AIControlCenter Runtime/source identity mismatch" >&2
    exit 78
fi

"$PYTHON_PATH" \
    -P \
    - "$SOURCE_REAL" "$SOURCE_MANIFEST" \
    "$SOURCE_SOURCE_MARKER" \
    "$RUNTIME_ID" "$RUNTIME_SOURCE_COMMIT" \
    <<'PY_VERIFY'
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import os
import re
import stat
import sys


root = Path(sys.argv[1]).resolve()
manifest_path = Path(sys.argv[2])
marker_path = Path(sys.argv[3])
runtime_id = sys.argv[4]
source_commit = sys.argv[5]

commit_re = re.compile(
    r"^[0-9a-f]{40}$"
)

sha256_re = re.compile(
    r"^[0-9a-f]{64}$"
)

marker = marker_path.read_bytes()

if marker != (
    source_commit + "\n"
).encode("ascii"):
    raise SystemExit(
        "AIControlCenter source marker is invalid"
    )

try:
    manifest = json.loads(
        manifest_path.read_text(
            encoding="utf-8"
        )
    )
except Exception as error:
    raise SystemExit(
        "AIControlCenter source manifest is invalid"
    ) from error

required = {
    "schema_version",
    "runtime_id",
    "source_commit",
    "git_tree",
    "archive_sha256",
    "content_sha256",
    "artifact_root",
    "build_status",
    "production_authorized",
}

if set(manifest) != required:
    raise SystemExit(
        "AIControlCenter source manifest fields are invalid"
    )

if manifest["schema_version"] != 1:
    raise SystemExit(
        "AIControlCenter source manifest schema is invalid"
    )

if manifest["runtime_id"] != runtime_id:
    raise SystemExit(
        "AIControlCenter source Runtime identity mismatch"
    )

if manifest["source_commit"] != source_commit:
    raise SystemExit(
        "AIControlCenter source commit mismatch"
    )

if (
    not isinstance(manifest["git_tree"], str)
    or commit_re.fullmatch(
        manifest["git_tree"]
    ) is None
):
    raise SystemExit(
        "AIControlCenter source Git tree identity is invalid"
    )

if manifest["artifact_root"] != str(root):
    raise SystemExit(
        "AIControlCenter source artifact root mismatch"
    )

if manifest["build_status"] != "COMPLETE":
    raise SystemExit(
        "AIControlCenter source build status is invalid"
    )

if manifest["production_authorized"] is not False:
    raise SystemExit(
        "AIControlCenter source Production flag is invalid"
    )

for field in (
    "archive_sha256",
    "content_sha256",
):
    value = manifest[field]

    if (
        not isinstance(value, str)
        or sha256_re.fullmatch(value) is None
    ):
        raise SystemExit(
            "AIControlCenter source digest metadata is invalid"
        )

required_files = (
    root / "core" / "api" / "shadow.py",
    root / "core" / "runtime" / "data_paths.py",
    root / "config" / "workers.yaml",
)

for required_file in required_files:
    if not required_file.is_file():
        raise SystemExit(
            "AIControlCenter required Runtime source asset is unavailable"
        )

if (root / ".git").exists():
    raise SystemExit(
        "AIControlCenter immutable source contains Git metadata"
    )

digest = hashlib.sha256()

for path in sorted(
    root.rglob("*"),
    key=lambda item: item.relative_to(root).as_posix(),
):
    relative = path.relative_to(root).as_posix()

    if relative == ".aicontrolcenter-source-manifest.json":
        continue

    info = path.lstat()

    if (
        not path.is_symlink()
        and stat.S_IMODE(info.st_mode) & 0o222
    ):
        raise SystemExit(
            "AIControlCenter immutable source is writable"
        )

    digest.update(
        relative.encode("utf-8")
    )
    digest.update(b"\0")

    if stat.S_ISLNK(info.st_mode):
        target = path.resolve(
            strict=False
        )

        try:
            target.relative_to(root)
        except ValueError as error:
            raise SystemExit(
                "AIControlCenter source symlink escaped artifact"
            ) from error

        digest.update(b"L\0")
        digest.update(
            os.readlink(path).encode("utf-8")
        )

    elif stat.S_ISDIR(info.st_mode):
        digest.update(b"D\0")

    elif stat.S_ISREG(info.st_mode):
        digest.update(b"F\0")

        with path.open("rb") as stream:
            for block in iter(
                lambda: stream.read(
                    1024 * 1024
                ),
                b"",
            ):
                digest.update(block)

    else:
        raise SystemExit(
            "AIControlCenter source contains unsupported object"
        )

    digest.update(b"\0")

if digest.hexdigest() != manifest["content_sha256"]:
    raise SystemExit(
        "AIControlCenter immutable source digest mismatch"
    )
PY_VERIFY

cd "$SOURCE_REAL"
export PYTHONPATH="$SOURCE_REAL"

exec /usr/bin/python3 "$SECRET_DELIVERY" exec --provider "$ACTIVE_PROVIDER" -- \
  "$PYTHON_PATH" \
  -P \
  -m uvicorn \
  core.api.shadow:app \
  --host "$HOST" \
  --port "$PORT"

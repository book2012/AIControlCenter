#!/usr/bin/env bash

set -Eeuo pipefail
IFS=$'\n\t'

PROJECT_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/../.." &&
    pwd
)"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_PATH="${PROJECT_ROOT}/.venv"
ENV_TEMPLATE="${PROJECT_ROOT}/.env.mac-production.example"
ENV_FILE="${PROJECT_ROOT}/.env.mac-production"
LOG_DIR="${PROJECT_ROOT}/var/log"
RUN_DIR="${PROJECT_ROOT}/var/run"

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "ERROR: bootstrap-macos.sh must run on macOS." >&2
    exit 1
fi

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
    echo "ERROR: Python 3 is not installed." >&2
    exit 1
fi

echo "Project root: ${PROJECT_ROOT}"
echo "Python: $(${PYTHON_BIN} --version)"

if [[ ! -d "${VENV_PATH}" ]]; then
    echo "Creating virtual environment..."
    "${PYTHON_BIN}" -m venv "${VENV_PATH}"
else
    echo "Virtual environment already exists."
fi

VENV_PYTHON="${VENV_PATH}/bin/python"

"${VENV_PYTHON}" -m pip install --upgrade pip

if [[ -f "${PROJECT_ROOT}/requirements.txt" ]]; then
    "${VENV_PYTHON}" -m pip install \
        -r "${PROJECT_ROOT}/requirements.txt"
fi

mkdir -p "${LOG_DIR}" "${RUN_DIR}"

if [[ ! -f "${ENV_FILE}" ]]; then
    cp "${ENV_TEMPLATE}" "${ENV_FILE}"
    chmod 0600 "${ENV_FILE}"

    echo
    echo "Created environment file:"
    echo "${ENV_FILE}"
    echo
    echo "Edit the Datacenter host, SSH user, MAC address,"
    echo "broadcast address, and required API credentials."
else
    echo "Environment file already exists."
fi

bash \
    "${PROJECT_ROOT}/deploy/macos/validate-macos-profile.sh"

echo
echo "Bootstrap completed."
echo
echo "Next:"
echo "1. Edit ${ENV_FILE}"
echo "2. Configure SSH key access"
echo "3. Run the remote smoke test"
echo "4. Install launchd after validation"

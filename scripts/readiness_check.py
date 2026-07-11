import subprocess
import sys
from pathlib import Path

import requests

from core.runtime.env_validation import EnvironmentTemplateValidator
from core.runtime.service_health import ServiceHealth


def command_ok(command: list[str]) -> bool:
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def main() -> int:
    checks = {}

    checks["env_template"] = EnvironmentTemplateValidator().validate()["valid"]
    checks["requirements"] = Path("requirements.txt").exists()
    checks["env_file"] = Path(".env").exists()
    checks["tests"] = command_ok([sys.executable, "-m", "pytest", "-q"])
    checks["git_clean"] = command_ok(["git", "diff", "--quiet"])

    try:
        response = requests.get(
            "http://localhost:8000/health",
            timeout=5,
        )
        checks["api"] = response.status_code == 200
    except requests.RequestException:
        checks["api"] = False

    checks["services"] = ServiceHealth().status()["healthy"]

    print("AIControlCenter Production Readiness")
    print()

    for name, passed in checks.items():
        marker = "OK" if passed else "FAIL"
        print(f"{marker:4} {name}")

    ready = all(checks.values())

    print()
    print(f"Overall: {'READY' if ready else 'NOT READY'}")

    return 0 if ready else 1


if __name__ == "__main__":
    sys.exit(main())

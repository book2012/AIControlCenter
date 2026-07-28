from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DEFAULT_CONTRACT = Path(__file__).with_name("commerce-runtime.json")


def load_contract(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("runtime contract must be a JSON object")
    return data


def resolve_mount(path_value: str) -> Path:
    relative = Path(path_value)
    if relative.is_absolute():
        raise ValueError("mount path must be repository-relative")
    if ".." in relative.parts:
        raise ValueError("mount path may not escape repository")
    resolved = (REPO / relative).resolve(strict=False)
    try:
        resolved.relative_to(REPO)
    except ValueError as error:
        raise ValueError("mount path escapes repository") from error
    if not resolved.exists():
        raise ValueError("mount source does not exist")
    return resolved


def validate_contract(data: dict[str, object]) -> None:
    required = {
        "schema_version": 1,
        "profile": "aicontrolcenter-commerce",
        "runtime": "docker",
        "architecture": "aarch64",
        "vm_type": "vz",
        "mount_type": "virtiofs",
        "cpus": 4,
        "memory_gib": 6,
        "disk_gib": 80,
        "kubernetes": False,
        "network_address": False,
        "network_mode": "shared",
        "port_forwarder": "ssh",
        "auto_activate": False,
        "ssh_agent": False,
        "mount_policy": "explicit-compose-bind-allowlist",
        "docker_context": "colima-aicontrolcenter-commerce",
        "ai_workloads_allowed": False,
        "ubuntu_runtime_allowed": False,
        "public_ingress_owner": "host-caddy",
        "wordpress_host_binding": "127.0.0.1:${SHOPPING_WORDPRESS_PORT}:80",
    }

    mismatches = {}

    for key, expected in required.items():
        actual = data.get(key)
        if actual != expected:
            mismatches[key] = {"expected": expected, "actual": actual}

    allowed = data.get("allowed_workloads")
    expected_allowed = [
        "wordpress",
        "woocommerce",
        "database",
        "wordpress-cli",
    ]

    if allowed != expected_allowed:
        mismatches["allowed_workloads"] = {
            "expected": expected_allowed,
            "actual": allowed,
        }

    expected_mounts = [
        {
            "path": "deploy/shopping/wordpress/plugins/ai-shopping-storefront",
            "writable": False,
        }
    ]

    mounts = data.get("mounts")

    if mounts != expected_mounts:
        mismatches["mounts"] = {
            "expected": expected_mounts,
            "actual": mounts,
        }
    else:
        for mount in mounts:
            resolve_mount(str(mount["path"]))

    if mismatches:
        raise ValueError(
            json.dumps(
                {"contract_mismatches": mismatches},
                separators=(",", ":"),
                sort_keys=True,
            )
        )


def build_start_argv(data: dict[str, object]) -> list[str]:
    colima = shutil.which("colima")
    if colima is None:
        raise RuntimeError("colima binary unavailable")

    argv = [
        colima,
        "start",
        str(data["profile"]),
        "--runtime",
        str(data["runtime"]),
        "--arch",
        str(data["architecture"]),
        "--vm-type",
        str(data["vm_type"]),
        "--mount-type",
        str(data["mount_type"]),
        "--cpus",
        str(data["cpus"]),
        "--memory",
        str(data["memory_gib"]),
        "--disk",
        str(data["disk_gib"]),
        "--network-mode",
        str(data["network_mode"]),
        "--port-forwarder",
        str(data["port_forwarder"]),
    ]

    for mount in data["mounts"]:
        source = resolve_mount(str(mount["path"]))
        value = str(source)
        if bool(mount["writable"]):
            value += ":w"
        argv.extend(["--mount", value])

    argv.extend(
        [
            "--activate=false",
            "--kubernetes=false",
            "--network-address=false",
            "--network-host-addresses=false",
            "--ssh-agent=false",
            "--save-config",
        ]
    )

    return argv


def build_plan(data: dict[str, object]) -> dict[str, object]:
    argv = build_start_argv(data)
    mounts = []

    for mount in data["mounts"]:
        mounts.append(
            {
                "source": str(resolve_mount(str(mount["path"]))),
                "writable": bool(mount["writable"]),
            }
        )

    return {
        "action": "plan",
        "result": "PASS",
        "profile": data["profile"],
        "docker_context": data["docker_context"],
        "mount_policy": data["mount_policy"],
        "mounts": mounts,
        "start_argv": argv,
        "runtime_start_performed": False,
        "container_start_performed": False,
        "network_address_enabled": False,
        "kubernetes_enabled": False,
        "auto_activate_enabled": False,
        "ai_workloads_allowed": False,
        "ubuntu_modified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--contract",
        type=Path,
        default=DEFAULT_CONTRACT,
    )
    parser.add_argument(
        "--action",
        choices=["plan"],
        default="plan",
    )
    args = parser.parse_args()

    data = load_contract(args.contract)
    validate_contract(data)
    result = build_plan(data)

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())

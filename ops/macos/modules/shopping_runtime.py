"""On-demand Shopping resources. Plan by default; --apply is explicit execution."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import subprocess
import sys
import time

PROFILE = "aicontrolcenter-commerce"
LABELS = ("com.aicontrolcenter.dev-telegram-papachichi", "com.aicontrolcenter.homepage-dev",
          "com.aicontrolcenter.prod-homepage", "com.aicontrolcenter.prod-commerce-api",
          "com.aicontrolcenter.dev-order-https-proxy", "com.aicontrolcenter.dev-order-api")
NAMES = ("shopping-wordpress", "shopping-db", "aicc-order-dev-wordpress-1",
         "aicc-order-dev-database-1", "agachichi-atelier-qa-20261102-wordpress-1",
         "agachichi-atelier-qa-20261102-database-1")
PROD_LABELS = ("com.aicontrolcenter.prod-commerce-api", "com.aicontrolcenter.prod-homepage")
PROD_NAMES = ("shopping-db", "shopping-wordpress")

class ResourceError(RuntimeError):
    pass

def trusted_home():
    return Path(pwd.getpwuid(os.getuid()).pw_dir)

def validate_state(state):
    if (not isinstance(state, dict) or state.get("schema_version") != 1
            or state.get("module") != "shopping" or state.get("profile") != PROFILE
            or type(state.get("uid")) is not int
            or set(x.get("name") for x in state.get("containers", [])) != set(NAMES)
            or len(state.get("containers", [])) != len(NAMES)
            or set(x.get("label") for x in state.get("services", [])) != set(LABELS)
            or len(state.get("services", [])) != len(LABELS)):
        raise ResourceError("invalid_resource_inventory")
    for item in state["containers"]:
        if not re.fullmatch("[0-9a-f]{64}", item.get("id", "")) or not isinstance(item.get("mounts"), list):
            raise ResourceError("invalid_resource_identity")
    for item in state["services"]:
        if not re.fullmatch("[0-9a-f]{64}", item.get("plist_sha256", "")):
            raise ResourceError("invalid_service_identity")
    return state

def plan(action, state, home):
    validate_state(state)
    if action not in {"attach", "detach"}:
        raise ResourceError("invalid_action")
    home = Path(home)
    if not home.is_absolute():
        raise ResourceError("invalid_home")
    docker = ["/opt/homebrew/bin/docker", "--host", "unix://" + str(home / ".colima" / PROFILE / "docker.sock")]
    domain = "gui/" + str(state["uid"])
    if action == "attach":
        commands = [["/opt/homebrew/bin/colima", "start", "--profile", PROFILE]]
        commands += [docker + ["start", name] for name in PROD_NAMES]
        for label in PROD_LABELS:
            commands += [["launchctl", "enable", domain + "/" + label],
                         ["launchctl", "bootstrap", domain, str(home / "Library/LaunchAgents" / (label + ".plist"))]]
    else:
        commands = []
        for label in LABELS:
            commands += [["launchctl", "disable", domain + "/" + label],
                         ["launchctl", "bootout", domain + "/" + label]]
        commands += [docker + ["stop", "--time", "30", *[x for x in NAMES if "wordpress" in x]],
                     docker + ["stop", "--time", "30", *[x for x in NAMES if "wordpress" not in x]],
                     ["/opt/homebrew/bin/colima", "stop", "--profile", PROFILE]]
    return {"module": "shopping", "action": action, "apply": False, "data_deletion": False,
            "commands": commands, "preconditions": ["same container IDs and mount identities",
                "same launchd plist hashes", "Mac user identity", "VM stopped only if no other workloads"],
            "attach_scope": "production only; DEV and QA remain paused"}

class ShoppingRuntimeController:
    def __init__(self, *, home=None, run=None):
        self.home = Path(home) if home else trusted_home()
        self.state_path = self.home / "AIControlCenterRuntime/modules/shopping/runtime.json"
        self.run = run or subprocess.run

    def state(self):
        if self.state_path.is_symlink() or not self.state_path.is_file():
            raise ResourceError("inventory_missing")
        return validate_state(json.loads(self.state_path.read_text()))

    def _call(self, args, *, allow_missing=False, timeout=120):
        result = self.run(args, capture_output=True, text=True, timeout=timeout)
        if result.returncode and not allow_missing:
            raise ResourceError("resource_command_failed")
        return result

    def _vm(self):
        result = self._call(["/opt/homebrew/bin/colima", "list", "--json"])
        for line in result.stdout.splitlines():
            item = json.loads(line)
            if item.get("name") == PROFILE:
                return item.get("status")
        raise ResourceError("profile_missing")

    def _save(self, state):
        temp = self.state_path.with_suffix(".tmp")
        temp.write_text(json.dumps(state, indent=2) + "\n")
        temp.chmod(0o600)
        temp.replace(self.state_path)

    def _service_identities(self, state):
        for item in state["services"]:
            path = self.home / "Library/LaunchAgents" / (item["label"] + ".plist")
            if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != item["plist_sha256"]:
                raise ResourceError("service_generation_changed")
    def _identities(self, state, docker):
        self._service_identities(state)
        result = self._call(docker + ["inspect", *NAMES])
        actual = {x["Name"].lstrip("/"): x for x in json.loads(result.stdout)}
        for item in state["containers"]:
            value = actual[item["name"]]
            mounts = [{"type": m["Type"], "name": m.get("Name"), "source": m["Source"],
                       "destination": m["Destination"]} for m in value["Mounts"]]
            if (value["Id"] != item["id"]
                    or sorted(mounts, key=lambda m: m["destination"]) != sorted(item["mounts"], key=lambda m: m["destination"])):
                raise ResourceError("container_generation_changed")

    def _healthy(self, docker, name):
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            value = json.loads(self._call(docker + ["inspect", name]).stdout)[0]
            status = value["State"]
            if status["Running"] and status.get("Health", {}).get("Status") == "healthy":
                return
            if not status["Running"] or status.get("Health", {}).get("Status") == "unhealthy":
                raise ResourceError("container_unhealthy")
            time.sleep(1)
        raise ResourceError("container_health_timeout")

    def _service_ready(self, label, domain):
        import plistlib
        import socket
        value = plistlib.loads((self.home / "Library/LaunchAgents" / (label + ".plist")).read_bytes())
        args = value.get("ProgramArguments", [])
        try:
            port = int(args[args.index("--port") + 1])
            if not 1024 <= port <= 65535:
                raise ValueError
        except (ValueError, IndexError):
            raise ResourceError("service_port_missing") from None
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            observation = self._call(["launchctl", "print", domain + "/" + label], allow_missing=True)
            if not observation.returncode and re.search(r"state = running", observation.stdout) and re.search(r"pid = [1-9][0-9]*", observation.stdout):
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=1):
                        return
                except OSError:
                    pass
            time.sleep(1)
        raise ResourceError("service_not_listening")

    def apply(self, action):
        if sys.platform != "darwin":
            raise ResourceError("mac_only")
        state = self.state()
        if state["uid"] != os.getuid():
            raise ResourceError("user_changed")
        if action not in {"attach", "detach"}:
            raise ResourceError("invalid_action")
        self._service_identities(state)
        docker = ["/opt/homebrew/bin/docker", "--host", "unix://" + str(self.home / ".colima" / PROFILE / "docker.sock")]
        domain = "gui/" + str(os.getuid())
        vm = self._vm()
        if vm not in {"Running", "Stopped"}:
            raise ResourceError("profile_not_ready")
        state["phase"] = "ATTACHING" if action == "attach" else "DRAINING"
        self._save(state)
        try:
            if vm == "Stopped" and action == "attach":
                self._call(["/opt/homebrew/bin/colima", "start", "--profile", PROFILE])
            if vm == "Running" or action == "attach":
                self._identities(state, docker)
            if action == "attach":
                for name in PROD_NAMES:
                    self._call(docker + ["start", name])
                    self._healthy(docker, name)
                for label in PROD_LABELS:
                    self._call(["launchctl", "enable", domain + "/" + label])
                    loaded = self._call(["launchctl", "print", domain + "/" + label], allow_missing=True)
                    if loaded.returncode:
                        self._call(["launchctl", "bootstrap", domain,
                            str(self.home / "Library/LaunchAgents" / (label + ".plist"))])
                    self._service_ready(label, domain)
                state["phase"] = "ATTACHED"
            else:
                for label in LABELS:
                    self._call(["launchctl", "disable", domain + "/" + label])
                    loaded = self._call(["launchctl", "print", domain + "/" + label], allow_missing=True)
                    if not loaded.returncode:
                        self._call(["launchctl", "bootout", domain + "/" + label])
                if vm == "Running":
                    for group in ([x for x in NAMES if "wordpress" in x], [x for x in NAMES if "wordpress" not in x]):
                        self._call(docker + ["stop", "--time", "30", *group])
                    running = self._call(docker + ["ps", "--format", "{{.Names}}"]).stdout.splitlines()
                    if any(name in NAMES for name in running):
                        raise ResourceError("shopping_still_running")
                    if not running:
                        self._call(["/opt/homebrew/bin/colima", "stop", "--profile", PROFILE])
                state["phase"] = "PAUSED"
            self._save(state)
            return {"phase": state["phase"], "data_deletion": False}
        except Exception:
            state["phase"] = "TRANSITION_INCOMPLETE"
            self._save(state)
            raise ResourceError("transition_incomplete_no_automatic_retry") from None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["status", "attach", "detach"])
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    controller = ShoppingRuntimeController()
    try:
        state = controller.state()
        if args.action == "status":
            result = {"module": "shopping", "phase": state.get("phase"),
                      "observed_vm_status": controller._vm(), "data_deletion": False}
        elif args.apply:
            result = controller.apply(args.action)
        else:
            result = plan(args.action, state, controller.home)
        print(json.dumps(result))
        return 0
    except Exception as error:
        print(json.dumps({"status": "BLOCKED", "error": str(error) if isinstance(error, ResourceError) else "resource_unavailable"}))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())

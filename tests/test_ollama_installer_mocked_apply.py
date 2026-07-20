import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "ops/macos/ollama/install-managed-ollama.sh"


def write_executable(path: Path, body: str) -> Path:
    path.write_text("#!/bin/bash\nset -u\n" + body + "\n")
    path.chmod(0o755)
    return path


def create_common_files(tmp_path: Path) -> dict[str, Path]:
    approval = tmp_path / "approval.json"
    plan = tmp_path / "plan.json"
    snapshot = tmp_path / "snapshot.json"

    approval.write_text(json.dumps({"valid": True}))
    plan.write_text(json.dumps({"valid": True}))
    snapshot.write_text(json.dumps({"valid": True}))

    return {
        "approval": approval,
        "plan": plan,
        "snapshot": snapshot,
    }


def create_mock_gate(tmp_path: Path) -> Path:
    module_root = tmp_path / "modules"
    package = module_root / "mock_gate"
    package.mkdir(parents=True)

    (package / "__init__.py").write_text("")
    (package / "__main__.py").write_text(
        "import json\n"
        "print(json.dumps({\n"
        '    "valid": True,\n'
        '    "gate_status": "AUTHORIZED",\n'
        '    "execution_enabled": False,\n'
        '    "errors": [],\n'
        "}))\n"
    )

    return module_root


def create_mock_backup_generator(tmp_path: Path) -> Path:
    generator = tmp_path / "mock-backup.py"

    generator.write_text(
        "import argparse\n"
        "import json\n"
        "from pathlib import Path\n"
        "\n"
        "parser = argparse.ArgumentParser()\n"
        'parser.add_argument("--output-root", type=Path, required=True)\n'
        'parser.add_argument("--write-backup", action="store_true")\n'
        "args = parser.parse_args()\n"
        "\n"
        'backup = args.output_root / "ollama-test-backup"\n'
        "backup.mkdir(parents=True, exist_ok=True)\n"
        '(backup / "launchd").mkdir(exist_ok=True)\n'
        '(backup / "environment").mkdir(exist_ok=True)\n'
        '(backup / "binary").mkdir(exist_ok=True)\n'
        "\n"
        '(backup / "launchd/com.aicontrolcenter.ollama.plist").write_text(\n'
        '    "previous-plist\\n"\n'
        ")\n"
        '(backup / "environment/ollama.env").write_text(\n'
        '    "PREVIOUS_ENV=true\\n"\n'
        ")\n"
        '(backup / "binary/ollama").write_text("previous-binary\\n")\n'
        "\n"
        'manifest = backup / "backup-manifest.json"\n'
        'manifest.write_text("{}\\n")\n'
        "\n"
        "print(json.dumps({\n"
        '    "backup_directory": str(backup),\n'
        '    "manifest_path": str(manifest),\n'
        '    "write_performed": True,\n'
        "}))\n"
    )

    return generator


def create_mock_commands(tmp_path: Path, health_success: bool) -> dict[str, Path]:
    command_dir = tmp_path / "commands"
    command_dir.mkdir()

    command_log = tmp_path / "command.log"

    brew = write_executable(
        command_dir / "brew",
        f'echo "brew $*" >> "{command_log}"\nexit 0',
    )

    install = write_executable(
        command_dir / "install",
        f'''
echo "install $*" >> "{command_log}"

if [ "$1" = "-d" ]; then
  mkdir -p "$2"
  exit 0
fi

if [ "$1" = "-m" ]; then
  MODE="$2"
  SOURCE="$3"
  TARGET="$4"
  mkdir -p "$(dirname "$TARGET")"
  cp "$SOURCE" "$TARGET"
  chmod "$MODE" "$TARGET" 2>/dev/null || true
  exit 0
fi

exit 1
''',
    )

    launchctl = write_executable(
        command_dir / "launchctl",
        f'echo "launchctl $*" >> "{command_log}"\nexit 0',
    )

    curl_exit = 0 if health_success else 1
    privilege = write_executable(
        command_dir / "privilege",
        f'echo "privilege $*" >> "{command_log}"\nexec "$@"',
    )

    curl = write_executable(
        command_dir / "curl",
        f'echo "curl $*" >> "{command_log}"\nexit {curl_exit}',
    )

    return {
        "brew": brew,
        "install": install,
        "launchctl": launchctl,
        "curl": curl,
        "privilege": privilege,
        "log": command_log,
    }


def build_environment(
    tmp_path: Path,
    commands: dict[str, Path],
    module_root: Path,
    backup_generator: Path,
) -> tuple[dict[str, str], dict[str, Path]]:
    targets = {
        "plist": tmp_path / "targets/launchd/com.aicontrolcenter.ollama.plist",
        "env": tmp_path / "targets/environment/ollama.env",
        "models": tmp_path / "targets/models",
        "logs": tmp_path / "targets/logs",
        "backup": tmp_path / "backups",
        "binary": tmp_path / "targets/bin/ollama",
    }

    env = os.environ.copy()
    env.update(
        {
            "PYTHONPATH": (
                str(module_root)
                + os.pathsep
                + str(ROOT)
                + os.pathsep
                + env.get("PYTHONPATH", "")
            ),
            "EXECUTION_GATE_MODULE": "mock_gate",
            "BACKUP_GENERATOR": str(backup_generator),
            "BREW_COMMAND": str(commands["brew"]),
            "INSTALL_COMMAND": str(commands["install"]),
            "LAUNCHCTL_COMMAND": str(commands["launchctl"]),
            "CURL_COMMAND": str(commands["curl"]),
            "PRIVILEGE_COMMAND": str(commands["privilege"]),
            "OLLAMA_BINARY_TARGET": str(targets["binary"]),
            "PLIST_TARGET": str(targets["plist"]),
            "ENV_TARGET": str(targets["env"]),
            "MODELS_TARGET": str(targets["models"]),
            "LOG_TARGET": str(targets["logs"]),
            "SERVICE": "system/com.aicontrolcenter.ollama.test",
            "HEALTH_URL": "http://127.0.0.1:11434/api/tags",
        }
    )

    return env, targets


def run_installer(
    files: dict[str, Path],
    env: dict[str, str],
    targets: dict[str, Path],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            str(INSTALLER),
            "--approval",
            str(files["approval"]),
            "--plan",
            str(files["plan"]),
            "--snapshot",
            str(files["snapshot"]),
            "--execution-token",
            "a" * 64,
            "--backup-root",
            str(targets["backup"]),
            "--apply",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_mocked_apply_success(tmp_path: Path):
    files = create_common_files(tmp_path)
    module_root = create_mock_gate(tmp_path)
    backup_generator = create_mock_backup_generator(tmp_path)
    commands = create_mock_commands(tmp_path, health_success=True)
    env, targets = build_environment(
        tmp_path,
        commands,
        module_root,
        backup_generator,
    )

    result = run_installer(files, env, targets)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "applied successfully" in result.stdout
    assert targets["plist"].is_file()
    assert targets["env"].is_file()
    assert targets["models"].is_dir()
    assert targets["logs"].is_dir()

    command_log = commands["log"].read_text()
    assert "brew install ollama" in command_log
    assert "launchctl bootstrap system" in command_log
    assert "launchctl kickstart -k" in command_log
    assert "curl -fsS" in command_log


def test_mocked_health_failure_triggers_rollback(tmp_path: Path):
    files = create_common_files(tmp_path)
    module_root = create_mock_gate(tmp_path)
    backup_generator = create_mock_backup_generator(tmp_path)
    commands = create_mock_commands(tmp_path, health_success=False)
    env, targets = build_environment(
        tmp_path,
        commands,
        module_root,
        backup_generator,
    )

    result = run_installer(files, env, targets)

    assert result.returncode == 7
    assert "automatic rollback" in result.stdout.lower()
    assert "Automatic rollback completed" in result.stdout

    assert targets["plist"].read_text() == "previous-plist\n"
    assert targets["env"].read_text() == "PREVIOUS_ENV=true\n"
    assert targets["binary"].read_text() == "previous-binary\n"

    command_log = commands["log"].read_text()
    assert "launchctl bootout" in command_log
    assert command_log.count("curl -fsS") == 10

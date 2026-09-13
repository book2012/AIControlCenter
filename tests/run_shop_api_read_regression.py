"""Fixture-only pytest tooling: no ambient config, network, or external processes."""
import os
from pathlib import Path
import runpy
import socket
import subprocess
import sys
import tempfile


repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))
os.chdir(repo)
for key in tuple(os.environ):
    if key not in {"PATH", "TMPDIR", "LANG", "LC_ALL", "SYSTEMROOT"}:
        del os.environ[key]
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
sys.dont_write_bytecode = True

from core.config.loader import ConfigLoader

ConfigLoader.load = lambda self: {"env_path": str(self.env_path), "exists": False, "loaded": False}


def denied(*args, **kwargs):
    raise AssertionError("SHOP_API_READ fixture-only boundary: external operation blocked")


socket.socket.connect = denied
socket.socket.connect_ex = denied
socket.create_connection = denied
# Allow only the existing local port-isolation regression's guarded Python child.
port_test = runpy.run_path(str(repo / "tests/test_shopping_read_only_ports.py"))
port_program = "\n".join([
    "import importlib", "import pathlib", "import socket", "import sqlite3",
    "import subprocess", "import urllib.request",
    "def blocked(*args, **kwargs):",
    '    raise RuntimeError("external side effect blocked")',
    "socket.create_connection = blocked", "sqlite3.connect = blocked",
    "subprocess.Popen = blocked", "urllib.request.urlopen = blocked",
    "pathlib.Path.write_text = blocked", "pathlib.Path.write_bytes = blocked",
    "modules = " + repr(port_test["MODULES"]),
    "for name in modules:", "    importlib.import_module(name)",
])
original_popen = subprocess.Popen


def fixture_popen(args, **kwargs):
    if args == [sys.executable, "-B", "-c", port_program] and kwargs.get("cwd") == repo:
        return original_popen(args, **kwargs)
    return denied()


subprocess.Popen = fixture_popen

import pytest

with tempfile.TemporaryDirectory(prefix="shop-api-read-") as temp:
    sys.exit(pytest.main(["-p", "no:cacheprovider", "--basetemp", temp, *sys.argv[1:]]))

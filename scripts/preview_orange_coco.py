"""Run only the repository-owned demo preview on loopback; no production app.

Usage: .venv/bin/python -B scripts/preview_orange_coco.py [--port 18080]
Python changes reload automatically; templates/assets are read per request.
"""
import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True


def isolate_preview():
    # Inherited secrets/config and repository .env files are not preview inputs.
    for key in tuple(os.environ):
        if key not in {"PATH", "TMPDIR", "LANG", "LC_ALL", "SYSTEMROOT"}:
            del os.environ[key]
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    from core.config.loader import ConfigLoader
    ConfigLoader.load = lambda self: {"exists": False, "loaded": False}


# uvicorn's local reload child re-executes this module before importing its app.
isolate_preview()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=18080)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("Use an unprivileged local preview port")
    import uvicorn
    uvicorn.run("core.homepage.preview:create_app", factory=True, host="127.0.0.1",
                port=args.port, reload=True, reload_dirs=[str(ROOT / "core")],
                access_log=False, log_level="warning")

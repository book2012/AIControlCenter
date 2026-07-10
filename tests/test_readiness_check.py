from pathlib import Path


def test_readiness_script_exists():
    assert Path("scripts/readiness_check.py").exists()

from pathlib import Path


def test_launchd_templates_exist():
    root = Path("deploy/launchd")

    templates = list(root.glob("*.plist.template"))

    assert len(templates) == 3


def test_launchd_templates_use_project_placeholder():
    for path in Path("deploy/launchd").glob("*.plist.template"):
        content = path.read_text(encoding="utf-8")

        assert "__PROJECT_ROOT__" in content
        assert "RunAtLoad" in content
        assert "KeepAlive" in content

import json
from pathlib import Path

from core.deployment.plan import build_deployment_plan


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/services/mac-standalone-production.json"


def test_full_deployment_plan_is_read_only():
    manifest = json.loads(MANIFEST.read_text())
    result = build_deployment_plan(MANIFEST)

    assert result["valid"] is True
    assert result["read_only"] is True
    assert result["profile"] == "mac-standalone-production"
    assert result["service_count"] == len(manifest["services"])
    assert result["errors"] == []
    assert sum(
        plan["service_id"] == "shopping-runtime"
        for plan in result["plans"]
    ) == 1


def test_ollama_plan_requires_install_and_start():
    result = build_deployment_plan(MANIFEST, service_id="ollama")

    assert result["valid"] is True
    assert result["service_count"] == 1

    plan = result["plans"][0]
    actions = {
        action["action"]: action
        for action in plan["actions"]
    }

    assert plan["service_id"] == "ollama"
    assert plan["production_status"] == "NOT_RUNNING"
    assert plan["ubuntu_dependency"] is False
    assert actions["validate"]["write"] is False
    assert actions["inspect"]["write"] is False
    assert actions["install"]["write"] is True
    assert actions["install"]["required"] is True
    assert actions["start"]["required"] is True
    assert actions["health"]["required"] is True
    assert actions["rollback"]["required"] is True


def test_production_service_does_not_require_install():
    result = build_deployment_plan(
        MANIFEST,
        service_id="aicontrolcenter-api",
    )

    plan = result["plans"][0]
    actions = {
        action["action"]: action
        for action in plan["actions"]
    }

    assert actions["install"]["required"] is False
    assert actions["start"]["required"] is False
    assert actions["health"]["required"] is True


def test_unknown_service_returns_json_error():
    result = build_deployment_plan(
        MANIFEST,
        service_id="missing-service",
    )

    assert result["valid"] is False
    assert result["service_count"] == 0
    assert result["errors"] == [
        "service not found: missing-service"
    ]

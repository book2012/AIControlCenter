import json
from datetime import datetime, timedelta
from pathlib import Path

from core.runtime.service_health import ServiceHealth
from core.runtime.service_topology import ServiceTopology


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/services/mac-standalone-production.json"
SCHEMA = ROOT / "config/schemas/mac-service-manifest.schema.json"


class FakeHeartbeat:
    def __init__(self, created: datetime | None = None):
        self.created = created or datetime.utcnow()

    def latest(self):
        return {"status": "ALIVE", "created": self.created.isoformat()}


def health(
    *, heartbeat=None, launchd_state="RUNNING", topology=None,
    scheduler_log_inspector=None,
):
    return ServiceHealth(
        heartbeat=heartbeat or FakeHeartbeat(),
        topology=topology,
        launchd_inspector=lambda _label: launchd_state,
        scheduler_log_inspector=scheduler_log_inspector or (
            lambda: {
                "parent": {"valid": True},
                "logs": [{"valid": True}, {"valid": True}],
                "scheduler_log_contract_ready": True,
            }
        ),
    )


def test_canonical_api_launchd_label_can_report_running():
    result = health().status()

    assert result["services"]["api"] == {
        "service_id": "aicontrolcenter-api",
        "required": True,
        "lifecycle": "launchd",
        "status": "RUNNING",
        "launchd_label": "com.aicontrolcenter.api",
    }


def test_required_and_optional_not_deployed_semantics_are_truthful():
    result = health().status()

    assert result["services"]["telegram"]["status"] == "NOT_DEPLOYED"
    assert result["services"]["telegram"]["required"] is False
    assert result["services"]["scheduler"]["status"] == "RUNNING"
    assert result["services"]["scheduler"]["required"] is True
    assert result["healthy"] is True


def test_optional_not_deployed_does_not_fail_aggregate(tmp_path):
    manifest = json.loads(MANIFEST.read_text())
    for item in manifest["services"]:
        if item.get("logical_id") == "scheduler":
            item["required"] = False
            item["production_status"] = "NOT_DEPLOYED"
            item["runtime"] = "UNASSIGNED"
            item["supervisor"] = "UNASSIGNED"
            item["lifecycle"] = "not_deployed"
            item.pop("launchd_label", None)
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))

    result = health(topology=ServiceTopology(path, SCHEMA)).status()

    assert result["services"]["api"]["status"] == "RUNNING"
    assert result["services"]["api"]["required"] is True
    assert result["services"]["scheduler"]["status"] == "NOT_DEPLOYED"
    assert result["services"]["scheduler"]["required"] is False
    assert result["services"]["scheduler"]["lifecycle"] == "not_deployed"
    assert result["healthy"] is True


def test_stale_required_scheduler_heartbeat_fails_aggregate(tmp_path):
    manifest = json.loads(MANIFEST.read_text())
    for item in manifest["services"]:
        if item.get("logical_id") == "scheduler":
            item["production_status"] = "PRODUCTION"
            item["lifecycle"] = "launchd"
            item["launchd_label"] = "com.example.scheduler"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    stale = FakeHeartbeat(datetime.utcnow() - timedelta(minutes=10))

    result = health(
        heartbeat=stale,
        topology=ServiceTopology(path, SCHEMA),
    ).status()

    assert result["scheduler_heartbeat"]["status"] == "STALE"
    assert result["healthy"] is False


def test_malformed_topology_fails_closed(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text("{}")

    result = health(topology=ServiceTopology(path, SCHEMA)).status()

    assert result["healthy"] is False
    assert result["services"] == {}
    assert result["topology"]["status"] == "INVALID"


def test_service_health_format_reports_warning_for_required_not_deployed():
    text = health(launchd_state="STOPPED").format_text()

    assert "Service Health" in text
    assert "Overall: WARNING" in text


def test_scheduler_health_requires_launchd_running_and_fresh_heartbeat():
    fresh = FakeHeartbeat(datetime.utcnow() - timedelta(seconds=30))
    stale = FakeHeartbeat(datetime.utcnow() - timedelta(seconds=91))

    assert health(heartbeat=fresh, launchd_state="RUNNING").status()["healthy"] is True
    assert health(heartbeat=stale, launchd_state="RUNNING").status()["healthy"] is False
    assert health(heartbeat=fresh, launchd_state="STOPPED").status()["healthy"] is False


def test_scheduler_lifecycle_readiness_fails_closed_when_logs_are_missing():
    readiness = {
        "scheduler_log_contract_ready": False,
        "logs": [{"path": "/missing", "exists": False, "valid": False}],
    }
    result = health(scheduler_log_inspector=lambda: readiness).status()
    assert result["services"]["scheduler"]["status"] == "RUNNING"
    assert result["scheduler_log_readiness"] == readiness
    assert result["healthy"] is False


def test_scheduler_lifecycle_readiness_fails_closed_when_logs_are_invalid():
    readiness = {
        "scheduler_log_contract_ready": False,
        "logs": [{"path": "/invalid", "exists": True, "valid": False}],
    }
    assert health(scheduler_log_inspector=lambda: readiness).status()["healthy"] is False


def test_scheduler_lifecycle_readiness_fails_closed_on_inspector_error():
    def fail():
        raise PermissionError(13, "not disclosed")

    result = health(scheduler_log_inspector=fail).status()
    assert result["healthy"] is False
    assert result["scheduler_log_readiness"] == {
        "scheduler_log_contract_ready": False,
        "inspection_error": {"error_type": "PermissionError"},
    }
    assert "not disclosed" not in repr(result)


def test_core_has_no_direct_ops_imports():
    direct_imports = []
    for source_path in (ROOT / "core").rglob("*.py"):
        for line_number, line in enumerate(source_path.read_text().splitlines(), 1):
            if line.startswith(("from ops.", "import ops.")):
                direct_imports.append(f"{source_path.relative_to(ROOT)}:{line_number}")

    assert direct_imports == []


def test_legacy_linux_service_projection_is_absent():
    source = (ROOT / "core/runtime/service_health.py").read_text()

    assert "systemctl" not in source
    assert '"aicontrolcenter-api"' not in source
    assert '"aicontrolcenter-telegram"' not in source
    assert '"aicontrolcenter-scheduler"' not in source
    assert "from ops." not in source
    assert "import ops." not in source

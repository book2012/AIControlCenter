import json
from pathlib import Path

from core.runtime.service_topology import ServiceTopology


ROOT = Path(__file__).resolve().parents[1]


def test_application_scheduler_uses_mac_launchd_without_ubuntu_dependency():
    services = ServiceTopology().runtime_services()
    scheduler = next(item for item in services if item.service_id == "application-scheduler")

    assert scheduler.logical_id == "scheduler"
    assert scheduler.lifecycle == "launchd"
    assert scheduler.launchd_label == "com.aicontrolcenter.application-scheduler"
    assert scheduler.deployment_status == "PRODUCTION"

    manifest = json.loads(
        (ROOT / "config/services/mac-standalone-production.json").read_text()
    )
    record = next(
        item for item in manifest["services"]
        if item["service_id"] == "application-scheduler"
    )
    assert record["ubuntu_dependency"] is False


def test_governance_scheduler_remains_a_separate_domain():
    assert (ROOT / "core/scheduler/daemon.py").is_file()
    assert (ROOT / "core/governance/operations/application/scheduler.py").is_file()
    manifest = json.loads(
        (ROOT / "config/services/mac-standalone-production.json").read_text()
    )
    scheduler = next(
        item for item in manifest["services"]
        if item["service_id"] == "application-scheduler"
    )
    governance = json.loads(
        (ROOT / "config/governance_scheduler_smappservice.json").read_text()
    )

    assert scheduler["launchd_label"] != governance["bundle"]["identifier"]

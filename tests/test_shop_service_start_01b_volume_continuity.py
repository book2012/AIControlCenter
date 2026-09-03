from __future__ import annotations

import ast
import json
from dataclasses import replace
from pathlib import Path

from core.infrastructure.profile_recovery import (
    ProfileHealth, ProfileHealthFacts, RecoveryEvidence, SHOPPING_PROFILE,
    decide_profile_recovery,
)
from core.shopping.observability.storage_continuity import (
    CANONICAL_VOLUMES, ContinuityCompleteness, ContinuityReason,
    DATABASE_DESTINATION, DATABASE_VOLUME, EXPECTED_DESTINATIONS,
    StorageContinuityObservation, VolumeContinuitySnapshot,
    WORDPRESS_DESTINATION, WORDPRESS_VOLUME, compare_volume_identity_continuity,
)
from ops.macos.shopping.storage_continuity_observer import (
    COMPOSE_PROJECT, CONTAINERS, DOCKER_CONTEXT, CommandResult,
    observe_storage_continuity,
)


ROOT = Path(__file__).resolve().parents[1]


def snapshot(name: str, *, created_at: str = "2026-01-02T03:04:05Z") -> VolumeContinuitySnapshot:
    service, container = CONTAINERS[name]
    return VolumeContinuitySnapshot(
        volume_name=name, present=True, driver="local", scope="local",
        created_at=created_at, expected_attachment=True,
        expected_destination=EXPECTED_DESTINATIONS[name],
        observed_destination=EXPECTED_DESTINATIONS[name], attachment_type="volume",
        service=service, container=container,
        completeness=ContinuityCompleteness.COMPLETE, reason=ContinuityReason.NONE,
    )


def observation(*items: VolumeContinuitySnapshot) -> StorageContinuityObservation:
    return StorageContinuityObservation(tuple(items or (snapshot(DATABASE_VOLUME), snapshot(WORDPRESS_VOLUME))))


class FakeRunner:
    def __init__(self, *, mount_changes: dict[str, object] | None = None, malformed_volume: str | None = None, absent_volume: str | None = None):
        self.calls: list[tuple[str, ...]] = []
        self.mount_changes = mount_changes or {}
        self.malformed_volume = malformed_volume
        self.absent_volume = absent_volume

    def __call__(self, argv):
        call = tuple(argv)
        self.calls.append(call)
        identity = call[-1]
        if "volume" in call:
            if identity == self.absent_volume:
                return CommandResult(1)
            if identity == self.malformed_volume:
                return CommandResult(0, "not-json")
            return CommandResult(0, json.dumps({
                "Name": identity, "Driver": "local", "Scope": "local",
                "CreatedAt": "2026-01-02T03:04:05Z", "Mountpoint": "/must/not/project",
            }).replace(', "Mountpoint": "/must/not/project"', ""))
        name = next(name for name, (_, container) in CONTAINERS.items() if container == identity)
        mount = {"Type": "volume", "Name": name,
                 "Destination": EXPECTED_DESTINATIONS[name], "Source": "/must/not/project"}
        changed = self.mount_changes.get(name)
        mounts = changed if isinstance(changed, list) else [dict(mount, **(changed or {}))]
        service, _ = CONTAINERS[name]
        return CommandResult(0, json.dumps({
            "Mounts": mounts, "Project": COMPOSE_PROJECT, "Service": service,
        }))


def test_canonical_identities_and_destinations_are_exact() -> None:
    assert CANONICAL_VOLUMES == (DATABASE_VOLUME, WORDPRESS_VOLUME)
    assert CANONICAL_VOLUMES == ("ai-shopping-database", "ai-shopping-wordpress")
    assert DATABASE_DESTINATION == "/var/lib/mysql"
    assert WORDPRESS_DESTINATION == "/var/www/html"
    assert DOCKER_CONTEXT == "colima-aicontrolcenter-commerce"
    assert COMPOSE_PROJECT == "ai-shopping"


def test_same_stable_identity_and_exact_attachment_proves_only_identity_continuity() -> None:
    result = compare_volume_identity_continuity(observation(), observation())
    assert result.volume_identity_continuity_proven is True
    projection = result.to_json_safe()
    assert projection["content_preservation_proven"] is False
    assert projection["backup_restore_proven"] is False
    assert projection["recovery_authorized"] is False
    assert projection["mutation_authorized"] is False
    assert projection["mutation_selected"] is False


def test_single_snapshot_never_projects_continuity_or_preservation() -> None:
    projection = observation().to_json_safe()
    assert "volume_identity_continuity_proven" not in projection
    assert projection["content_preservation_proven"] is False
    assert projection["backup_restore_proven"] is False
    assert projection["mutation_authorized"] is False


def test_same_name_with_changed_creation_identity_fails() -> None:
    after = observation(snapshot(DATABASE_VOLUME, created_at="changed"), snapshot(WORDPRESS_VOLUME))
    result = compare_volume_identity_continuity(observation(), after)
    assert result.volume_identity_continuity_proven is False
    assert ContinuityReason.IDENTITY_METADATA_CHANGED in result.reasons


def test_absent_wrong_destination_bind_and_malformed_fail_closed() -> None:
    base = snapshot(DATABASE_VOLUME)
    cases = (
        replace(base, present=False, reason=ContinuityReason.VOLUME_ABSENT),
        replace(base, observed_destination="/wrong"),
        replace(base, attachment_type="bind"),
        replace(base, completeness=ContinuityCompleteness.MALFORMED,
                reason=ContinuityReason.MALFORMED_EVIDENCE),
    )
    assert all(not compare_volume_identity_continuity(
        observation(case, snapshot(WORDPRESS_VOLUME)), observation()
    ).volume_identity_continuity_proven for case in cases)


def test_unexpected_or_duplicate_volume_fails_closed() -> None:
    unexpected = replace(snapshot(DATABASE_VOLUME), volume_name="other")
    duplicate = observation(snapshot(DATABASE_VOLUME), snapshot(DATABASE_VOLUME))
    assert not compare_volume_identity_continuity(observation(unexpected, snapshot(WORDPRESS_VOLUME)), observation()).volume_identity_continuity_proven
    assert not compare_volume_identity_continuity(duplicate, observation()).volume_identity_continuity_proven


def test_adapter_collects_fixed_read_only_projection_without_mountpoint_or_environment() -> None:
    runner = FakeRunner()
    projection = observe_storage_continuity(runner).to_json_safe()
    encoded = json.dumps(projection, sort_keys=True)
    assert "/must/not/project" not in encoded
    assert "Mountpoint" not in encoded and "Source" not in encoded
    assert "environment" not in encoded.lower()
    assert all(call[:3] == ("docker", "--context", DOCKER_CONTEXT) for call in runner.calls)
    assert {call[-1] for call in runner.calls} == set(CANONICAL_VOLUMES) | {"shopping-db", "shopping-wordpress"}
    assert all(".Mounts" in " ".join(call) or "CreatedAt" in " ".join(call) for call in runner.calls)
    assert all(".Config.Env" not in " ".join(call) for call in runner.calls)


def test_adapter_wrong_destination_bind_duplicate_absent_and_malformed_fail_closed() -> None:
    wrong = observe_storage_continuity(FakeRunner(mount_changes={DATABASE_VOLUME: {"Destination": "/wrong"}}))
    bind = observe_storage_continuity(FakeRunner(mount_changes={DATABASE_VOLUME: {"Type": "bind"}}))
    duplicate_mount = {"Type": "volume", "Name": DATABASE_VOLUME, "Destination": DATABASE_DESTINATION}
    duplicate = observe_storage_continuity(FakeRunner(mount_changes={DATABASE_VOLUME: [duplicate_mount, duplicate_mount]}))
    absent = observe_storage_continuity(FakeRunner(absent_volume=DATABASE_VOLUME))
    malformed = observe_storage_continuity(FakeRunner(malformed_volume=DATABASE_VOLUME))
    for value in (wrong, bind, duplicate, absent, malformed):
        assert not compare_volume_identity_continuity(value, observation()).volume_identity_continuity_proven


def test_no_destructive_authority_or_outer_mutation_surface_is_introduced() -> None:
    facts = ProfileHealthFacts(SHOPPING_PROFILE, True, "diagnostic", False, ProfileHealth.BROKEN)
    decision = decide_profile_recovery(facts, RecoveryEvidence())
    assert decision.candidate is None
    assert decision.destructive_recovery_available is False
    assert decision.to_json_safe()["mutation_selected"] is False
    path = ROOT / "ops/macos/shopping/storage_continuity_observer.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    literals = {node.value.lower() for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)}
    forbidden = {"start", "stop", "restart", "pull", "build", "create", "remove", "prune", "delete", "exec", "up", "down"}
    command_literals = {value for value in literals if value in forbidden}
    assert not command_literals
    assert "shell" not in {keyword.arg for node in ast.walk(tree) if isinstance(node, ast.Call) for keyword in node.keywords}

"""Fixed-identity, read-only macOS adapter for Shopping volume evidence."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Callable, Sequence

from core.shopping.observability.storage_continuity import (
    CANONICAL_VOLUMES,
    ContinuityCompleteness,
    ContinuityReason,
    EXPECTED_DESTINATIONS,
    StorageContinuityObservation,
    VolumeContinuitySnapshot,
)


DOCKER_CONTEXT = "colima-aicontrolcenter-commerce"
COMPOSE_PROJECT = "ai-shopping"
VOLUME_FORMAT = '{"Name":{{json .Name}},"Driver":{{json .Driver}},"Scope":{{json .Scope}},"CreatedAt":{{json .CreatedAt}}}'
CONTAINER_FORMAT = '{"Mounts":{{json .Mounts}},"Project":{{json (index .Config.Labels "com.docker.compose.project")}},"Service":{{json (index .Config.Labels "com.docker.compose.service")}}}'
CONTAINERS = {
    "ai-shopping-database": ("database", "shopping-db"),
    "ai-shopping-wordpress": ("wordpress", "shopping-wordpress"),
}


@dataclass(frozen=True, slots=True)
class CommandResult:
    returncode: int
    stdout: str = ""


Runner = Callable[[Sequence[str]], CommandResult]


def _run(argv: Sequence[str]) -> CommandResult:
    completed = subprocess.run(
        list(argv), text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        timeout=10, check=False,
    )
    return CommandResult(completed.returncode, completed.stdout)


def _failure(name: str, completeness: ContinuityCompleteness, reason: ContinuityReason) -> VolumeContinuitySnapshot:
    service, container = CONTAINERS[name]
    return VolumeContinuitySnapshot(
        name, False if reason is ContinuityReason.VOLUME_ABSENT else None,
        None, None, None, None, EXPECTED_DESTINATIONS[name], None, None,
        service, container, completeness, reason,
    )


def observe_storage_continuity(runner: Runner = _run) -> StorageContinuityObservation:
    rows: list[VolumeContinuitySnapshot] = []
    for name in CANONICAL_VOLUMES:
        service, container = CONTAINERS[name]
        volume_result = runner((
            "docker", "--context", DOCKER_CONTEXT, "volume", "inspect",
            "--format", VOLUME_FORMAT, name,
        ))
        if volume_result.returncode != 0:
            rows.append(_failure(name, ContinuityCompleteness.UNAVAILABLE, ContinuityReason.SOURCE_UNAVAILABLE))
            continue
        mounts_result = runner((
            "docker", "--context", DOCKER_CONTEXT, "container", "inspect",
            "--format", CONTAINER_FORMAT, container,
        ))
        if mounts_result.returncode != 0:
            rows.append(_failure(name, ContinuityCompleteness.UNAVAILABLE, ContinuityReason.SOURCE_UNAVAILABLE))
            continue
        try:
            metadata = json.loads(volume_result.stdout)
            attachment = json.loads(mounts_result.stdout)
            if not isinstance(metadata, dict) or set(metadata) != {"Name", "Driver", "Scope", "CreatedAt"}:
                raise ValueError
            if metadata["Name"] != name or any(not isinstance(metadata[key], str) or not metadata[key] for key in ("Driver", "Scope", "CreatedAt")):
                raise ValueError
            if not isinstance(attachment, dict) or set(attachment) != {"Mounts", "Project", "Service"}:
                raise ValueError
            if attachment["Project"] != COMPOSE_PROJECT or attachment["Service"] != service:
                raise ValueError
            mounts = attachment["Mounts"]
            if not isinstance(mounts, list) or any(
                not isinstance(item, dict)
                or any(not isinstance(item.get(key), str) or not item[key].strip()
                       for key in ("Type", "Destination"))
                or (item.get("Type") == "volume" and (
                    not isinstance(item.get("Name"), str) or not item["Name"].strip()))
                for item in mounts
            ):
                raise ValueError
            matches = [item for item in mounts if item["Type"] == "volume" and item["Name"] == name]
            if len(matches) != 1:
                reason = ContinuityReason.AMBIGUOUS_ATTACHMENT if len(matches) > 1 else ContinuityReason.ATTACHMENT_ABSENT
                rows.append(_failure(name, ContinuityCompleteness.INCOMPLETE, reason))
                continue
            mount = matches[0]
            attachment_type = mount["Type"]
            if mount["Destination"] != EXPECTED_DESTINATIONS[name]:
                reason = ContinuityReason.ATTACHMENT_DESTINATION_MISMATCH
            else:
                reason = ContinuityReason.NONE
            completeness = ContinuityCompleteness.COMPLETE if reason is ContinuityReason.NONE else ContinuityCompleteness.INCOMPLETE
            rows.append(VolumeContinuitySnapshot(
                name, True, metadata["Driver"], metadata["Scope"], metadata["CreatedAt"],
                True, EXPECTED_DESTINATIONS[name], mount["Destination"], attachment_type,
                service, container, completeness, reason,
            ))
        except (json.JSONDecodeError, TypeError, ValueError):
            rows.append(_failure(name, ContinuityCompleteness.MALFORMED, ContinuityReason.MALFORMED_EVIDENCE))
    return StorageContinuityObservation(tuple(rows))


__all__ = ("COMPOSE_PROJECT", "CONTAINERS", "DOCKER_CONTEXT", "CommandResult", "observe_storage_continuity")

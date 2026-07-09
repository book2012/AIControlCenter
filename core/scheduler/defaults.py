from core.scheduler.jobs import JobRegistry


def create_default_jobs() -> JobRegistry:
    registry = JobRegistry()

    registry.add(
        name="heartbeat",
        command="heartbeat",
        interval_seconds=30,
    )

    registry.add(
        name="doctor",
        command="/doctor",
        interval_seconds=3600,
    )

    registry.add(
        name="provider-check",
        command="/status",
        interval_seconds=3600,
    )

    registry.add(
        name="backup-verify",
        command="/backup verify",
        interval_seconds=86400,
    )

    return registry

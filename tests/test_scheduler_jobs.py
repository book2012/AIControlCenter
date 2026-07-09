from core.scheduler.jobs import JobRegistry


def test_job_registry_add():
    registry = JobRegistry()

    job = registry.add(
        name="doctor",
        command="/doctor",
        interval_seconds=3600,
    )

    assert job.name == "doctor"
    assert job.enabled is True


def test_job_registry_list():
    registry = JobRegistry()

    registry.add("heartbeat", "heartbeat", 30)

    jobs = registry.list()

    assert len(jobs) == 1
    assert jobs[0]["name"] == "heartbeat"


def test_job_registry_disable_enable():
    registry = JobRegistry()

    job = registry.add("doctor", "/doctor", 3600)

    registry.disable(job.id)
    assert registry.get(job.id).enabled is False

    registry.enable(job.id)
    assert registry.get(job.id).enabled is True

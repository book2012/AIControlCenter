from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


@dataclass
class ScheduledJob:
    id: str
    name: str
    command: str
    interval_seconds: int
    enabled: bool = True
    created: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "command": self.command,
            "interval_seconds": self.interval_seconds,
            "enabled": self.enabled,
            "created": self.created.isoformat(),
        }


class JobRegistry:
    def __init__(self):
        self.jobs = {}

    def add(self, name: str, command: str, interval_seconds: int):
        job = ScheduledJob(
            id=str(uuid4()),
            name=name,
            command=command,
            interval_seconds=interval_seconds,
        )
        self.jobs[job.id] = job
        return job

    def list(self):
        return [job.to_dict() for job in self.jobs.values()]

    def get(self, job_id: str):
        return self.jobs[job_id]

    def enable(self, job_id: str):
        self.jobs[job_id].enabled = True
        return self.jobs[job_id]

    def disable(self, job_id: str):
        self.jobs[job_id].enabled = False
        return self.jobs[job_id]

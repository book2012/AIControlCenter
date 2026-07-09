from datetime import datetime, timedelta

from core.scheduler.heartbeat import HeartbeatStore
from core.scheduler.jobs import JobRegistry
from core.scheduler.runner import JobRunner


class SchedulerLoop:
    def __init__(
        self,
        heartbeat: HeartbeatStore | None = None,
        jobs: JobRegistry | None = None,
        runner: JobRunner | None = None,
    ):
        self.heartbeat = heartbeat or HeartbeatStore()
        self.jobs = jobs or JobRegistry()
        self.runner = runner or JobRunner()
        self.last_run = {}

    def due_jobs(self):
        now = datetime.utcnow()
        due = []

        for job in self.jobs.jobs.values():
            if not job.enabled:
                continue

            last = self.last_run.get(job.id)

            if last is None:
                due.append(job)
                continue

            if now - last >= timedelta(seconds=job.interval_seconds):
                due.append(job)

        return due

    def tick(self):
        beat = self.heartbeat.beat()

        due = self.due_jobs()
        results = []

        for job in due:
            self.last_run[job.id] = datetime.utcnow()
            results.append(self.runner.run(job))

        return {
            "heartbeat": beat,
            "due_jobs": [
                job.to_dict()
                for job in due
            ],
            "results": results,
        }

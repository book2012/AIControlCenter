import time

from core.scheduler.defaults import create_default_jobs
from core.scheduler.heartbeat import HeartbeatStore
from core.scheduler.loop import SchedulerLoop
from core.scheduler.runner import JobRunner


class SchedulerService:
    def __init__(
        self,
        interval_seconds: int = 30,
        loop: SchedulerLoop | None = None,
    ):
        self.interval_seconds = interval_seconds
        self.loop = loop or SchedulerLoop(
            heartbeat=HeartbeatStore(),
            jobs=create_default_jobs(),
            runner=JobRunner(),
        )
        self.running = False

    def status(self):
        latest = self.loop.heartbeat.latest()

        return {
            "running": self.running,
            "interval_seconds": self.interval_seconds,
            "heartbeat": latest,
            "jobs": self.loop.jobs.list(),
        }

    def run_once(self):
        return self.loop.tick()

    def run_for_ticks(self, ticks: int = 1):
        self.running = True
        results = []

        try:
            for _ in range(ticks):
                results.append(self.run_once())
        finally:
            self.running = False

        return {
            "ticks": ticks,
            "results": results,
        }

    def run_forever(self):
        self.running = True

        try:
            while True:
                self.run_once()
                time.sleep(self.interval_seconds)
        finally:
            self.running = False

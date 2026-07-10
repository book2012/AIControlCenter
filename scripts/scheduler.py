import time

from core.runtime.lifecycle import GracefulLifecycle
from core.scheduler.service import SchedulerService


if __name__ == "__main__":
    lifecycle = GracefulLifecycle()
    lifecycle.install_signal_handlers()

    service = SchedulerService()

    while not lifecycle.should_stop():
        service.run_once()
        time.sleep(service.interval_seconds)

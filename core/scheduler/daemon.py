"""Dedicated, non-networked Application Scheduler process entrypoint."""

from core.scheduler.service import SchedulerService


def main() -> None:
    SchedulerService().run_forever()


if __name__ == "__main__":
    main()

from core.power.safe_shutdown import (
    SafeShutdownService,
    ShutdownContext,
)


WORKER = {
    "status": "READY",
}

STORAGE = {
    "overall_status": "HEALTHY",
}

BACKUP = {
    "overall_status": "HEALTHY",
}


def test_shutdown_requires_confirmation() -> None:
    result = SafeShutdownService().evaluate(
        worker=WORKER,
        storage=STORAGE,
        backup=BACKUP,
        context=ShutdownContext(
            confirmed=False,
        ),
    )

    assert result["approved"] is False
    assert result["decision"] == "BLOCKED"
    assert "confirmation_required" in result["blocking_reasons"]
    assert result["command_executed"] is False


def test_shutdown_is_blocked_by_running_tasks() -> None:
    result = SafeShutdownService().evaluate(
        worker=WORKER,
        storage=STORAGE,
        backup=BACKUP,
        context=ShutdownContext(
            confirmed=True,
            running_tasks=1,
        ),
    )

    assert result["approved"] is False
    assert "running_tasks" in result["blocking_reasons"]


def test_shutdown_is_blocked_by_storage_operation() -> None:
    result = SafeShutdownService().evaluate(
        worker=WORKER,
        storage=STORAGE,
        backup=BACKUP,
        context=ShutdownContext(
            confirmed=True,
            active_storage_operations=1,
        ),
    )

    assert result["approved"] is False
    assert (
        "active_storage_operations"
        in result["blocking_reasons"]
    )


def test_shutdown_is_blocked_by_backup_operation() -> None:
    result = SafeShutdownService().evaluate(
        worker=WORKER,
        storage=STORAGE,
        backup=BACKUP,
        context=ShutdownContext(
            confirmed=True,
            active_backup_operations=1,
        ),
    )

    assert result["approved"] is False
    assert (
        "active_backup_operations"
        in result["blocking_reasons"]
    )


def test_shutdown_is_blocked_when_worker_is_offline() -> None:
    result = SafeShutdownService().evaluate(
        worker={"status": "OFFLINE"},
        storage=STORAGE,
        backup=BACKUP,
        context=ShutdownContext(
            confirmed=True,
        ),
    )

    assert result["approved"] is False
    assert "worker_not_available" in result["blocking_reasons"]


def test_shutdown_is_approved_when_all_checks_pass() -> None:
    result = SafeShutdownService().evaluate(
        worker=WORKER,
        storage=STORAGE,
        backup=BACKUP,
        context=ShutdownContext(
            confirmed=True,
        ),
    )

    assert result["approved"] is True
    assert result["decision"] == "APPROVED"
    assert result["blocking_reasons"] == []
    assert result["command_executed"] is False

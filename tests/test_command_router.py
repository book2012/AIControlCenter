from core.commands.router import CommandRouter


def test_command_router_help():
    router = CommandRouter()

    result = router.route("/help")

    assert "/status" in result
    assert "/backup" in result


def test_command_router_tasks_empty():
    router = CommandRouter()

    result = router.route("/tasks")

    assert "Running: none" in result


def test_command_router_storage():
    router = CommandRouter()

    result = router.route("/storage")

    assert "Storage" in result
    assert "Root:" in result


def test_command_router_backup():
    router = CommandRouter()

    result = router.route("/backup")

    assert "Backup" in result
    assert "Read-only" in result

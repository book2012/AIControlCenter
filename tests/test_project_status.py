from core.project.status import ProjectStatusService


def test_project_sprint_status():
    service = ProjectStatusService()

    data = service.sprint_status()

    assert data["remaining_count"] == 5


def test_project_agent_status():
    service = ProjectStatusService()

    data = service.agent_status()

    assert data["remaining_count"] == 9


def test_project_format():
    service = ProjectStatusService()

    text = service.format_project()

    assert "AIControlCenter Project" in text
    assert "Sprint Status" in text
    assert "Agent Status" in text

from core.agent.actions.status_action import StatusAction


class FakeDashboard:
    def status(self):
        return {
            "brain": {
                "state": "ONLINE",
            },
            "workers": {},
        }


class FakeProviders:
    def chat(self, prompt):
        return {
            "ok": True,
            "result": {
                "content": "AIControlCenter는 정상입니다."
            },
        }


def test_status_action_matches_korean():
    action = StatusAction(
        dashboard=FakeDashboard(),
        providers=FakeProviders(),
    )

    assert action.matches("AIControlCenter 상태 알려줘")


def test_status_action_run():
    action = StatusAction(
        dashboard=FakeDashboard(),
        providers=FakeProviders(),
    )

    result = action.run("상태 알려줘")

    assert result["action"] == "status"
    assert result["summary"]["ok"] is True

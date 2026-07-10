from core.runtime.env_validation import EnvironmentTemplateValidator


def test_environment_template_valid(tmp_path):
    path = tmp_path / ".env.example"

    lines = [
        "AI_PROVIDER=openai",
        "OPENAI_API_KEY=",
        "OPENAI_MODEL=gpt-5",
        "GOOGLE_API_KEY=",
        "GOOGLE_MODEL=gemini-test",
        "GITHUB_TOKEN=",
        "NOTION_API_KEY=",
        "TELEGRAM_BOT_TOKEN=",
        "TELEGRAM_CHAT_ID=",
        "LOG_LEVEL=INFO",
        "TIMEZONE=Asia/Seoul",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")

    result = EnvironmentTemplateValidator(str(path)).validate()

    assert result["valid"] is True
    assert result["exposed_secrets"] == []


def test_environment_template_detects_secret(tmp_path):
    path = tmp_path / ".env.example"

    lines = [
        "AI_PROVIDER=openai",
        "OPENAI_API_KEY=secret-value",
        "OPENAI_MODEL=gpt-5",
        "GOOGLE_API_KEY=",
        "GOOGLE_MODEL=gemini-test",
        "GITHUB_TOKEN=",
        "NOTION_API_KEY=",
        "TELEGRAM_BOT_TOKEN=",
        "TELEGRAM_CHAT_ID=",
        "LOG_LEVEL=INFO",
        "TIMEZONE=Asia/Seoul",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")

    result = EnvironmentTemplateValidator(str(path)).validate()

    assert result["valid"] is False
    assert "OPENAI_API_KEY" in result["exposed_secrets"]

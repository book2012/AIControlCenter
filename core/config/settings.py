import os
from dataclasses import dataclass

from core.config.loader import ConfigLoader


@dataclass
class BrainSettings:
    name: str
    role: str
    log_level: str
    timezone: str


@dataclass
class AISettings:
    provider: str


@dataclass
class OpenAISettings:
    api_key: str | None
    model: str
    embedding_model: str


@dataclass
class GoogleSettings:
    api_key: str | None
    model: str


@dataclass
class GitHubSettings:
    username: str | None
    token: str | None


@dataclass
class NotionSettings:
    api_key: str | None
    database: str | None


@dataclass
class WorkerSettings:
    ubuntu_host: str | None
    ubuntu_port: int
    ubuntu_user: str | None
    ubuntu_ssh_key: str | None


@dataclass
class StorageSettings:
    root: str
    backup_root: str
    ai_root: str


@dataclass
class Settings:
    brain: BrainSettings
    ai: AISettings
    openai: OpenAISettings
    google: GoogleSettings
    github: GitHubSettings
    notion: NotionSettings
    worker: WorkerSettings
    storage: StorageSettings


def load_settings() -> Settings:
    ConfigLoader().load()

    return Settings(
        brain=BrainSettings(
            name=os.getenv("BRAIN_NAME", "AIControlCenter"),
            role=os.getenv("BRAIN_ROLE", "brain"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            timezone=os.getenv("TIMEZONE", "Asia/Seoul"),
        ),
        ai=AISettings(
            provider=os.getenv("AI_PROVIDER", "openai"),
        ),
        openai=OpenAISettings(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("OPENAI_MODEL", "gpt-5"),
            embedding_model=os.getenv(
                "OPENAI_EMBEDDING_MODEL",
                "text-embedding-3-small",
            ),
        ),
        google=GoogleSettings(
            api_key=os.getenv("GOOGLE_API_KEY"),
            model=os.getenv("GOOGLE_MODEL", "gemini-2.5-pro"),
        ),
        github=GitHubSettings(
            username=os.getenv("GITHUB_USERNAME"),
            token=os.getenv("GITHUB_TOKEN"),
        ),
        notion=NotionSettings(
            api_key=os.getenv("NOTION_API_KEY"),
            database=os.getenv("NOTION_DATABASE"),
        ),
        worker=WorkerSettings(
            ubuntu_host=os.getenv("WORKER_UBUNTU_HOST"),
            ubuntu_port=int(os.getenv("WORKER_UBUNTU_PORT", "22")),
            ubuntu_user=os.getenv("WORKER_UBUNTU_USER"),
            ubuntu_ssh_key=os.getenv("WORKER_UBUNTU_SSH_KEY"),
        ),
        storage=StorageSettings(
            root=os.getenv("STORAGE_ROOT", "/mnt/storage"),
            backup_root=os.getenv("BACKUP_ROOT", "/mnt/storage/Backup"),
            ai_root=os.getenv("AI_STORAGE_ROOT", "/mnt/storage/AI"),
        ),
    )

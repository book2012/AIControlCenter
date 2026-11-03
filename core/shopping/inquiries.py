"""Legacy host contact configuration and repository constructor bridges."""
import os
from aicc_plugin_shopping import inquiries as _implementation

CONTACT_CHANNELS = ({"type": "kakao_openchat", "label": "카카오 오픈채팅",
                     "url": "https://open.kakao.com/o/sV26tFNi", "enabled": True},)


def configured_contact_channels() -> list[dict]:
    channels = [dict(channel) for channel in CONTACT_CHANNELS if channel["enabled"]]
    instagram_url = os.getenv("AICC_INSTAGRAM_CONTACT_URL", "").strip()
    if instagram_url.startswith("https://www.instagram.com/"):
        channels.append({"type": "instagram", "label": "인스타그램", "url": instagram_url, "enabled": True})
    return channels


class InMemoryInquiryRepository(_implementation.InMemoryInquiryRepository):
    def __init__(self, *, channel_provider=None):
        super().__init__(channel_provider=channel_provider or (lambda: configured_contact_channels()))


class SQLiteInquiryRepository(_implementation.SQLiteInquiryRepository, InMemoryInquiryRepository):
    def __init__(self, db_path: str, *, channel_provider=None):
        super().__init__(db_path, channel_provider=channel_provider or (lambda: configured_contact_channels()))

    @classmethod
    def open_existing(cls, db_path: str, *, channel_provider=None):
        return super().open_existing(db_path, channel_provider=channel_provider or (lambda: configured_contact_channels()))


def __getattr__(name):
    return getattr(_implementation, name)

__all__ = tuple(name for name in vars(_implementation) if not name.startswith("_"))

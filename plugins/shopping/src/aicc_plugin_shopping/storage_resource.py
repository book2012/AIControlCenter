"""Explicit existing-store lifecycle; no default path or migration authority."""
from pathlib import Path
from .customer_persistence import StorageUnavailable
from .customer_session_service import CustomerSessionService
from .inquiries import SQLiteInquiryRepository


class ShoppingStorageResource:
    def __init__(self, database_path, *, data_root, channel_provider=None):
        self._database_path = Path(database_path)
        self._data_root = Path(data_root)
        self._channels = channel_provider
        self.sessions = None
        self.inquiries = None

    @property
    def ready(self):
        return self.sessions is not None and self.inquiries is not None

    def start(self):
        if self.ready:
            return
        root, path = self._data_root, self._database_path
        if not root.is_absolute() or not path.is_absolute() or not root.is_dir() or root.is_symlink():
            raise StorageUnavailable("storage boundary invalid")
        if not path.resolve().is_relative_to(root.resolve()) or not path.is_file() or path.is_symlink():
            raise StorageUnavailable("storage boundary invalid")
        for parent in path.parents:
            if parent == root:
                break
            if parent.is_symlink():
                raise StorageUnavailable("storage boundary invalid")
        repository = SQLiteInquiryRepository.open_existing(str(path), channel_provider=self._channels)
        self.sessions = CustomerSessionService(str(path.resolve()))
        self.inquiries = repository

    def close(self):
        # Repositories use short-lived connections. The owner drains all leases
        # before dropping bindings. No purge, credential revocation or DB deletion.
        self.sessions = None
        self.inquiries = None

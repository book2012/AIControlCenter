"""Optional Mac evidence collector limited to read-only standard-library probes."""

from __future__ import annotations

import os
import platform
from pathlib import Path


class MacOperationalBootstrapEvidenceCollector:
    def collect_path(self, path: Path) -> dict[str, object]:
        candidate = Path(path)
        parent_symlink = False
        current = candidate.parent
        parent_filesystem_identity = ""
        while current != current.parent:
            try:
                parent_stat = current.lstat()
                parent_filesystem_identity = str(parent_stat.st_dev)
                if current.is_symlink():
                    parent_symlink = True
                    break
            except FileNotFoundError:
                pass
            current = current.parent
        try:
            stat = candidate.lstat()
            exists, symlink, filesystem_identity = True, candidate.is_symlink(), str(stat.st_dev)
        except FileNotFoundError:
            exists, symlink = False, False
            filesystem_identity = parent_filesystem_identity
        return {"normalized_identity": str(candidate.absolute()), "exists": exists,
                "symlink": symlink, "parent_component_symlink": parent_symlink,
                "filesystem_identity": filesystem_identity}

    @staticmethod
    def collect_host() -> dict[str, object]:
        return {"operating_system": platform.system(),
                "machine_architecture": platform.machine(), "user_id": os.getuid()}

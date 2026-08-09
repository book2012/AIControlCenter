from __future__ import annotations

import os
from pathlib import Path


DATA_ROOT_ENV = "AICONTROLCENTER_DATA_ROOT"


def data_root() -> Path:
    raw = os.environ.get(DATA_ROOT_ENV)

    if raw is None or not raw.strip():
        return Path("data")

    root = Path(raw).expanduser()

    if not root.is_absolute():
        raise ValueError(
            "aicontrolcenter_data_root_must_be_absolute"
        )

    return root.resolve(strict=False)


def resolve_data_path(name: str) -> Path:
    relative = Path(name)

    if (
        relative.is_absolute()
        or ".." in relative.parts
        or relative == Path(".")
    ):
        raise ValueError(
            "aicontrolcenter_data_path_must_be_relative"
        )

    return data_root() / relative

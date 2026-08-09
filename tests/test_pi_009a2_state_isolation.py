from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest

from core.memory.sqlite_store import SQLiteConversationStore
from core.runtime.data_paths import data_root, resolve_data_path


ROOT = Path(__file__).parents[1]


def test_data_root_default_preserves_development_contract(
    monkeypatch,
):
    monkeypatch.delenv(
        "AICONTROLCENTER_DATA_ROOT",
        raising=False,
    )

    assert data_root() == Path("data")

    assert resolve_data_path(
        "conversations.db"
    ) == Path(
        "data/conversations.db"
    )


def test_explicit_data_root_requires_absolute_path(
    monkeypatch,
):
    monkeypatch.setenv(
        "AICONTROLCENTER_DATA_ROOT",
        "relative/state",
    )

    with pytest.raises(
        ValueError,
        match="aicontrolcenter_data_root_must_be_absolute",
    ):
        data_root()


def test_conversation_store_uses_external_data_root(
    tmp_path,
    monkeypatch,
):
    state = (
        tmp_path / "state"
    ).resolve()

    monkeypatch.setenv(
        "AICONTROLCENTER_DATA_ROOT",
        str(state),
    )

    store = SQLiteConversationStore()

    assert store.db_path == (
        state / "conversations.db"
    )

    assert store.db_path.is_file()


def test_scheduler_source_uses_canonical_data_root():
    source = (
        ROOT
        / "core"
        / "scheduler"
        / "heartbeat.py"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "resolve_data_path"
        in source
    )

    assert (
        'resolve_data_path(\n'
        '                "scheduler.db"'
        in source
    )

    assert (
        '"data/scheduler.db"'
        not in source
    )


def test_shadow_import_uses_external_state_root(
    tmp_path,
):
    state = (
        tmp_path / "state"
    ).resolve()

    environment = dict(
        os.environ
    )

    environment[
        "AICONTROLCENTER_DATA_ROOT"
    ] = str(state)

    environment[
        "PYTHONPATH"
    ] = str(ROOT)

    environment[
        "PYTHONNOUSERSITE"
    ] = "1"

    environment[
        "PYTHONDONTWRITEBYTECODE"
    ] = "1"

    completed = subprocess.run(
        [
            sys.executable,
            "-P",
            "-c",
            (
                "import core.api.shadow as shadow;"
                "print(shadow.__file__)"
            ),
        ],
        cwd=str(ROOT),
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, (
        completed.stdout
        + completed.stderr
    )

    loaded = Path(
        completed.stdout.strip()
    ).resolve()

    loaded.relative_to(
        ROOT.resolve()
    )

    assert (
        state
        / "conversations.db"
    ).is_file()

from dataclasses import FrozenInstanceError, fields
from pathlib import Path
import os
import sqlite3

import pytest

from core.governance.control_plane.trust.pre_bootstrap_remediation_journal import (
    AuthorizationReplayKey, DurableAttemptState, DurableJournalError,
    FUTURE_PRODUCTION_JOURNAL_PATH, JOURNAL_PURPOSE_VERSION, ReplayDenied,
    SQLitePreBootstrapRemediationAttemptJournal,
)


def key(seed: bytes = b"ephemeral-test-capability") -> AuthorizationReplayKey:
    return AuthorizationReplayKey.derive_from_ephemeral_capability(seed)


def store(tmp_path: Path, **kwargs) -> SQLitePreBootstrapRemediationAttemptJournal:
    return SQLitePreBootstrapRemediationAttemptJournal(
        tmp_path / "isolated" / "attempt.sqlite3", **kwargs
    )


def test_first_identity_claims_once_and_duplicate_is_denied(tmp_path):
    journal = store(tmp_path)
    assert journal.claim_once(key()).state is DurableAttemptState.DURABLY_CLAIMED
    with pytest.raises(ReplayDenied):
        journal.claim_once(key())


@pytest.mark.parametrize("state", list(DurableAttemptState))
def test_claim_and_every_terminal_state_survive_reopen(tmp_path, state):
    journal = store(tmp_path)
    journal.claim_once(key())
    if state is not DurableAttemptState.DURABLY_CLAIMED:
        journal.record_terminal(key(), state)
    reopened = store(tmp_path)
    assert reopened.read(key()).state is state
    with pytest.raises(ReplayDenied):
        reopened.claim_once(key())


def test_no_lease_ttl_claim_steal_reset_delete_or_generic_api(tmp_path):
    journal = store(tmp_path)
    journal.claim_once(key())
    for name in ("steal", "renew", "retry", "reset", "delete", "execute", "query"):
        assert not hasattr(journal, name)
    assert [name for name in type(journal).__dict__ if not name.startswith("_")] == [
        "read", "claim_once", "record_terminal"
    ]


def test_key_contract_rejects_raw_text_bool_and_empty_or_mutable_models(tmp_path):
    with pytest.raises(TypeError):
        AuthorizationReplayKey("a" * 64)
    for value in (b"", True, 1, "external-form"):
        with pytest.raises(ValueError):
            AuthorizationReplayKey.derive_from_ephemeral_capability(value)
    replay_key = key()
    assert len(replay_key.value) == 64
    with pytest.raises(FrozenInstanceError):
        replay_key.value = "0" * 64
    with pytest.raises(ValueError):
        store(tmp_path).claim_once(True)


def test_journal_models_cannot_represent_raw_external_form_or_authority_fields():
    forbidden = {
        "authorization_ref", "authorization_external_form", "raw_bytes", "credential",
        "password", "username", "token", "command", "argv", "environment", "path",
        "mode", "uid", "gid",
    }
    assert forbidden.isdisjoint(field.name for field in fields(AuthorizationReplayKey))


def test_production_path_is_frozen_but_constructor_refuses_it():
    assert str(FUTURE_PRODUCTION_JOURNAL_PATH).startswith(
        "/Library/Application Support/AIControlCenter/Security/PreBootstrapRemediation/"
    )
    with pytest.raises(ValueError):
        SQLitePreBootstrapRemediationAttemptJournal(FUTURE_PRODUCTION_JOURNAL_PATH)


def test_exact_test_directory_and_file_modes_are_required(tmp_path):
    journal = store(tmp_path)
    assert journal._path.parent.stat().st_mode & 0o777 == 0o700
    assert journal._path.stat().st_mode & 0o777 == 0o600


def test_wrong_schema_fails_closed(tmp_path):
    path = tmp_path / "wrong.sqlite3"
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE wrong(value TEXT)")
    connection.execute("PRAGMA user_version=99")
    connection.close()
    with pytest.raises(DurableJournalError, match="schema mismatch"):
        SQLitePreBootstrapRemediationAttemptJournal(path)


def test_corrupt_row_and_wrong_purpose_fail_closed(tmp_path):
    journal = store(tmp_path)
    journal.claim_once(key())
    connection = sqlite3.connect(journal._path)
    connection.execute("PRAGMA ignore_check_constraints=ON")
    connection.execute(
        "UPDATE remediation_attempts SET purpose_version=?", ("WRONG",)
    )
    connection.commit()
    connection.close()
    with pytest.raises(DurableJournalError, match="corrupt"):
        journal.read(key())
    assert JOURNAL_PURPOSE_VERSION.endswith("/V1")


def test_same_call_ambiguous_claim_commit_may_only_verify(tmp_path):
    def fault(stage, _connection):
        if stage == "after_claim_commit":
            raise sqlite3.OperationalError("ack lost")
    journal = store(tmp_path, fault=fault)
    assert journal.claim_once(key()).state is DurableAttemptState.DURABLY_CLAIMED


def test_same_call_ambiguous_terminal_commit_may_only_verify(tmp_path):
    triggered = False
    def fault(stage, _connection):
        nonlocal triggered
        if stage == "after_terminal_commit" and not triggered:
            triggered = True
            raise sqlite3.OperationalError("ack lost")
    journal = store(tmp_path, fault=fault)
    journal.claim_once(key())
    assert journal.record_terminal(key(), DurableAttemptState.TERMINAL_SUCCESS).state \
        is DurableAttemptState.TERMINAL_SUCCESS


def test_no_upsert_replace_or_delete_in_executable_source():
    source = Path(__file__).parents[4] / "core/governance/control_plane/trust/pre_bootstrap_remediation_journal.py"
    text = source.read_text()
    assert "UPSERT" not in text
    assert "INSERT OR REPLACE" not in text
    assert "DELETE FROM" not in text

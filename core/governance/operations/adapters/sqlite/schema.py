"""Append-only SQLite schema and read queries."""

TABLE_NAME = 'governance_audit_operation_events'
ADAPTER_SCHEMA_VERSION = 1

UPDATE_TRIGGER_NAME = 'governance_audit_operation_events_deny_update'
DELETE_TRIGGER_NAME = 'governance_audit_operation_events_deny_delete'
RUN_INDEX_NAME = 'idx_governance_audit_operation_events_run_sequence'
OPERATION_INDEX_NAME = 'idx_governance_audit_operation_events_operation_occurred'
TYPE_INDEX_NAME = 'idx_governance_audit_operation_events_type_occurred'

REQUIRED_OBJECTS = frozenset(
    {
        TABLE_NAME,
        UPDATE_TRIGGER_NAME,
        DELETE_TRIGGER_NAME,
        RUN_INDEX_NAME,
        OPERATION_INDEX_NAME,
        TYPE_INDEX_NAME,
    }
)

SCHEMA_SQL = "CREATE TABLE IF NOT EXISTS governance_audit_operation_events (\n    sequence_no INTEGER PRIMARY KEY AUTOINCREMENT,\n    event_id TEXT NOT NULL UNIQUE,\n    run_id TEXT NOT NULL,\n    operation TEXT NOT NULL CHECK (\n        operation IN (\n            'governance_audit_snapshot',\n            'sqlite_online_backup_verification'\n        )\n    ),\n    event_type TEXT NOT NULL CHECK (\n        event_type IN (\n            'run_scheduled',\n            'run_started',\n            'run_succeeded',\n            'run_failed',\n            'run_missed'\n        )\n    ),\n    scheduled_for TEXT NOT NULL,\n    occurred_at TEXT NOT NULL,\n    recorded_at TEXT NOT NULL,\n    attempt INTEGER NOT NULL CHECK (attempt >= 1),\n    producer TEXT NOT NULL CHECK (\n        producer = 'AIControlCenter'\n    ),\n    schema_version TEXT NOT NULL CHECK (\n        schema_version = '1.0.0'\n    ),\n    duration_ms INTEGER CHECK (\n        duration_ms IS NULL OR duration_ms >= 0\n    ),\n    scheduling_latency_ms INTEGER CHECK (\n        scheduling_latency_ms IS NULL\n        OR scheduling_latency_ms >= 0\n    ),\n    error_json TEXT,\n    evidence_json TEXT NOT NULL DEFAULT '{}',\n    payload_sha256 TEXT NOT NULL\n);\n\nCREATE INDEX IF NOT EXISTS idx_governance_audit_operation_events_run_sequence\nON governance_audit_operation_events (\n    run_id,\n    sequence_no\n);\n\nCREATE INDEX IF NOT EXISTS idx_governance_audit_operation_events_operation_occurred\nON governance_audit_operation_events (\n    operation,\n    occurred_at DESC,\n    sequence_no DESC\n);\n\nCREATE INDEX IF NOT EXISTS idx_governance_audit_operation_events_type_occurred\nON governance_audit_operation_events (\n    event_type,\n    occurred_at DESC,\n    sequence_no DESC\n);\n\nCREATE TRIGGER IF NOT EXISTS governance_audit_operation_events_deny_update\nBEFORE UPDATE ON governance_audit_operation_events\nBEGIN\n    SELECT RAISE(\n        ABORT,\n        'append-only violation: operation event update denied'\n    );\nEND;\n\nCREATE TRIGGER IF NOT EXISTS governance_audit_operation_events_deny_delete\nBEFORE DELETE ON governance_audit_operation_events\nBEGIN\n    SELECT RAISE(\n        ABORT,\n        'append-only violation: operation event delete denied'\n    );\nEND;"

SELECT_COLUMNS = """
    sequence_no,
    event_id,
    run_id,
    operation,
    event_type,
    scheduled_for,
    occurred_at,
    recorded_at,
    attempt,
    producer,
    schema_version,
    duration_ms,
    scheduling_latency_ms,
    error_json,
    evidence_json,
    payload_sha256
""".strip()

INSERT_SQL = f"""
INSERT INTO {TABLE_NAME} (
    event_id,
    run_id,
    operation,
    event_type,
    scheduled_for,
    occurred_at,
    recorded_at,
    attempt,
    producer,
    schema_version,
    duration_ms,
    scheduling_latency_ms,
    error_json,
    evidence_json,
    payload_sha256
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""".strip()

EVENTS_FOR_RUN_SQL = f"""
SELECT {SELECT_COLUMNS}
FROM {TABLE_NAME}
WHERE run_id = ?
ORDER BY sequence_no ASC
""".strip()

ITER_EVENTS_SQL = f"""
SELECT {SELECT_COLUMNS}
FROM {TABLE_NAME}
ORDER BY sequence_no ASC
""".strip()

ITER_OPERATION_EVENTS_SQL = f"""
SELECT {SELECT_COLUMNS}
FROM {TABLE_NAME}
WHERE operation = ?
ORDER BY sequence_no ASC
""".strip()

LAST_SUCCESS_SQL = f"""
SELECT {SELECT_COLUMNS}
FROM {TABLE_NAME}
WHERE operation = ?
  AND event_type = 'run_succeeded'
ORDER BY occurred_at DESC, sequence_no DESC
LIMIT 1
""".strip()

LAST_FAILURE_SQL = f"""
SELECT {SELECT_COLUMNS}
FROM {TABLE_NAME}
WHERE operation = ?
  AND event_type = 'run_failed'
ORDER BY occurred_at DESC, sequence_no DESC
LIMIT 1
""".strip()

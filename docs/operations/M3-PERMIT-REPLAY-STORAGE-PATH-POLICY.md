# M3 Permit and Replay Storage Path Policy

The future path is defined, not provisioned:

`~/Library/Application Support/AIControlCenter/security/permit-replay.sqlite3`

Composition must inject the complete path explicitly. Runtime must never infer
it, select it by default, create it or create its parent directory.

An acceptable path is absolute, below the Mac operator's
`Library/Application Support` tree, outside the Git repository, and free of
symlink components. Relative and traversal paths, protected system paths,
Linux or Ubuntu ownership paths, network or removable volumes, repository
paths, and secret-bearing filenames are blocked.

The M3-A2A inspector opens an accepted existing regular file only with SQLite
URI `mode=ro`, enables `query_only`, uses a bounded timeout and closes the
connection deterministically. It performs zero writes, reservations,
consumptions, migrations, repairs or journal changes.

Operational permit/replay database: `NOT CREATED`.
Production activation: `NOT_AUTHORIZED`.

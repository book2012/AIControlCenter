# M3 Audit Storage Path Policy

The canonical future policy location is:

`~/Library/Application Support/AIControlCenter/audit/audit-ledger.sqlite3`

This is a policy representation, not an instruction to create the directory or
file. Operators must inject an absolute configured path. The inspector has no
operational default.

Only the current Mac user's `Library/Application Support` tree is eligible.
Repository-relative or repository-contained paths, traversal, symlink files,
symlink parent components, protected system paths, Linux/Ubuntu ownership
paths, `/Volumes` network or removable storage, and secret-bearing database
names are blocked. The path policy reports reason codes without exposing
database contents.

Creation and ownership of the operational database are deferred to a separately
authorized increment. Production activation remains `NOT_AUTHORIZED`.

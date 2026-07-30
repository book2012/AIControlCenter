# M3-A4B Bootstrap Failure Cleanup

Before mutation the executor proves that its application-state and
restore-validation subtrees do not exist. It tracks artifacts created by the
current test execution.

On failure it rolls back and closes SQLite connections, removes only those
proven-new owned subtrees (including SQLite sidecars), returns no success
evidence and leaves the synthetic permit claimed. A retry requires a separate
synthetic permit.

Pre-existing artifacts fail before mutation and are never removed, overwritten,
truncated, migrated, repaired or reused. A cleanup problem remains failed
closed; it never authorizes writer, monitoring, dispatch or Production
activation. No operational cleanup occurred because operational bootstrap was
not executed.

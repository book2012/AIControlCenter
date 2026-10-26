# Checkout SQLite connection lifecycle

AIControlCenter remains the Mac Control Plane. No authority, schema, API or order-state transition changes are introduced.

Checkout persistence and operator polling own each SQLite connection for one operation. Enter `closing(connection)` outside the existing transaction context; transaction exit commits or rolls back before closing on both success and exception. Read-only URI connections remain read-only. Connection lifetime must not depend on cyclic garbage collection.

This addresses the observed DEV descriptor exhaustion: 242 checkout handles and Errno 24 while the process still existed. Health must be checked with an HTTP request, not PID presence alone. Recovery and a later source fix are distinct evidence.

Regression retains every connection reference to prevent GC from masking a leak, exercises repeated lookup/polling and injected read/write errors, and verifies rollback. No production deployment is included. See [status and evidence](../operations/STATUS_AUDIT_20261027.md).

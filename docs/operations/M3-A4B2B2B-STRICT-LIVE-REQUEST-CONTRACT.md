# M3-A4B2B2B Strict Live Request Contract

The canonical request binds an ID, exact branch and commit, trusted operational
root, requester/operator/independent-approver identities,
controlled-non-production scope, maximum uses one, monotonic time policy,
active restrictions, dual acknowledgements, and all eleven artifact paths.

Paths must be absolute, traversal-free, and distinct. Production, writers,
monitoring, and external-dispatch flags must be false. Unknown fields, secrets,
raw nonce/environment data, commands, shell, argv, scripts, URLs,
destinations, Ubuntu/worker scope, and caller-selected production roots are
rejected.

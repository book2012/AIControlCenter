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

The strict shared-parent preflight artifact is the sole exception: it must
contain the exact field `ubuntu_participation` with Boolean value `false`.
This is deny-evidence, not an Ubuntu instruction. True, missing, null,
string/integer/container values, alternate or nested Ubuntu fields, and
unknown environment, command, host, worker, destination, or production fields
are rejected. The global unsafe-field policy remains unchanged.

The live permit is an immutable typed result, never an arbitrary mapping. Its
canonical digest binds one use, controlled-non-production scope, branch,
commit, identities, validity window, bootstrap deadline, inactive
capabilities, and `production_authorized=false`.

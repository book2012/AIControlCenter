# M3-A4B2B2B Live Issuance and Runner Gate

Live issuance and controlled runtime are default deny. An environment variable,
boolean, CLI enable option, caller-selected mode, arbitrary adapter or monkey
patch is not authorization.

The issuance coordinator accepts non-synthetic approval only with a valid
non-synthetic activation authorization matching approval, identities, branch,
commit, target, restrictions, scope, window and zero safety state. It does not
persist or claim the resulting permit.

The runtime coordinator requires the activation digest, exact operational
bindings, live permit and issuance evidence, controlled mode and the
`MacOperationalBootstrapRuntimeAdapter`. Test mode accepts only the test
adapter and injected test roots. Linux, Ubuntu, root, arbitrary roots,
production scope and any active writer, monitoring or dispatch permission are
rejected.

R2 validation did not invoke the actual operational adapter.

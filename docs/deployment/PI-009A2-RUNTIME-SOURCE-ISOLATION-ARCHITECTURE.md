# PI-009A2 Runtime Source Isolation Architecture

Status: FROZEN FOR IMPLEMENTATION

Production authorized: NO

## Problem

The active AIControlCenter Runtime currently identifies an immutable Python
virtual environment but does not contain the AIControlCenter application
source.

The active Runtime is:

`runtime/venvs/acd80ab9f6ae`

Its full source commit marker is:

`acd80ab9f6aeb848900e1a19e3fa3afd69face8a`

A neutral invocation of the Candidate Runtime Python with `PYTHONPATH`
removed cannot resolve:

`core.api.shadow`

The production wrapper currently changes directory to the mutable Git working
tree and adds the repository root to `PYTHONPATH`.

Therefore the service Runtime identity does not independently identify the
application source it executes.

Production authorization remains blocked.

## Architecture Decision

AIControlCenter will use a paired immutable Runtime artifact model.

Python dependency artifact:

`runtime/venvs/<runtime-id>`

Application source artifact:

`runtime/sources/<runtime-id>`

The existing `runtime/current` pointer continues to point to:

`runtime/venvs/<runtime-id>`

No pointer-layout migration is required by PI-009A2.

The wrapper derives `<runtime-id>` from the resolved current Runtime and then
requires the matching immutable source artifact.

## Source Artifact

The source artifact is built from the exact full Git commit recorded in the
Runtime source marker.

For the currently active Candidate:

Runtime ID:

`acd80ab9f6ae`

Source commit:

`acd80ab9f6aeb848900e1a19e3fa3afd69face8a`

The source artifact is created from:

`git archive <full-approved-source-commit>`

The complete tracked repository snapshot is used rather than only `core/`.
This prevents future Runtime assets such as schemas, templates or configuration
files from silently remaining dependent on the mutable repository.

The artifact must not contain `.git`.

## Source Metadata

Each immutable source artifact contains:

`.aicontrolcenter-source-commit`

and:

`.aicontrolcenter-source-manifest.json`

The commit marker contains the exact lowercase 40-character Git commit followed
by one newline.

The manifest records at minimum:

- schema version
- runtime ID
- full source commit
- Git tree identity
- archive SHA-256
- artifact root identity
- build status

The Runtime venv source marker and source artifact source marker must match
exactly.

## Immutability

Source artifact construction uses a staging directory.

The final destination must not already exist.

The builder must fail closed on:

- an invalid Runtime ID
- an invalid full source commit
- missing Git commit
- source marker mismatch
- repository overlap
- destination symlink
- existing destination
- archive/extraction failure
- manifest validation failure

Final publication uses a same-parent atomic rename.

After publication:

- source files are read-only
- source directories are non-writable
- Python bytecode writes remain disabled

The production service must not mutate application source.

## Wrapper Contract

The production wrapper resolves:

`runtime/current`

to an approved direct child of:

`runtime/venvs`

It derives the Runtime ID from that resolved directory.

It then resolves:

`runtime/sources/<runtime-id>`

The wrapper fails closed unless all of the following hold:

1. current Runtime is a valid direct child of `runtime/venvs`
2. Runtime Python exists and is executable
3. Runtime source marker is valid
4. matching source directory exists
5. source directory is not a symlink
6. source directory resolves as a direct child of `runtime/sources`
7. source marker is valid
8. Runtime and source full commits match exactly
9. source manifest matches Runtime ID and full commit
10. `core/api/shadow.py` exists inside the source artifact

The wrapper then executes from the immutable source root.

Required execution model:

`cd <immutable-source-root>`

`PYTHONPATH=<immutable-source-root>`

`<runtime-python> -m uvicorn core.api.shadow:app ...`

The mutable Git repository must not be part of the production application
import path.

## Repository Separation

The Git working tree remains the Control Plane governance and development
repository.

Git HEAD and production Runtime source identity are separate concepts.

A documentation or governance commit must not silently change the source
executed by an already approved Runtime.

## Runtime Validation

Production source isolation is not verified until a neutral source test proves
that the application resolves inside the immutable Runtime source artifact.

Required evidence includes:

- Runtime ID
- Runtime full source commit
- source artifact full source commit
- manifest validation
- exact imported `core.api.shadow.__file__`
- imported path is below `runtime/sources/<runtime-id>`
- imported path is not below the mutable repository
- GET `/health` = 200
- GET `/runtime/health` = 200
- POST `/health` = 405
- launchd PID equals listener PID

## Rollback

PI-009A2 does not change the current Runtime pointer.

Wrapper cutover rollback is therefore independent of Runtime pointer rollback.

Rollback requires separate explicit human authorization and consists only of:

- restore the previously approved wrapper artifact
- perform one authorized service kickstart
- revalidate listener and HTTP health

Automatic rollback is not authorized.

## Safety Boundaries

PI-009A2 does not authorize:

- Production
- public exposure
- Caddy mutation
- Ubuntu mutation
- Runtime current pointer mutation
- application-state mutation
- automatic rollback

## Production Gate

Production remains:

`NOT_AUTHORIZED`

until:

`RUNTIME_SOURCE_ISOLATION_VERIFIED`

is satisfied and PI-009 Technical Production Authorization Review is rerun.

## Application State Isolation Amendment

During A2.1 immutable-source validation, the approved Candidate source was found
to initialize writable SQLite application state through repository-relative
paths:

- `data/conversations.db`
- `data/scheduler.db`

An immutable production source artifact must never become writable to preserve
such state.

The production Runtime architecture therefore separates:

- immutable source: `runtime/sources/<runtime-id>`
- writable application state:
  `~/Library/Application Support/AIControlCenter/data`

`AICONTROLCENTER_DATA_ROOT` is the canonical application-state root contract.

Memory and scheduler database defaults must resolve through this contract.

When the environment variable is explicitly configured it must be an absolute
path. Development fallback to repository-relative `data/` remains available
only when the variable is absent.

The existing Candidate source
`acd80ab9f6aeb848900e1a19e3fa3afd69face8a`
does not satisfy this state-isolation requirement and therefore cannot be the
final immutable-source Production release.

A new source commit and new Runtime Candidate are required.

Production remains unauthorized.

## A2.1 Immutable Source Artifact Tooling

Status: COMPLETE

The canonical bootstrap build contract was verified to be HEAD-only.

Accordingly, the completed A2.1 repository commit becomes the source identity
for the next Runtime Candidate. Historical source commits are not injected into
the bootstrap build path.

The repository now provides:

- JSON-first immutable source artifact builder
- immutable source artifact validator
- source commit and Git tree identity
- Git archive SHA-256
- independent source-content SHA-256
- same-parent staging and atomic publication
- explicit capability requirement for operational source writes
- immutable-source launchd wrapper template
- Python `-P` path isolation
- mutable repository removal from application cwd and PYTHONPATH
- required external application-state contract

The source validator requires the state-isolation module,
`core/runtime/data_paths.py`, in addition to the application entrypoint and
tracked worker configuration.

Production state remains external through `AICONTROLCENTER_DATA_ROOT`.

No operational Runtime, source artifact, live wrapper, service, or Runtime
pointer was modified during A2.1.

The next Runtime Candidate must be built from the clean A2.1 completion HEAD.

Production remains unauthorized.

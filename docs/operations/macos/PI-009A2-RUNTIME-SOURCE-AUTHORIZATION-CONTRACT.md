# PI-009A2 Runtime Source Authorization Contract

Status: FROZEN

Production authorized: NO

PI-009A2 uses separate human authorization boundaries.

## A2.1 Repository Implementation

Repository-local source builder, validator, wrapper template and tests may be
implemented and committed without production Runtime mutation.

This phase does not authorize any file write under the operational Runtime
root or `/usr/local/libexec`.

## A2.2 Source Artifact Creation

Source artifact creation requires explicit authorization after the exact
artifact identity and builder implementation have passed repository tests.

The future authorization must identify:

- Runtime ID
- full source commit
- exact destination
- builder Git commit
- expected existing-destination state

The authorization permits one source-artifact creation only.

It does not authorize:

- current pointer changes
- wrapper changes
- service restart or kickstart
- rollback
- Caddy
- Ubuntu
- Production

## A2.3 Wrapper Cutover

Wrapper cutover requires a separate explicit authorization after the immutable
source artifact passes read-only validation.

The future authorization must identify:

- Runtime ID
- full source commit
- source artifact validation digest
- new wrapper SHA-256
- previous wrapper SHA-256
- exact wrapper destination
- one launchd kickstart

The authorization permits only the named wrapper installation and one service
kickstart.

It does not authorize:

- Runtime current pointer changes
- automatic rollback
- Caddy
- Ubuntu
- public exposure
- Production

## Rollback Authorization

Rollback is a separate human gate.

No PI-009A2 authorization implicitly authorizes rollback.

## Completion Evidence

PI-009A2 is complete only when:

- immutable source artifact validates
- wrapper no longer imports application source from the Git working tree
- loaded `core.api.shadow.__file__` is inside the approved source artifact
- Runtime/source full commits match
- launchd and listener identity match
- exact HTTP checks pass
- Git is clean and synchronized
- documentation is updated
- Production remains explicitly gated pending PI-009 final review

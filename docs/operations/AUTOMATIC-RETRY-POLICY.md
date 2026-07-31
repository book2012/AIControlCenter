# Automatic Retry Policy

AIControlCenter owns retry and recovery decisions. Codex may report evidence but
cannot classify or authorize a post-claim retry.

- `SAFE_PREFLIGHT_RETRY`: no edit, authorization, permit, claim or operational
  write exists.
- `SAFE_PRE_CLAIM_RECOVERY`: explicit complete evidence is required and no
  claim exists.
- `MANUAL_POST_CLAIM_RECOVERY`: a real claim exists; automatic retry is
  prohibited and human approval is mandatory.
- `NO_RETRY`: production or safety violation, uncertain side effects,
  operational write, or incomplete evidence.

The classifier is deterministic and default-deny. Environment variables cannot
authorize retry, recovery or activation. AUTO-01 performs no retry.
